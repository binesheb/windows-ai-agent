from __future__ import annotations

import platform
from typing import Any, Callable

import psutil


def _safe_service_value(getter: Callable[[], Any]) -> Any:
    """Read one service property without allowing one broken entry to abort inventory."""
    try:
        return getter()
    except (FileNotFoundError, OSError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, psutil.Error):
        return None


def get_service_inventory(limit: int = 500) -> list[dict[str, object]]:
    """Return a bounded, read-only snapshot of Windows services.

    Windows service metadata can disappear or become inaccessible while the
    inventory is being collected. Each property is therefore queried safely
    so one problematic service cannot turn the whole endpoint into a 500.
    """
    if platform.system() != "Windows":
        raise RuntimeError("Windows service inventory is only supported on Windows")

    services: list[dict[str, object]] = []
    for service in psutil.win_service_iter():
        try:
            name = _safe_service_value(service.name)
            display_name = _safe_service_value(service.display_name)
            services.append(
                {
                    "name": name,
                    "display_name": display_name,
                    "status": _safe_service_value(service.status),
                    "start_type": _safe_service_value(service.start_type),
                    "username": _safe_service_value(service.username),
                    "description": _safe_service_value(service.description),
                    "binpath": _safe_service_value(service.binpath),
                    "pid": _safe_service_value(service.pid),
                }
            )
        except (FileNotFoundError, OSError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, psutil.Error):
            # A service can disappear or become inaccessible between enumeration
            # and property lookup. Skip only that service and continue safely.
            continue

    services.sort(key=lambda item: str(item.get("display_name") or item.get("name") or "").lower())
    return services[:limit]
