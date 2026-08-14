from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from secrets import token_urlsafe


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    capability: str
    reason: str
    created_at: str
    status: str = "pending"


class ApprovalManager:
    """In-memory approval queue for the first release.

    Persistent approvals will only be added after authentication and replay
    protection are implemented. Nothing in this class executes an operation.
    """

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def create(self, capability: str, reason: str) -> ApprovalRequest:
        request = ApprovalRequest(
            request_id=token_urlsafe(18),
            capability=capability,
            reason=reason,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._requests[request.request_id] = request
        return request

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._requests.get(request_id)

    def list_pending(self) -> list[ApprovalRequest]:
        return [item for item in self._requests.values() if item.status == "pending"]
