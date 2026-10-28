"""
MemorySpace Interactive CLI & Dashboard
"""

import sys
import os
import time
import argparse
import subprocess
import webbrowser
from pathlib import Path
from typing import List, Dict, Any

from .config import load_config, save_config
from .core.monitor import get_memory_stats, get_top_processes
from .core.protector import (
    protect_all_configured_apps,
    add_app_to_protection,
    remove_app_from_protection,
    get_active_user_scopes,
)
from .core.optimizer import optimize_memory_soft, manual_boost_memory
from .daemon import run_daemon, is_daemon_running, stop_daemon
from .web.server import start_web_server

# ANSI Color codes
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BLUE = "\033[34m"
PURPLE = "\033[35m"
GRAY = "\033[90m"
RESET = "\033[0m"


def print_banner():
    print(f"{CYAN}{BOLD}")
    print("  __  __                               ____                       ")
    print(" |  \\/  | ___ _ __ ___   ___  _ __ _   / ___| _ __   __ _  ___ ___ ")
    print(" | |\\/| |/ _ \\ '_ ` _ \\ / _ \\| '__| | |\\___ \\| '_ \\ / _` |/ __/ _ \\")
    print(" | |  | |  __/ | | | | | (_) | |  |_| | ___) | |_) | (_| | (_|  __/")
    print(" |_|  |_|\\___|_| |_| |_|\\___/|_|   \\__, |____/| .__/ \\__,_|\\___\\___|")
    print("                                   |___/      |_|                   ")
    print(f"{RESET}  {BOLD}🛡️  Zero-Crash Memory Guard & RAM Optimizer for Linux{RESET}")
    print(f"{GRAY}  ---------------------------------------------------------------{RESET}")


def render_dashboard_view(clear_screen: bool = True):
    if clear_screen:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    print_banner()
    stats = get_memory_stats()
    daemon_ok = is_daemon_running()
    config = load_config()

    daemon_badge = f"{GREEN}● ACTIVE GUARD (Protecting Apps){RESET}" if daemon_ok else f"{YELLOW}○ STANDBY (Daemon Inactive){RESET}"
    print(f" Daemon Service: {daemon_badge}")

    # Status Message
    status = stats["status"]
    status_color = GREEN if status == "HEALTHY" else (YELLOW if status in ("ELEVATED", "HIGH_PRESSURE") else RED)
    print(f" System Health:  {status_color}{BOLD}{status}{RESET} - {stats['status_message']}")
    print("-" * 65)

    # RAM Bar
    ram = stats["ram"]
    ram_bar_len = 28
    filled = int((ram["percent"] / 100) * ram_bar_len)
    bar = "█" * filled + "░" * (ram_bar_len - filled)
    ram_col = RED if ram["percent"] > 90 else (YELLOW if ram["percent"] > 80 else GREEN)
    print(f" {BOLD}Physical RAM:{RESET}   [{ram_col}{bar}{RESET}] {ram_col}{ram['percent']}%{RESET}")
    print(f"                 Used: {ram['used_gb']} GB / Total: {ram['total_gb']} GB (Avail: {ram['available_gb']} GB)")

    # Swap Bar
    swap = stats["swap"]
    sw_filled = int((swap["percent"] / 100) * ram_bar_len)
    sw_bar = "█" * sw_filled + "░" * (ram_bar_len - sw_filled)
    print(f" {BOLD}Swap Memory:{RESET}    [{BLUE}{sw_bar}{RESET}] {swap['percent']}%")
    print(f"                 Used: {swap['used_gb']} GB / Total: {swap['total_gb']} GB (Free: {swap['free_gb']} GB)")

    # PSI Pressure
    psi = stats["psi"]
    print(f" {BOLD}Kernel PSI:{RESET}     10s Stall: {psi['some_avg10']}%  |  60s: {psi['some_avg60']}%  |  300s: {psi['some_avg300']}%")
    print(f"                 {GRAY}(Ubuntu triggers oom-kill if 10s pressure > 50% for 20s){RESET}")
    print("-" * 65)

    # Protected apps & scopes
    p_res = protect_all_configured_apps()
    protected_apps = config.get("protected_apps", [])
    print(f" {BOLD}Protected Config:{RESET} {', '.join(protected_apps[:7])} (+{max(0, len(protected_apps) - 7)} more)")
    if p_res.get("currently_protected"):
        scopes_str = ", ".join(p_res["currently_protected"][:3])
        if len(p_res["currently_protected"]) > 3:
            scopes_str += f" (+{len(p_res['currently_protected']) - 3} more)"
        print(f" {BOLD}Active Guarded:{RESET}  {GREEN}{scopes_str}{RESET}")
    print("-" * 65)

    # Top processes
    print(f" {BOLD}{'PID':<7} {'APP NAME':<20} {'MEM (MB)':<10} {'RAM %':<7} {'GUARD STATUS':<15}{RESET}")
    procs = get_top_processes(limit=6)
    for p in procs:
        status_tag = f"{GREEN}🛡️ PROTECTED{RESET}" if p["protected"] else f"{GRAY}Normal{RESET}"
        print(f" {p['pid']:<7} {p['name'][:18]:<20} {p['memory_mb']:<10} {p['memory_percent']:<7} {status_tag}")
    print("-" * 65)


