from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Risk(str, Enum):
    READ = "read"
    SAFE_WRITE = "safe_write"
    SENSITIVE = "sensitive"
    DANGEROUS = "dangerous"


@dataclass(frozen=True)
class Capability:
    name: str
    description: str
    risk: Risk
    enabled_by_default: bool = False


CAPABILITIES: tuple[Capability, ...] = (
    Capability("system_inventory", "Inspect basic Windows system health", Risk.READ, True),
    Capability("filesystem_read", "Read files explicitly permitted by policy", Risk.READ),
    Capability("filesystem_write", "Create or modify files in permitted workspaces", Risk.SAFE_WRITE),
    Capability("process_read", "Inspect running processes", Risk.READ),
    Capability("process_control", "Start, stop, or otherwise control processes", Risk.SENSITIVE),
    Capability("service_read", "Inspect Windows services", Risk.READ),
    Capability("service_control", "Start, stop, or restart Windows services", Risk.SENSITIVE),
    Capability("powershell", "Execute a constrained PowerShell operation", Risk.DANGEROUS),
    Capability("git", "Perform approved Git operations", Risk.SAFE_WRITE),
    Capability("docker", "Perform approved Docker operations", Risk.SENSITIVE),
    Capability("network_read", "Inspect local network configuration", Risk.READ),
    Capability("network_control", "Change network configuration", Risk.DANGEROUS),
)


def all_capabilities() -> list[dict[str, object]]:
    return [
        {
            "name": capability.name,
            "description": capability.description,
            "risk": capability.risk.value,
            "enabled_by_default": capability.enabled_by_default,
        }
        for capability in CAPABILITIES
    ]
