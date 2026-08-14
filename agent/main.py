from __future__ import annotations

from pathlib import Path

import psutil
from fastapi import FastAPI, HTTPException, Query

from agent.audit.logger import AuditLogger
from agent.core.approval import ApprovalManager
from agent.core.capabilities import all_capabilities
from agent.core.config import filesystem_settings
from agent.core.paths import evaluate_path
from agent.core.policy import PolicyEngine
from agent.system.filesystem import list_directory, read_text_file
from agent.system.inventory import get_system_inventory
from agent.system.services import get_service_inventory


app = FastAPI(
    title="Windows AI Agent",
    version="0.3.0",
    description="Security-first local Windows AI control gateway",
)

policy = PolicyEngine()
audit_logger = AuditLogger()
approvals = ApprovalManager()


def _mb(value: int) -> float:
    return round(value / (1024**2), 2)


def get_process_inventory(limit: int = 250) -> list[dict]:
    """Return a bounded, read-only snapshot of running processes."""
    processes: list[dict] = []
    for process in psutil.process_iter(
        ["pid", "name", "username", "exe", "status", "memory_info", "cpu_percent"]
    ):
        try:
            info = process.info
            memory_info = info.get("memory_info")
            processes.append(
                {
                    "pid": info.get("pid"),
                    "name": info.get("name"),
                    "username": info.get("username"),
                    "executable": info.get("exe"),
                    "status": info.get("status"),
                    "memory_mb": _mb(memory_info.rss) if memory_info else None,
                    "cpu_percent": info.get("cpu_percent"),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    processes.sort(key=lambda item: item["pid"] or 0)
    return processes[:limit]


@app.get("/")
def root() -> dict:
    return {
        "name": "Windows AI Agent",
        "version": "0.3.0",
        "mode": "READ_ONLY",
        "status": "online",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "mode": "READ_ONLY"}


@app.get("/capabilities")
def capabilities() -> dict:
    return {"capabilities": all_capabilities()}


@app.get("/capabilities/{capability}")
def capability(capability: str) -> dict:
    decision = policy.evaluate(capability)
    audit_logger.record(
        "policy.evaluate",
        "success",
        details={
            "capability": capability,
            "allowed": decision.allowed,
            "requires_approval": decision.requires_approval,
        },
    )
    return {
        "capability": capability,
        "allowed": decision.allowed,
        "requires_approval": decision.requires_approval,
        "risk": decision.risk.value if decision.risk else None,
        "reason": decision.reason,
    }


@app.get("/approvals")
def pending_approvals() -> dict:
    return {"requests": [request.__dict__ for request in approvals.list_pending()]}


@app.get("/system")
def system() -> dict:
    decision = policy.evaluate("system_inventory")
    if not decision.allowed:
        audit_logger.record("system.inventory", "denied")
        raise HTTPException(status_code=403, detail=decision.reason)

    result = get_system_inventory()
    audit_logger.record("system.inventory", "success")
    return result


@app.get("/processes")
def processes(limit: int = Query(default=250, ge=1, le=500)) -> dict:
    decision = policy.evaluate("process_read")
    if not decision.allowed:
        audit_logger.record("process.inventory", "denied")
        raise HTTPException(status_code=403, detail=decision.reason)

    result = get_process_inventory(limit)
    audit_logger.record(
        "process.inventory",
        "success",
        details={"count": len(result), "limit": limit},
    )
    return {"count": len(result), "processes": result}


@app.get("/services")
def services(limit: int = Query(default=500, ge=1, le=1000)) -> dict:
    decision = policy.evaluate("service_read")
    if not decision.allowed:
        audit_logger.record("service.inventory", "denied")
        raise HTTPException(status_code=403, detail=decision.reason)

    try:
        result = get_service_inventory(limit)
    except RuntimeError as exc:
        audit_logger.record("service.inventory", "failed", details={"reason": str(exc)})
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    audit_logger.record(
        "service.inventory",
        "success",
        details={"count": len(result), "limit": limit},
    )
    return {"count": len(result), "services": result}


@app.get("/filesystem/check")
def filesystem_check(path: str = Query(..., min_length=1, max_length=4096)) -> dict:
    """Evaluate a path without reading its contents."""
    decision = policy.evaluate("filesystem_read")
    if not decision.allowed:
        audit_logger.record("filesystem.check", "denied", details={"path": path})
        raise HTTPException(status_code=403, detail=decision.reason)

    roots, _, _ = filesystem_settings()
    path_decision = evaluate_path(path, roots)
    audit_logger.record(
        "filesystem.check",
        "allowed" if path_decision.allowed else "denied",
        details={"path": path_decision.normalized, "reason": path_decision.reason},
    )
    return {
        "allowed": path_decision.allowed,
        "path": path_decision.normalized,
        "reason": path_decision.reason,
    }


@app.get("/filesystem/list")
def filesystem_list(
    path: str = Query(default=".", min_length=1, max_length=4096),
    limit: int = Query(default=500, ge=1, le=500),
) -> dict:
    decision = policy.evaluate("filesystem_read")
    if not decision.allowed:
        audit_logger.record("filesystem.list", "denied", details={"path": path})
        raise HTTPException(status_code=403, detail=decision.reason)

    roots, _, configured_limit = filesystem_settings()
    path_decision = evaluate_path(path, roots)
    if not path_decision.allowed:
        audit_logger.record(
            "filesystem.list",
            "denied",
            details={"path": path_decision.normalized, "reason": path_decision.reason},
        )
        raise HTTPException(status_code=403, detail=path_decision.reason)

    target = Path(path_decision.normalized)
    if not target.is_dir():
        audit_logger.record("filesystem.list", "failed", details={"path": str(target)})
        raise HTTPException(status_code=400, detail="Path is not a directory")

    result = list_directory(target, min(limit, configured_limit))
    audit_logger.record(
        "filesystem.list",
        "success",
        details={"path": str(target), "count": len(result)},
    )
    return {"path": str(target), "count": len(result), "entries": result}


@app.get("/filesystem/read")
def filesystem_read(path: str = Query(..., min_length=1, max_length=4096)) -> dict:
    decision = policy.evaluate("filesystem_read")
    if not decision.allowed:
        audit_logger.record("filesystem.read", "denied", details={"path": path})
        raise HTTPException(status_code=403, detail=decision.reason)

    roots, max_read_bytes, _ = filesystem_settings()
    path_decision = evaluate_path(path, roots)
    if not path_decision.allowed:
        audit_logger.record(
            "filesystem.read",
            "denied",
            details={"path": path_decision.normalized, "reason": path_decision.reason},
        )
        raise HTTPException(status_code=403, detail=path_decision.reason)

    target = Path(path_decision.normalized)
    try:
        result = read_text_file(target, max_read_bytes)
    except FileNotFoundError as exc:
        audit_logger.record("filesystem.read", "not_found", details={"path": str(target)})
        raise HTTPException(status_code=404, detail="File not found") from exc
    except ValueError as exc:
        audit_logger.record("filesystem.read", "rejected", details={"path": str(target), "reason": str(exc)})
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except (OSError, PermissionError) as exc:
        audit_logger.record("filesystem.read", "failed", details={"path": str(target), "reason": str(exc)})
        raise HTTPException(status_code=403, detail="File cannot be read") from exc

    audit_logger.record(
        "filesystem.read",
        "success",
        details={"path": str(target), "size_bytes": result["size_bytes"]},
    )
    return result