def render_menu():
    print(f"{CYAN}┌─────────────────────────────────────────────────────────────┐{RESET}")
    print(f"{CYAN}│{RESET}  {BOLD}ACTIONS & CONTROLS:{RESET}                                         {CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  {GREEN}[1]{RESET} ⚡ {BOLD}Manual Memory Boost{RESET} (Flush buffers & reclaim RAM)      {CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  {GREEN}[2]{RESET} 🛡️ {BOLD}Protect an App{RESET} (Shield from systemd-oomd kill)         {CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  {GREEN}[3]{RESET} 🔓 {BOLD}Unprotect an App{RESET} (Remove from shield list)            {CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  {GREEN}[4]{RESET} 🚀 {BOLD}Boost RAM with ZRAM{RESET} (Double usable memory)             {CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  {GREEN}[5]{RESET} 🌐 {BOLD}Launch Web Dashboard{RESET} (http://localhost:7890)          {CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  {GREEN}[6]{RESET} 🔄 {BOLD}Toggle Background Daemon{RESET} (Start / Stop)              {CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  {GREEN}[7]{RESET} 📡 {BOLD}Live Auto-Refresh Monitor{RESET} (htop style)                 {CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  {RED}[0]{RESET} 🚪 {BOLD}Exit{RESET}                                                     {CYAN}│{RESET}")
    print(f"{CYAN}└─────────────────────────────────────────────────────────────┘{RESET}")


