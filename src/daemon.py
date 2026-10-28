"""
MemorySpace Background Daemon
Silently monitors memory, auto-protects user apps from being killed, and manages pressure.
Operates in quiet mode so it protects without annoying the user with notifications.
"""

import os
import sys
import time
import signal
from pathlib import Path
from .config import load_config
from .core.monitor import get_memory_stats, get_top_processes
from .core.protector import protect_all_configured_apps
from .core.optimizer import optimize_memory_soft
from .core.notifier import send_desktop_notification

LOG_DIR = Path.home() / ".local" / "state" / "memoryspace"
LOG_FILE = LOG_DIR / "daemon.log"
PID_FILE = LOG_DIR / "memoryspace.pid"

_running = True


def _log(msg: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def _sig_handler(signum, frame):
    global _running
    _log(f"Received signal {signum}, stopping MemorySpace daemon...")
    _running = False


def run_daemon() -> None:
    global _running
    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))

    _log("MemorySpace daemon started successfully in quiet background mode.")

    try:
        while _running:
            config = load_config()
            interval = config.get("check_interval_seconds", 3)
            thresholds = config.get("thresholds", {})
            opt_p = thresholds.get("optimize_percent", 90.0)
            crit_p = thresholds.get("critical_percent", 95.0)

            # 1. Protect all active scopes from systemd-oomd
            prot_res = protect_all_configured_apps()
            if prot_res.get("newly_protected"):
                for p in prot_res["newly_protected"]:
                    _log(f"Protected scope from systemd-oomd: {p}")

            # 2. Check memory metrics
            stats = get_memory_stats()
            ram_pct = stats["ram"]["percent"]
            psi_some = stats["psi"].get("some_avg10", 0.0)

            # Critical threshold (> 95%): Silent optimization + optional emergency alert
            if ram_pct >= crit_p:
                top_procs = get_top_processes(limit=3)
                proc_summary = ", ".join([f"{p['name']} ({p['memory_mb']}MB)" for p in top_procs])
                _log(f"CRITICAL: RAM at {ram_pct}%, PSI={psi_some}%. Top consumers: {proc_summary}")
                optimize_memory_soft()
                send_desktop_notification(
                    "MemorySpace: Critical Memory",
                    f"RAM is at {ram_pct}%. Active tasks remain protected.",
                    urgency="critical",
                    category="critical",
                )

            # High pressure threshold (> 90%): Optimize silently in background (No annoying popups)
            elif ram_pct >= opt_p:
                _log(f"HIGH PRESSURE: RAM at {ram_pct}%, PSI={psi_some}%. Auto-optimizing quietly...")
                opt_res = optimize_memory_soft()
                if opt_res.get("actions"):
                    _log("Optimization actions: " + "; ".join(opt_res["actions"]))

            time.sleep(interval)
    finally:
        if PID_FILE.exists():
            try:
                PID_FILE.unlink()
            except Exception:
                pass
        _log("MemorySpace daemon stopped.")


def is_daemon_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, OSError):
        return False


def stop_daemon() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        return True
    except Exception:
        return False
