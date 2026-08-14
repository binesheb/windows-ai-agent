from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


CONFIG_PATH = Path("config/agent.yml")


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def filesystem_settings() -> tuple[list[str], int, int]:
    config = load_config()
    filesystem = config.get("filesystem", {})
    workspaces = filesystem.get("workspaces") or []

    roots: list[str] = []
    for workspace in workspaces:
        if not isinstance(workspace, dict):
            continue
        if str(workspace.get("access", "read")).lower() != "read":
            continue
        path = workspace.get("path")
        if path:
            roots.append(str(path))

    # Backward-compatible fallback for older configurations.
    if not roots:
        roots = [str(root) for root in (filesystem.get("allowed_roots") or ["."])]

    max_read_bytes = int(filesystem.get("max_read_bytes", 1_048_576))
    max_entries = int(filesystem.get("max_entries", 500))
    return roots, max_read_bytes, max_entries


def filesystem_workspaces() -> list[dict[str, str]]:
    config = load_config()
    filesystem = config.get("filesystem", {})
    workspaces = filesystem.get("workspaces") or []

    result: list[dict[str, str]] = []
    for workspace in workspaces:
        if not isinstance(workspace, dict):
            continue
        name = workspace.get("name")
        path = workspace.get("path")
        access = str(workspace.get("access", "read")).lower()
        if name and path and access == "read":
            result.append({"name": str(name), "path": str(path), "access": access})
    return result
