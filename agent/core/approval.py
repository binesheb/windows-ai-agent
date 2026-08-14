from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from secrets import token_urlsafe
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    capability: str
    reason: str
    created_at: str
    status: str = "pending"
    caller: str = "local_token"
    action: dict[str, Any] | None = None
    decided_at: str | None = None
    decided_by: str | None = None


class ApprovalManager:
    """Thread-safe in-memory approval queue.

    This component records decisions only. It deliberately does not execute
    the requested operation. Execution belongs to a later, capability-specific
    layer after approval and policy checks.
    """

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}
        self._lock = Lock()

    def create(
        self,
        capability: str,
        reason: str,
        *,
        caller: str = "local_token",
        action: dict[str, Any] | None = None,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            request_id=f"apr_{token_urlsafe(18)}",
            capability=capability,
            reason=reason,
            created_at=datetime.now(timezone.utc).isoformat(),
            caller=caller,
            action=action or {},
        )
        with self._lock:
            self._requests[request.request_id] = request
        return request

    def get(self, request_id: str) -> ApprovalRequest | None:
        with self._lock:
            return self._requests.get(request_id)

    def list_pending(self) -> list[ApprovalRequest]:
        with self._lock:
            return [item for item in self._requests.values() if item.status == "pending"]

    def decide(self, request_id: str, decision: str, decided_by: str = "local_user") -> ApprovalRequest | None:
        if decision not in {"approved", "denied"}:
            raise ValueError("Decision must be 'approved' or 'denied'")

        with self._lock:
            current = self._requests.get(request_id)
            if current is None:
                return None
            if current.status != "pending":
                raise ValueError("Approval request has already been decided")

            updated = replace(
                current,
                status=decision,
                decided_at=datetime.now(timezone.utc).isoformat(),
                decided_by=decided_by,
            )
            self._requests[request_id] = updated
            return updated
