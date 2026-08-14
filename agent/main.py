from __future__ import annotations

from fastapi import FastAPI, HTTPException

from agent.audit.logger import AuditLogger
from agent.core.approval import ApprovalManager
from agent.core.capabilities import all_capabilities
from agent.core.policy import PolicyEngine
from agent.system.inventory import get_system_inventory


app = FastAPI(
    title="Windows AI Agent",
    version="0.2.0",
    description="Security-first local Windows AI control gateway",
)

policy = PolicyEngine()
audit_logger = AuditLogger()
approvals = ApprovalManager()


@app.get("/")
def root() -> dict:
    return {
        "name": "Windows AI Agent",
        "version": "0.2.0",
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
    return {
        "requests": [request.__dict__ for request in approvals.list_pending()]
    }


@app.get("/system")
def system() -> dict:
    decision = policy.evaluate("system_inventory")
    if not decision.allowed:
        audit_logger.record("system.inventory", "denied")
        raise HTTPException(status_code=403, detail=decision.reason)

    result = get_system_inventory()
    audit_logger.record("system.inventory", "success")
    return result
