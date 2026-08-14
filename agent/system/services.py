from __future__ import annotations

import platform

import psutil


def get_service_inventory(limit: int = 500) -> list[dict[str, object]]:
    """Return a bounded, read-only snapshot of Windows services."""
    if platform.system() != "Windows":
        raise RuntimeError("Windows service inventory is only supported on Windows")

    services: list[dict[str, object]] = []
    for service in psutil.win_service_iter():
        try:
            info = service.as_dict()
            services.append(
                {
                    "name": info.get("name"),
                    "display_name": info.get("display_name"),
                    "status": info.get("status"),
                    "start_type": info.get("start_type"),
                    "username": info.get("username"),
                    "description": info.get("description"),
                    "binpath": info.get("binpath"),
                    "pid": info.get("pid"),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
            continue

    services.sort(key=lambda item: str(item.get("display_name") or item.get("name") or "").lower())
    return services[:limit]
