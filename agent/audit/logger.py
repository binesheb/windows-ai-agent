from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


class AuditLogger:
    """Append-only JSONL audit logger for security-relevant agent events."""

    def __init__(self, path: str | Path = "logs/audit.jsonl") -> None:
        self.path = Path(path)
        self._lock = Lock()

    def record(self, action: str, result: str, *, details: dict[str, Any] | None = None) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "result": result,
            "details": details or {},
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, separators=(",", ":")) + "\n")


def audit(action: str, result: str, *, details: dict[str, Any] | None = None) -> None:
    AuditLogger().record(action, result, details=details)
