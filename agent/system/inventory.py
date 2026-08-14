from __future__ import annotations

import platform
import socket
from datetime import datetime, timezone

import psutil


def _gb(value: int) -> float:
    return round(value / (1024**3), 2)


def get_system_inventory() -> dict:
    memory = psutil.virtual_memory()
    disks = []
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except OSError:
            continue
        disks.append(
            {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "filesystem": partition.fstype,
                "total_gb": _gb(usage.total),
                "free_gb": _gb(usage.free),
                "used_percent": usage.percent,
            }
        )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "computer": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
        },
        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=0.2),
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
        },
        "memory": {
            "total_gb": _gb(memory.total),
            "available_gb": _gb(memory.available),
            "used_percent": memory.percent,
        },
        "disks": disks,
    }
