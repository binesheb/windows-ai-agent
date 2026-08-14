from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import psutil
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from agent.audit.context import set_caller, set_request_context
from agent.audit.logger import AuditLogger
from agent.core.approval import ApprovalManager
from agent.core.auth import get_or_create_token, token_matches, token_path
from agent.core.capabilities import all_capabilities
from agent.core.config import filesystem_settings, filesystem_workspaces, load_config
from agent.core.paths import evaluate_path
from agent.core.policy import PolicyEngine
from agent.system.filesystem import list_directory, read_text_file
from agent.system.inventory import get_system_inventory
from agent.system.services import get_service_inventory

app = FastAPI(title="Windows AI Agent", version="0.5.0", description="Security-first local Windows AI control gateway")
policy = PolicyEngine()
audit_logger = AuditLogger()
approvals = ApprovalManager()

class ApprovalCreate(BaseModel):
    capability: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)
    action: dict = Field(default_factory=dict)

class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approved|denied)$")

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
    set_request_context(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

def _authentication_required() -> bool:
    config = load_config()
    return bool(config.get("agent", {}).get("require_authentication", True))

def require_authentication(x_agent_token: str | None = Header(default=None)) -> str:
    if not _authentication_required():
        set_caller("authentication_disabled_by_policy")
        return "authentication_disabled_by_policy"
    if token_matches(x_agent_token):
        set_caller("local_token")
        audit_logger.record("authentication.success", "success")
        return "local_token"
    audit_logger.record("authentication.failed", "denied", details={"reason": "missing_or_invalid_token"})
    raise HTTPException(status_code=401, detail="Authentication required")

def _mb(value: int) -> float:
    return round(value / (1024**2), 2)

def get_process_inventory(limit: int = 250) -> list[dict]:
    processes = []
    for process in psutil.process_iter(["pid", "name", "username", "exe", "status", "memory_info", "cpu_percent"]):
        try:
            info = process.info
            memory_info = info.get("memory_info")
            processes.append({"pid": info.get("pid"), "name": info.get("name"), "username": info.get("username"), "executable": info.get("exe"), "status": info.get("status"), "memory_mb": _mb(memory_info.rss) if memory_info else None, "cpu_percent": info.get("cpu_percent")})
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    processes.sort(key=lambda item: item["pid"] or 0)
    return processes[:limit]

def _capability_snapshot() -> list[dict[str, object]]:
    snapshot = []
    for item in all_capabilities():
        decision = policy.evaluate(str(item["name"]))
        snapshot.append({**item, "enabled": decision.allowed, "requires_approval": decision.requires_approval, "policy_reason": decision.reason})
    return snapshot

@app.get("/")
def root() -> dict:
    return {"name": "Windows AI Agent", "version": "0.5.0", "mode": "READ_ONLY", "status": "online"}

@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "mode": "READ_ONLY"}

@app.get("/auth/status")
def auth_status() -> dict:
    required = _authentication_required()
    token = get_or_create_token()
    return {"required": required, "configured": bool(token), "scheme": "X-Agent-Token" if required else None, "token_path": token_path() if required else None}

@app.get("/capabilities")
def capabilities(_: str = Depends(require_authentication)) -> dict:
    return {"capabilities": all_capabilities()}

@app.get("/capabilities/{capability}")
def capability(capability: str, _: str = Depends(require_authentication)) -> dict:
    decision = policy.evaluate(capability)
    audit_logger.record("policy.evaluate", "success", details={"capability": capability, "allowed": decision.allowed, "requires_approval": decision.requires_approval})
    return {"capability": capability, "allowed": decision.allowed, "requires_approval": decision.requires_approval, "risk": decision.risk.value if decision.risk else None, "reason": decision.reason}

@app.get("/approvals")
def pending_approvals(_: str = Depends(require_authentication)) -> dict:
    return {"requests": [request.__dict__ for request in approvals.list_pending()]}

@app.post("/approvals", status_code=201)
def create_approval(payload: ApprovalCreate, caller: str = Depends(require_authentication)) -> dict:
    decision = policy.evaluate(payload.capability)
    if not decision.allowed:
        audit_logger.record("approval.create", "denied", details={"capability": payload.capability, "reason": decision.reason})
        raise HTTPException(status_code=403, detail=decision.reason)
    if not decision.requires_approval:
        raise HTTPException(status_code=400, detail="Capability does not require approval")
    request = approvals.create(payload.capability, payload.reason, caller=caller, action=payload.action)
    audit_logger.record("approval.create", "pending", details={"approval_id": request.request_id, "capability": request.capability})
    return request.__dict__

@app.get("/approvals/{request_id}")
def get_approval(request_id: str, _: str = Depends(require_authentication)) -> dict:
    request = approvals.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request.__dict__

