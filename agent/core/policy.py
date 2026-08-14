from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class Risk(str, Enum):
    READ = "read"
    SAFE_WRITE = "safe_write"
    SENSITIVE = "sensitive"
    DANGEROUS = "dangerous"


@dataclass(frozen=True)
class Decision:
    allowed: bool
    requires_approval: bool
    reason: str
    risk: Risk | None = None


class PolicyEngine:
    """Evaluates named capabilities. Unknown capabilities are always denied."""

    def __init__(self, policy_path: str | Path = "policies/default.yml") -> None:
        self.policy_path = Path(policy_path)
        self._policy: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        if not self.policy_path.exists():
            self._policy = {"agent": {"mode": "read_only"}, "capabilities": {}}
            return
        with self.policy_path.open("r", encoding="utf-8") as handle:
            self._policy = yaml.safe_load(handle) or {}

    def evaluate(self, capability: str) -> Decision:
        capabilities = self._policy.get("capabilities", {})
        entry = capabilities.get(capability)
        if not entry:
            return Decision(False, False, "Capability is not defined", None)

        risk_value = entry.get("risk", Risk.DANGEROUS.value)
        try:
            risk = Risk(risk_value)
        except ValueError:
            return Decision(False, False, "Policy contains an invalid risk level", None)

        if not bool(entry.get("enabled", False)):
            return Decision(False, False, "Capability is disabled by policy", risk)

        requires_approval = risk in {Risk.SENSITIVE, Risk.DANGEROUS}
        return Decision(True, requires_approval, "Capability is enabled by policy", risk)