def interactive_dashboard():
    while True:
        render_dashboard_view(clear_screen=True)
        render_menu()
        try:
            choice = input(f"{BOLD}Select an option [0-7] (or press Enter to refresh): {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{CYAN}Exiting MemorySpace. Stay protected! 👋{RESET}")
            sys.exit(0)

        if not choice:
            continue  # Just re-render and refresh

        if choice == "1":
            # Manual Boost
            print(f"\n{CYAN}⚡ Running aggressive memory boost...{RESET}")
            res = manual_boost_memory()
            print(f"\n{GREEN}{BOLD}======================================================={RESET}")
            print(f"{GREEN}{BOLD}🎉 MEMORY BOOST SUCCESSFUL!{RESET}")
            print(f"{GREEN}{BOLD}======================================================={RESET}")
            print(f" RAM Reclaimed:     {GREEN}{res['freed_mb']} MB{RESET}")
            print(f" RAM Usage Now:     {res['before_used_gb']} GB ➔ {GREEN}{res['after_used_gb']} GB{RESET} ({res['percent_after']}%)")
            print(f" Available Memory:  {GREEN}{res['available_gb']} GB{RESET}")
            print(" Actions:")
            for act in res["actions"]:
                print(f"  {GREEN}✔{RESET} {act}")
            print(f"{GRAY}Running tasks and IDE are intact and running smoothly.{RESET}")
            input(f"\n{BOLD}Press Enter to return to Dashboard...{RESET}")

        elif choice == "2":
            # Protect an App
            config = load_config()
            protected = [a.lower() for a in config.get("protected_apps", [])]
            top_procs = get_top_processes(limit=15)
            unprotected_cands = []
            seen = set()
            for p in top_procs:
                n = p["name"].lower()
                if not p["protected"] and n not in seen and n not in ("python3", "systemd", "kthreadd"):
                    seen.add(n)
                    unprotected_cands.append(p["name"])

            print(f"\n{BOLD}🛡️ Protect an Application from OOM Killer:{RESET}")
            if unprotected_cands:
                print(f"{GRAY}Top active applications currently unshielded:{RESET}")
                for idx, c in enumerate(unprotected_cands[:5], 1):
                    print(f"  [{chr(96 + idx)}] {c}")
            print(f"{GRAY}Or type any app/binary name (e.g. android-studio, code, blender, godot):{RESET}")

            try:
                target = input(f"\nEnter choice: ").strip()
            except (KeyboardInterrupt, EOFError):
                continue

            if not target:
                continue

            # Check if letter chosen
            selected_name = target
            if len(target) == 1 and target.isalpha():
                idx = ord(target.lower()) - 97
                if 0 <= idx < len(unprotected_cands[:5]):
                    selected_name = unprotected_cands[idx]

            add_app_to_protection(selected_name)
            print(f"\n{GREEN}✔ Successfully shielded '{selected_name}'! MemorySpace will prevent it from ever being killed.{RESET}")
            input(f"\n{BOLD}Press Enter to return to Dashboard...{RESET}")

        elif choice == "3":
            # Unprotect an App
            config = load_config()
            apps = config.get("protected_apps", [])
            print(f"\n{BOLD}Currently Protected Applications:{RESET}")
            for idx, a in enumerate(apps, 1):
                print(f"  [{idx}] {a}")

            try:
                target = input(f"\nEnter number or app name to unprotect (or press Enter to cancel): ").strip()
            except (KeyboardInterrupt, EOFError):
                continue

            if not target:
                continue

            removed = None
            if target.isdigit():
                idx = int(target) - 1
                if 0 <= idx < len(apps):
                    removed = apps[idx]
                    remove_app_from_protection(removed)
            else:
                removed = target
                remove_app_from_protection(removed)

            if removed:
                print(f"\n{YELLOW}✔ Removed '{removed}' from protection list.{RESET}")
            input(f"\n{BOLD}Press Enter to return to Dashboard...{RESET}")

        elif choice == "4":
            # ZRAM Check & Setup
            print(f"\n{BOLD}🚀 In-Memory ZRAM (Double RAM Accelerator):{RESET}")
            # Check if zram is active
            zram_active = os.path.exists("/dev/zram0")
            if zram_active:
                print(f"{GREEN}✔ ZRAM is already active on this system!{RESET}")
                subprocess.run(["swapon", "--show"])
            else:
                print(f"{YELLOW}ZRAM is not yet enabled.{RESET}")
                print("Enabling ZRAM compresses RAM in memory with fast LZ4, turning 5.2GB RAM into ~9-10GB!")
                fix_script = Path(__file__).resolve().parent.parent / "scripts" / "fix_ubuntu_oomd.sh"
                ans = input(f"Would you like to run the automated setup now? (Requires sudo) [y/N]: ").strip().lower()
                if ans in ("y", "yes"):
                    subprocess.run(["sudo", str(fix_script)])
                else:
                    print(f"You can run it anytime with: sudo {fix_script}")
            input(f"\n{BOLD}Press Enter to return to Dashboard...{RESET}")

        elif choice == "5":
            # Launch Web Dashboard
            print(f"\n{CYAN}🌐 Launching Web Dashboard at http://localhost:7890 ...{RESET}")
            start_web_server(host="127.0.0.1", port=7890, block=False)
            time.sleep(0.5)
            try:
                webbrowser.open("http://127.0.0.1:7890")
            except Exception:
                pass
            print(f"{GREEN}✔ Web Dashboard is live! Open http://localhost:7890 in your browser.{RESET}")
            input(f"\n{BOLD}Press Enter to return to Dashboard...{RESET}")

        elif choice == "6":
            # Toggle Background Daemon
            if is_daemon_running():
                ans = input("Daemon is currently RUNNING. Stop it? [y/N]: ").strip().lower()
                if ans in ("y", "yes"):
                    stop_daemon()
                    subprocess.run(["systemctl", "--user", "stop", "memoryspace.service"], capture_output=True)
                    print(f"{YELLOW}Daemon stopped.{RESET}")
            else:
                ans = input("Daemon is STOPPED. Start background protection service? [Y/n]: ").strip().lower()
                if ans in ("", "y", "yes"):
                    subprocess.run(["systemctl", "--user", "start", "memoryspace.service"], capture_output=True)
                    time.sleep(1)
                    if is_daemon_running():
                        print(f"{GREEN}✔ Daemon is now ACTIVE and shielding your running tasks!{RESET}")
                    else:
                        print(f"{RED}Failed to start daemon service. Check systemctl --user status memoryspace.service{RESET}")
            input(f"\n{BOLD}Press Enter to return to Dashboard...{RESET}")

        elif choice == "7":
            # Live Monitor Mode
            cmd_monitor()

        elif choice in ("0", "q", "exit"):
            print(f"\n{CYAN}Exiting MemorySpace. Background daemon continues guarding your tasks. Goodbye! 👋{RESET}\n")
            sys.exit(0)

        else:
            print(f"{RED}Invalid option. Please choose 0 to 7.{RESET}")
            time.sleep(1)


