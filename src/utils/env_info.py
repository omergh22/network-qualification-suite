"""Machine / environment snapshot for qualification logs."""

from __future__ import annotations

import platform
import socket
import sys
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


def collect_environment_snapshot() -> dict[str, Any]:
    """Return a dict suitable for JSON logging (best-effort, no secrets)."""
    snap: dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "hostname": socket.gethostname(),
    }
    if psutil:
        try:
            snap["cpu_count_logical"] = psutil.cpu_count(logical=True)
            snap["cpu_count_physical"] = psutil.cpu_count(logical=False)
            vm = psutil.virtual_memory()
            snap["ram_total_mb"] = round(vm.total / (1024 * 1024), 2)
            snap["ram_available_mb"] = round(vm.available / (1024 * 1024), 2)
        except Exception:
            snap["cpu_ram_note"] = "psutil partial read failed"
    else:
        snap["note"] = "psutil not installed; limited hardware info"
    return snap
