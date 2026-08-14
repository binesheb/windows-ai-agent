from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathDecision:
    allowed: bool
    normalized: str
    reason: str


# These locations are never readable through the agent, even if a workspace
# is accidentally configured too broadly.
SENSITIVE_PREFIXES = (
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\ProgramData",
)

SENSITIVE_USER_SUFFIXES = (
    r".ssh",
    r"AppData\Roaming\Microsoft\Credentials",
    r"AppData\Local\Microsoft\Credentials",
    r"AppData\Local\Google\Chrome\User Data",
    r"AppData\Local\Microsoft\Edge\User Data",
)


def normalize_path(value: str) -> Path:
    """Return an absolute, normalized Windows path without touching the file."""
    expanded = os.path.expandvars(os.path.expanduser(value.strip()))
    return Path(os.path.abspath(os.path.normpath(expanded)))


def _casefold(path: Path) -> str:
    return str(path).replace("/", "\\").rstrip("\\").casefold()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def is_sensitive(path: Path) -> bool:
    candidate = _casefold(path)

    for prefix in SENSITIVE_PREFIXES:
        p = prefix.casefold().rstrip("\\")
        if candidate == p or candidate.startswith(p + "\\"):
            return True

    home = Path.home()
    for suffix in SENSITIVE_USER_SUFFIXES:
        sensitive = home / suffix
        if _is_within(path, sensitive):
            return True

    return False


def evaluate_path(value: str, allowed_roots: list[str]) -> PathDecision:
    try:
        path = normalize_path(value)
    except (OSError, ValueError) as exc:
        return PathDecision(False, value, f"Invalid path: {exc}")

    if is_sensitive(path):
        return PathDecision(False, str(path), "Path is protected by the sensitive-path policy")

    roots = [normalize_path(root) for root in allowed_roots]
    if not any(_is_within(path, root) or path == root for root in roots):
        return PathDecision(False, str(path), "Path is outside configured read-only workspaces")

    return PathDecision(True, str(path), "Path is inside an allowed workspace")