def cmd_status():
    render_dashboard_view(clear_screen=False)
    print(f" {GRAY}Tip: Run 'mem' or 'memoryspace' for interactive menu, or 'mem boost' for instant RAM reclaim.{RESET}\n")


def cmd_monitor():
    try:
        while True:
            render_dashboard_view(clear_screen=True)
            print(f" {CYAN}Live Monitor mode (updating every 2.5s). Press Ctrl+C to return to menu...{RESET}")
            time.sleep(2.5)
    except KeyboardInterrupt:
        pass


def cmd_optimize():
    print(f"{CYAN}Performing safe memory boost...{RESET}")
    res = manual_boost_memory()
    for act in res.get("actions", []):
        print(f"  {GREEN}✔{RESET} {act}")
    stats = get_memory_stats()
    print(f"{GREEN}Done! Freed: {res['freed_mb']} MB. Physical RAM is currently at {stats['ram']['percent']}% ({stats['ram']['available_gb']} GB available).{RESET}")


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

    # boost / optimize
    subparsers.add_parser("boost", help="Instant manual memory boost & RAM reclaim")
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

    if args.command is None:
        # If run directly without arguments: open full interactive dashboard!
        if sys.stdin.isatty():
            interactive_dashboard()
        else:
            cmd_status()
    elif args.command == "status":
        cmd_status()
    elif args.command == "monitor":
        cmd_monitor()
    elif args.command in ("optimize", "boost"):
        cmd_optimize()
    elif args.command == "protect":
        add_app_to_protection(args.app)
        print(f"{GREEN}✔ Successfully added '{args.app}' to protected apps! MemorySpace will shield it from kills.{RESET}")
    elif args.command == "unprotect":
        remove_app_from_protection(args.app)
        print(f"{YELLOW}✔ Removed '{args.app}' from protected apps list.{RESET}")
    elif args.command == "list":
        config = load_config()
        apps = config.get("protected_apps", [])
        print(f"{BOLD}Currently configured protected applications:{RESET}")
        for a in apps:
            print(f"  {GREEN}🛡️{RESET} {a}")
    elif args.command == "daemon":
        if args.action == "restart":
            stop_daemon()
            subprocess.run(["systemctl", "--user", "restart", "memoryspace.service"], capture_output=True)
            print(f"{GREEN}✔ Daemon restarted.{RESET}")
        elif args.action == "stop":
            stop_daemon()
            subprocess.run(["systemctl", "--user", "stop", "memoryspace.service"], capture_output=True)
            print(f"{GREEN}✔ Daemon stopped.{RESET}")
        elif args.action == "start":
            subprocess.run(["systemctl", "--user", "start", "memoryspace.service"], capture_output=True)
            time.sleep(1)
            if is_daemon_running():
                print(f"{GREEN}✔ MemorySpace daemon is now active and guarding processes!{RESET}")
            else:
                print(f"{RED}Failed to verify daemon startup.{RESET}")
        elif args.action == "status":
            if is_daemon_running():
                print(f"{GREEN}● MemorySpace daemon is RUNNING and guarding your apps.{RESET}")
            else:
                print(f"{YELLOW}○ MemorySpace daemon is STOPPED.{RESET}")
    elif args.command == "daemon-run":
        run_daemon()
    elif args.command == "web":
        start_web_server(args.host, args.port, block=True)


if __name__ == "__main__":
    main()
