from __future__ import annotations

import psutil
from fastapi import FastAPI, HTTPException, Query

from agent.audit.logger import AuditLogger
from agent.core.approval import ApprovalManager
from agent.core.capabilities import all_capabilities
from agent.core.policy import PolicyEngine
from agent.system.inventory import get_system_inventory
from agent.system.services import get_service_inventory


app = FastAPI(
    title="Windows AI Agent",
    version="0.2.1",
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
        "version": "0.2.1",
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
