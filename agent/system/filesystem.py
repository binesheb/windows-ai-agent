from __future__ import annotations

from pathlib import Path

MAX_READ_BYTES = 1_048_576
MAX_ENTRIES = 500


def list_directory(path: Path, limit: int = MAX_ENTRIES) -> list[dict]:
    """Return metadata only; never reads file contents."""
    entries: list[dict] = []
    for entry in sorted(path.iterdir(), key=lambda item: item.name.casefold()):
        if len(entries) >= limit:
            break
        try:
            stat = entry.stat()
            entries.append(
                {
                    "name": entry.name,
                    "path": str(entry),
                    "type": "directory" if entry.is_dir() else "file",
                    "size_bytes": stat.st_size if entry.is_file() else None,
                }
            )
        except (OSError, PermissionError):
            continue
    return entries


def read_text_file(path: Path, max_bytes: int = MAX_READ_BYTES) -> dict:
    """Read a bounded text file as UTF-8, with replacement for invalid bytes."""
    if not path.is_file():
        raise FileNotFoundError(str(path))

    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"File exceeds the {max_bytes} byte read limit")

    data = path.read_bytes()
    return {
        "path": str(path),
        "size_bytes": size,
        "content": data.decode("utf-8", errors="replace"),
    }