@app.post("/approvals/{request_id}/decision")
def decide_approval(request_id: str, payload: ApprovalDecision, _: str = Depends(require_authentication)) -> dict:
    try:
        request = approvals.decide(request_id, payload.decision)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if request is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    audit_logger.record("approval.decision", request.status, details={"approval_id": request.request_id, "decided_by": request.decided_by})
    return request.__dict__

@app.get("/system")
def system(_: str = Depends(require_authentication)) -> dict:
    decision = policy.evaluate("system_inventory")
    if not decision.allowed: raise HTTPException(status_code=403, detail=decision.reason)
    result = get_system_inventory(); audit_logger.record("system.inventory", "success"); return result

@app.get("/processes")
def processes(limit: int = Query(default=250, ge=1, le=500), _: str = Depends(require_authentication)) -> dict:
    decision = policy.evaluate("process_read")
    if not decision.allowed: raise HTTPException(status_code=403, detail=decision.reason)
    result = get_process_inventory(limit); audit_logger.record("process.inventory", "success", details={"count": len(result), "limit": limit}); return {"count": len(result), "processes": result}

@app.get("/services")
def services(limit: int = Query(default=500, ge=1, le=1000), _: str = Depends(require_authentication)) -> dict:
    decision = policy.evaluate("service_read")
    if not decision.allowed: raise HTTPException(status_code=403, detail=decision.reason)
    try: result = get_service_inventory(limit)
    except RuntimeError as exc: raise HTTPException(status_code=501, detail=str(exc)) from exc
    audit_logger.record("service.inventory", "success", details={"count": len(result), "limit": limit}); return {"count": len(result), "services": result}

@app.get("/workspaces")
def workspaces(_: str = Depends(require_authentication)) -> dict:
    configured = filesystem_workspaces(); roots, _, _ = filesystem_settings(); resolved = []
    for workspace in configured:
        path_decision = evaluate_path(workspace["path"], roots)
        resolved.append({"name": workspace["name"], "path": path_decision.normalized, "access": workspace["access"], "allowed": path_decision.allowed, "reason": path_decision.reason})
    return {"count": len(resolved), "workspaces": resolved}

@app.get("/resources")
def resources(_: str = Depends(require_authentication)) -> dict:
    roots, _, _ = filesystem_settings(); workspace_items = []
    for workspace in filesystem_workspaces():
        decision = evaluate_path(workspace["path"], roots)
        workspace_items.append({"name": workspace["name"], "path": decision.normalized, "access": workspace["access"], "allowed": decision.allowed, "reason": decision.reason})
    payload = {"agent": {"name": "Windows AI Agent", "version": "0.5.0", "mode": "read_only"}, "capabilities": _capability_snapshot(), "workspaces": workspace_items}
    return payload

@app.get("/filesystem/check")
def filesystem_check(path: str = Query(..., min_length=1, max_length=4096), _: str = Depends(require_authentication)) -> dict:
    decision = policy.evaluate("filesystem_read")
    if not decision.allowed: raise HTTPException(status_code=403, detail=decision.reason)
    roots, _, _ = filesystem_settings(); path_decision = evaluate_path(path, roots)
    return {"allowed": path_decision.allowed, "path": path_decision.normalized, "reason": path_decision.reason}

@app.get("/filesystem/list")
def filesystem_list(path: str = Query(default=".", min_length=1, max_length=4096), limit: int = Query(default=500, ge=1, le=500), _: str = Depends(require_authentication)) -> dict:
    decision = policy.evaluate("filesystem_read")
    if not decision.allowed: raise HTTPException(status_code=403, detail=decision.reason)
    roots, _, configured_limit = filesystem_settings(); path_decision = evaluate_path(path, roots)
    if not path_decision.allowed: raise HTTPException(status_code=403, detail=path_decision.reason)
    target = Path(path_decision.normalized)
    if not target.is_dir(): raise HTTPException(status_code=400, detail="Path is not a directory")
    result = list_directory(target, min(limit, configured_limit)); return {"path": str(target), "count": len(result), "entries": result}

@app.get("/filesystem/read")
def filesystem_read(path: str = Query(..., min_length=1, max_length=4096), _: str = Depends(require_authentication)) -> dict:
    decision = policy.evaluate("filesystem_read")
    if not decision.allowed: raise HTTPException(status_code=403, detail=decision.reason)
    roots, max_read_bytes, _ = filesystem_settings(); path_decision = evaluate_path(path, roots)
    if not path_decision.allowed: raise HTTPException(status_code=403, detail=path_decision.reason)
    target = Path(path_decision.normalized)
    try: result = read_text_file(target, max_read_bytes)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail="File not found") from exc
    except ValueError as exc: raise HTTPException(status_code=413, detail=str(exc)) from exc
    except (OSError, PermissionError) as exc: raise HTTPException(status_code=403, detail="File cannot be read") from exc
    return result
