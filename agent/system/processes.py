from __future__ import annotations

import psutil


def get_process_inventory() -> list[dict[str, object]]:
    """Return non-invasive information about currently running processes."""
    processes: list[dict[str, object]] = []

    for process in psutil.process_iter(["pid", "name", "username", "status"]):
        try:
            info = process.info
            processes.append(
                {
                    "pid": info.get("pid"),
                    "name": info.get("name"),
                    "username": info.get("username"),
                    "status": info.get("status"),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return sorted(processes, key=lambda item: (item["name"] or "", item["pid"] or 0))
