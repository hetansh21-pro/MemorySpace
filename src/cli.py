"""
MemorySpace Command Line Interface
"""

import sys
import os
import time
import argparse
from typing import List

from .config import load_config
from .core.monitor import get_memory_stats, get_top_processes
from .core.protector import (
    protect_all_configured_apps,
    add_app_to_protection,
    remove_app_from_protection,
)
from .core.optimizer import optimize_memory_soft
from .daemon import run_daemon, is_daemon_running, stop_daemon
from .web.server import start_web_server

# ANSI Color codes
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BLUE = "\033[34m"
GRAY = "\033[90m"
RESET = "\033[0m"


def print_banner():
    print(f"{CYAN}{BOLD}================================================================={RESET}")
    print(f"{CYAN}{BOLD}       🧠 MemorySpace - Intelligent Task & Memory Guard          {RESET}")
    print(f"{CYAN}{BOLD}================================================================={RESET}")


def cmd_status():
    print_banner()
    stats = get_memory_stats()
    daemon_ok = is_daemon_running()
    config = load_config()

    daemon_badge = f"{GREEN}● ACTIVE GUARD{RESET}" if daemon_ok else f"{YELLOW}○ STANDBY{RESET}"
    print(f" Daemon Service: {daemon_badge}")

    # Status Message
    status = stats["status"]
    status_color = GREEN if status == "HEALTHY" else (YELLOW if status in ("ELEVATED", "HIGH_PRESSURE") else RED)
    print(f" System Health:  {status_color}{BOLD}{status}{RESET} - {stats['status_message']}")
    print("-" * 65)

    # RAM
    ram = stats["ram"]
    ram_bar_len = 30
    filled = int((ram["percent"] / 100) * ram_bar_len)
    bar = "█" * filled + "░" * (ram_bar_len - filled)
    ram_col = RED if ram["percent"] > 90 else (YELLOW if ram["percent"] > 80 else GREEN)
    print(f" {BOLD}Physical RAM:{RESET}   [{ram_col}{bar}{RESET}] {ram_col}{ram['percent']}%{RESET}")
    print(f"                 Used: {ram['used_gb']} GB / Total: {ram['total_gb']} GB (Avail: {ram['available_gb']} GB)")

    # Swap
    swap = stats["swap"]
    sw_filled = int((swap["percent"] / 100) * ram_bar_len)
    sw_bar = "█" * sw_filled + "░" * (ram_bar_len - sw_filled)
    print(f" {BOLD}Swap Memory:{RESET}    [{BLUE}{sw_bar}{RESET}] {swap['percent']}%")
    print(f"                 Used: {swap['used_gb']} GB / Total: {swap['total_gb']} GB (Free: {swap['free_gb']} GB)")

    # PSI Pressure
    psi = stats["psi"]
    print(f" {BOLD}Kernel PSI:{RESET}     10s Stall: {psi['some_avg10']}%  |  60s: {psi['some_avg60']}%  |  300s: {psi['some_avg300']}%")
    print(f"                 {GRAY}(Ubuntu triggers oom-kill if 10s-60s pressure exceeds 50% for 20s){RESET}")
    print("-" * 65)

    # Protected apps summary
    p_res = protect_all_configured_apps()
    protected_apps = config.get("protected_apps", [])
    print(f" {BOLD}Protected Apps:{RESET} {', '.join(protected_apps[:8])} (+{max(0, len(protected_apps) - 8)} more)")
    if p_res.get("currently_protected"):
        print(f" {BOLD}Active Scopes Guarded:{RESET} {GREEN}{', '.join(p_res['currently_protected'])}{RESET}")
    print("-" * 65)

    # Top processes
    print(f" {BOLD}{'PID':<8} {'APP NAME':<22} {'MEM (MB)':<12} {'RAM %':<8} {'STATUS':<15}{RESET}")
    procs = get_top_processes(limit=8)
    for p in procs:
        status_tag = f"{GREEN}🛡️ PROTECTED{RESET}" if p["protected"] else f"{GRAY}Normal{RESET}"
        print(f" {p['pid']:<8} {p['name'][:20]:<22} {p['memory_mb']:<12} {p['memory_percent']:<8} {status_tag}")
    print("-" * 65)
    print(f" {GRAY}Tip: Run 'memoryspace optimize' to free buffers or 'memoryspace web' for dashboard.{RESET}\n")


def cmd_monitor():
    try:
        while True:
            # Clear terminal
            sys.stdout.write("\033[2J\033[H")
            cmd_status()
            print(f" {CYAN}Monitoring every 2.5s. Press Ctrl+C to stop...{RESET}")
            time.sleep(2.5)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")


