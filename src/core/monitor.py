"""
MemorySpace System Monitor
Reads RAM, Swap, Kernel PSI (Pressure Stall Information), and process consumption.
"""

import os
from typing import Any, Dict, List
import psutil
from ..config import is_protected, load_config


def read_psi_memory() -> Dict[str, float]:
    """
    Reads Linux PSI (Pressure Stall Information) from /proc/pressure/memory.
    Returns avg10, avg60, avg300 for both 'some' and 'full' stalls.
    """
    psi_data = {
        "some_avg10": 0.0,
        "some_avg60": 0.0,
        "some_avg300": 0.0,
        "full_avg10": 0.0,
        "full_avg60": 0.0,
        "full_avg300": 0.0,
    }
    psi_path = "/proc/pressure/memory"
    if not os.path.exists(psi_path):
        return psi_data

    try:
        with open(psi_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                prefix = parts[0]  # 'some' or 'full'
                for item in parts[1:]:
                    if "=" in item:
                        k, v = item.split("=", 1)
                        if k in ("avg10", "avg60", "avg300"):
                            psi_data[f"{prefix}_{k}"] = float(v)
    except Exception:
        pass
    return psi_data


def get_memory_stats() -> Dict[str, Any]:
    """
    Returns current memory and swap snapshot.
    """
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    psi = read_psi_memory()

    config = load_config()
    thresholds = config.get("thresholds", {})
    warn_p = thresholds.get("warning_percent", 80.0)
    opt_p = thresholds.get("optimize_percent", 88.0)
    crit_p = thresholds.get("critical_percent", 94.0)
    psi_thresh = thresholds.get("psi_pressure_threshold", 35.0)

    # Determine status
    if vm.percent >= crit_p or psi.get("some_avg10", 0) >= 60.0:
        status = "CRITICAL"
        status_color = "red"
        status_msg = "Critical memory pressure! System at risk of OOM kills."
    elif vm.percent >= opt_p or psi.get("some_avg10", 0) >= psi_thresh:
        status = "HIGH_PRESSURE"
        status_color = "yellow"
        status_msg = "High memory usage detected. Soft optimization recommended."
    elif vm.percent >= warn_p or psi.get("some_avg10", 0) >= 20.0:
        status = "ELEVATED"
        status_color = "cyan"
        status_msg = "Elevated memory consumption. Monitoring active tasks."
    else:
        status = "HEALTHY"
        status_color = "green"
        status_msg = "Memory healthy. Running tasks running smoothly."

    return {
        "ram": {
            "total_bytes": vm.total,
            "total_gb": round(vm.total / (1024**3), 2),
            "used_bytes": vm.used,
            "used_gb": round(vm.used / (1024**3), 2),
            "free_bytes": vm.free,
            "free_gb": round(vm.free / (1024**3), 2),
            "available_bytes": vm.available,
            "available_gb": round(vm.available / (1024**3), 2),
            "percent": vm.percent,
        },
        "swap": {
            "total_bytes": sm.total,
            "total_gb": round(sm.total / (1024**3), 2),
            "used_bytes": sm.used,
            "used_gb": round(sm.used / (1024**3), 2),
            "free_bytes": sm.free,
            "free_gb": round(sm.free / (1024**3), 2),
            "percent": sm.percent,
        },
        "psi": psi,
        "status": status,
        "status_color": status_color,
        "status_message": status_msg,
    }


def get_top_processes(limit: int = 15) -> List[Dict[str, Any]]:
    """
    Returns top memory-consuming processes and their protection status.
    """
    config = load_config()
    protected_apps = config.get("protected_apps", [])
    procs = []

    for p in psutil.process_iter(
        ["pid", "name", "cmdline", "username", "memory_info", "memory_percent", "cpu_percent"]
    ):
        try:
            info = p.info
            mem_info = info.get("memory_info")
            if not mem_info:
                continue

            rss = mem_info.rss
            name = info.get("name") or "unknown"
            cmdline_list = info.get("cmdline") or []
            cmdline = " ".join(cmdline_list)

            # Check if this process matches protected patterns
            protected = is_protected(name, protected_apps) or is_protected(cmdline, protected_apps)

            procs.append({
                "pid": info["pid"],
                "name": name,
                "cmdline": cmdline[:100] + ("..." if len(cmdline) > 100 else ""),
                "username": info.get("username", ""),
                "memory_mb": round(rss / (1024**2), 1),
                "memory_gb": round(rss / (1024**3), 2),
                "memory_percent": round(info.get("memory_percent", 0.0), 1),
                "cpu_percent": round(info.get("cpu_percent", 0.0) or 0.0, 1),
                "protected": protected,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    procs.sort(key=lambda x: x["memory_mb"], reverse=True)
    return procs[:limit]
