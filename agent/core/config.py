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
    roots = filesystem.get("allowed_roots") or ["."]
    max_read_bytes = int(filesystem.get("max_read_bytes", 1_048_576))
    max_entries = int(filesystem.get("max_entries", 500))
    return [str(root) for root in roots], max_read_bytes, max_entries