def cmd_optimize():
    print(f"{CYAN}Performing safe memory optimization...{RESET}")
    res = optimize_memory_soft()
    for act in res.get("actions", []):
        print(f"  {GREEN}✔{RESET} {act}")
    stats = get_memory_stats()
    print(f"{GREEN}Done! Physical RAM is currently at {stats['ram']['percent']}% ({stats['ram']['available_gb']} GB available).{RESET}")


def cmd_protect(app_name: str):
    add_app_to_protection(app_name)
    print(f"{GREEN}✔ Successfully added '{app_name}' to protected apps! MemorySpace will shield it from kills.{RESET}")


def cmd_unprotect(app_name: str):
    remove_app_from_protection(app_name)
    print(f"{YELLOW}✔ Removed '{app_name}' from protected apps list.{RESET}")


def cmd_list_protected():
    config = load_config()
    apps = config.get("protected_apps", [])
    print(f"{BOLD}Currently configured protected applications:{RESET}")
    for a in apps:
        print(f"  {GREEN}🛡️{RESET} {a}")


def cmd_daemon(action: str):
    if action == "start":
        if is_daemon_running():
            print(f"{YELLOW}MemorySpace daemon is already running.{RESET}")
            return
        print(f"{GREEN}Starting MemorySpace daemon in background...{RESET}")
        # Run daemon in background process
        import subprocess
        python_bin = sys.executable
        daemon_script = Path(__file__).resolve().parent.parent / "bin" / "memoryspace"
        subprocess.Popen([python_bin, str(daemon_script), "daemon-run"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        if is_daemon_running():
            print(f"{GREEN}✔ MemorySpace daemon is now active and guarding processes!{RESET}")
        else:
            print(f"{RED}Failed to verify daemon startup. Check ~/.local/state/memoryspace/daemon.log{RESET}")

    elif action == "stop":
        if stop_daemon():
            print(f"{GREEN}✔ MemorySpace daemon stopped.{RESET}")
        else:
            print(f"{YELLOW}Daemon was not running.{RESET}")

    elif action == "status":
        if is_daemon_running():
            print(f"{GREEN}● MemorySpace daemon is RUNNING and guarding your apps.{RESET}")
        else:
            print(f"{YELLOW}○ MemorySpace daemon is STOPPED.{RESET}")


def main():
    parser = argparse.ArgumentParser(
        prog="memoryspace",
        description="MemorySpace - Intelligent Memory Management & Task Protector",
    )
    subparsers = parser.add_subparsers(dest="command")

    # status
    subparsers.add_parser("status", help="Show current memory status & protected tasks")

    # monitor
    subparsers.add_parser("monitor", help="Live terminal monitor")

    # optimize
    subparsers.add_parser("optimize", help="Safely free memory buffers and trim caches")

    # protect
    p_parser = subparsers.add_parser("protect", help="Add an application to protected list")
    p_parser.add_argument("app", help="Application name or executable keyword (e.g. antigravity, node)")

    # unprotect
    u_parser = subparsers.add_parser("unprotect", help="Remove an application from protected list")
    u_parser.add_argument("app", help="Application name to unprotect")

    # list
    subparsers.add_parser("list", help="List all protected applications")

    # daemon
    d_parser = subparsers.add_parser("daemon", help="Manage background daemon")
    d_parser.add_argument("action", choices=["start", "stop", "status", "restart"])

    # daemon-run (internal)
    subparsers.add_parser("daemon-run", help=argparse.SUPPRESS)

    # web
    w_parser = subparsers.add_parser("web", help="Launch Web Dashboard")
    w_parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    w_parser.add_argument("--port", type=int, default=7890, help="Port (default: 7890)")

    args = parser.parse_args()

    if args.command in (None, "status"):
        cmd_status()
    elif args.command == "monitor":
        cmd_monitor()
    elif args.command == "optimize":
        cmd_optimize()
    elif args.command == "protect":
        cmd_protect(args.app)
    elif args.command == "unprotect":
        cmd_unprotect(args.app)
    elif args.command == "list":
        cmd_list_protected()
    elif args.command == "daemon":
        if args.action == "restart":
            cmd_daemon("stop")
            time.sleep(1)
            cmd_daemon("start")
        else:
            cmd_daemon(args.action)
    elif args.command == "daemon-run":
        run_daemon()
    elif args.command == "web":
        start_web_server(args.host, args.port, block=True)


if __name__ == "__main__":
    main()
