"""
MemorySpace Interactive CLI & Dashboard
High-precision, pixel-perfect terminal UI for Linux memory monitoring and task protection.
"""

import sys
import os
import re
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
DIM = "\033[2m"
RESET = "\033[0m"


def clean_human_scope_name(scope: str) -> str:
    """
    Converts ugly systemd scope names like:
    'app-gnome-brave\\x2dbrowser-29203.scope' -> 'Brave Browser'
    'app-antigravity-20809.scope' -> 'Antigravity'
    'ptyxis-spawn-1702c9ca.scope' -> 'Terminal'
    """
    s = scope.replace("\\x2d", "-").replace("\\\\x2d", "-")
    s = re.sub(r"\.scope$", "", s)
    s = re.sub(r"-[0-9a-f]{4,}$", "", s)
    s = re.sub(r"-[0-9]+$", "", s)
    s = re.sub(r"^app-gnome-org\.gnome\.", "", s)
    s = re.sub(r"^app-gnome-", "", s)
    s = re.sub(r"^app-org\.[^.]+\.", "", s)
    s = re.sub(r"^app-", "", s)
    if s.startswith("ptyxis-spawn") or "terminal" in s:
        return "Terminal"
    return s.replace("-", " ").title()


def get_zram_info() -> Dict[str, Any]:
    """
    Checks if ZRAM is active and returns size.
    """
    zram_path = Path("/sys/block/zram0")
    if zram_path.exists():
        try:
            with open(zram_path / "disksize", "r") as f:
                bytes_sz = int(f.read().strip())
                gb_sz = round(bytes_sz / (1024**3), 2)
                return {"active": True, "size_gb": gb_sz}
        except Exception:
            return {"active": True, "size_gb": 0.0}
    return {"active": False, "size_gb": 0.0}


def print_banner():
    print(f"{CYAN}{BOLD}")
    print("  __  __                               ____                       ")
    print(" |  \\/  | ___ _ __ ___   ___  _ __ _   / ___| _ __   __ _  ___ ___ ")
    print(" | |\\/| |/ _ \\ '_ ` _ \\ / _ \\| '__| | |\\___ \\| '_ \\ / _` |/ __/ _ \\")
    print(" | |  | |  __/ | | | | | (_) | |  |_| | ___) | |_) | (_| | (_|  __/")
    print(" |_|  |_|\\___|_| |_| |_|\\___/|_|   \\__, |____/| .__/ \\__,_|\\___\\___|")
    print("                                   |___/      |_|                   ")
    print(f"{RESET}  {BOLD}🛡️  Zero-Crash Memory Guard & RAM Optimizer for Linux{RESET}")
    print(f"{CYAN}─────────────────────────────────────────────────────────────────{RESET}")


def render_dashboard_view(clear_screen: bool = True):
    if clear_screen:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    print_banner()
    stats = get_memory_stats()
    daemon_ok = is_daemon_running()
    config = load_config()
    zram = get_zram_info()
    notif_cfg = config.get("notifications", {})

    # Daemon Status
    if daemon_ok:
        daemon_badge = f"{GREEN}{BOLD}● ACTIVE GUARD{RESET} {GRAY}(Protecting running apps){RESET}"
    else:
        daemon_badge = f"{YELLOW}○ STANDBY{RESET} {GRAY}(Run option 6 to start background protection){RESET}"
    print(f" Daemon Service: {daemon_badge}")

    # Notifications Status
    if notif_cfg.get("enabled", False):
        notif_badge = f"{YELLOW}Enabled (Critical Only){RESET}" if notif_cfg.get("critical_only", True) else f"{GREEN}Enabled (All){RESET}"
    else:
        notif_badge = f"{GREEN}{BOLD}🔕 QUIET MODE{RESET} {GRAY}(Muted - 100% silent background protection){RESET}"
    print(f" Notifications:  {notif_badge}")

    # System Health
    status = stats["status"]
    if status == "HEALTHY":
        status_color = GREEN
    elif status in ("ELEVATED", "HIGH_PRESSURE"):
        status_color = YELLOW
    else:
        status_color = RED
    print(f" System Health:  {status_color}{BOLD}{status}{RESET} - {stats['status_message']}")
    print(f"{CYAN}─────────────────────────────────────────────────────────────────{RESET}")

    # Physical RAM
    ram = stats["ram"]
    bar_len = 26
    filled = int((ram["percent"] / 100) * bar_len)
    filled = max(0, min(bar_len, filled))
    bar = "█" * filled + "░" * (bar_len - filled)
    ram_col = RED if ram["percent"] > 90 else (YELLOW if ram["percent"] > 80 else GREEN)
    print(f" {BOLD}Physical RAM:{RESET}   [{ram_col}{bar}{RESET}] {ram_col}{ram['percent']}%{RESET}")
    print(f"                 Used: {ram['used_gb']} GB / Total: {ram['total_gb']} GB (Avail: {ram['available_gb']} GB)")

    # Swap & ZRAM
    swap = stats["swap"]
    sw_filled = int((swap["percent"] / 100) * bar_len)
    sw_filled = max(0, min(bar_len, sw_filled))
    sw_bar = "█" * sw_filled + "░" * (bar_len - sw_filled)
    swap_label = "Swap / ZRAM:" if zram["active"] else "Swap Memory:"
    print(f" {BOLD}{swap_label:<15}{RESET} [{BLUE}{sw_bar}{RESET}] {swap['percent']}%")
    zram_tag = f" ({GREEN}ZRAM Active: {zram['size_gb']} GB Fast RAM{RESET})" if zram["active"] else ""
    print(f"                 Used: {swap['used_gb']} GB / Total: {swap['total_gb']} GB (Free: {swap['free_gb']} GB){zram_tag}")

    # Kernel PSI Pressure
    psi = stats["psi"]
    print(f" {BOLD}Kernel PSI:{RESET}     10s Stall: {psi['some_avg10']}%  |  60s: {psi['some_avg60']}%  |  300s: {psi['some_avg300']}%")
    print(f"                 {GRAY}(Ubuntu kills apps when 10s pressure > 50% for 20s){RESET}")
    print(f"{CYAN}─────────────────────────────────────────────────────────────────{RESET}")

    # Guarded Apps (clean human-readable names)
    p_res = protect_all_configured_apps()
    raw_scopes = p_res.get("currently_protected", [])
    clean_names = []
    seen = set()
    for s in raw_scopes:
        c = clean_human_scope_name(s)
        if c and c not in seen:
            seen.add(c)
            clean_names.append(c)

    if clean_names:
        display_apps = ", ".join(clean_names[:5])
        if len(clean_names) > 5:
            display_apps += f" (+{len(clean_names) - 5} more)"
        print(f" {BOLD}Guarded Apps:{RESET}   {GREEN}{display_apps}{RESET}")
        print(f"                 {GRAY}(Shielded from systemd-oomd with ManagedOOMPreference=omit){RESET}")
    else:
        print(f" {BOLD}Guarded Apps:{RESET}   {YELLOW}Scanning active applications...{RESET}")
    print(f"{CYAN}─────────────────────────────────────────────────────────────────{RESET}")

    # Top processes table
    header = f" {BOLD}{'PID':<7} {'APPLICATION':<22} {'MEMORY':<11} {'RAM %':<7} {'STATUS':<12}{RESET}"
    print(header)
    procs = get_top_processes(limit=6)
    for p in procs:
        p_name = p["name"][:20]
        p_mem = f"{p['memory_mb']} MB"
        p_ram = f"{p['memory_percent']}%"
        status_tag = f"{GREEN}{BOLD}● SHIELDED{RESET}" if p["protected"] else f"{GRAY}○ Normal{RESET}"
        print(f" {p['pid']:<7} {p_name:<22} {p_mem:<11} {p_ram:<7} {status_tag}")
    print(f"{CYAN}─────────────────────────────────────────────────────────────────{RESET}")


def render_menu():
    zram = get_zram_info()
    zram_desc = f"In-memory compression ({GREEN}Active: {zram['size_gb']} GB{RESET})" if zram["active"] else "In-memory compression (Double RAM)"
    config = load_config()
    notif_enabled = config.get("notifications", {}).get("enabled", False)
    notif_label = "Enable Notifications" if not notif_enabled else "Mute Notifications (Quiet Mode)"
    notif_icon = "🔔" if not notif_enabled else "🔕"

    print(f"{CYAN}╭─────────────────────────────────────────────────────────────╮{RESET}")
    print(f"{CYAN}│{RESET}  {BOLD}ACTIONS & CONTROLS{RESET}                                         {CYAN}│{RESET}")
    print(f"{CYAN}╰─────────────────────────────────────────────────────────────╯{RESET}")
    print(f"  {GREEN}{BOLD}[1]{RESET} ⚡ {BOLD}Manual Memory Boost{RESET}     {GRAY}Flush buffers & reclaim free RAM{RESET}")
    print(f"  {GREEN}{BOLD}[2]{RESET} 🛡️  {BOLD}Protect Application{RESET}     {GRAY}Shield app from systemd-oomd kill{RESET}")
    print(f"  {GREEN}{BOLD}[3]{RESET} 🔓 {BOLD}Unprotect App{RESET}           {GRAY}Remove from shield list{RESET}")
    print(f"  {GREEN}{BOLD}[4]{RESET} 🚀 {BOLD}ZRAM Accelerator{RESET}        {GRAY}{zram_desc}{RESET}")
    print(f"  {GREEN}{BOLD}[5]{RESET} 🌐 {BOLD}Web Dashboard{RESET}           {GRAY}Open live UI at http://localhost:7890{RESET}")
    print(f"  {GREEN}{BOLD}[6]{RESET} 🔄 {BOLD}Daemon Service{RESET}          {GRAY}Toggle background active protection{RESET}")
    print(f"  {GREEN}{BOLD}[7]{RESET} 📡 {BOLD}Live Monitor{RESET}            {GRAY}Real-time htop-style stream{RESET}")
    print(f"  {GREEN}{BOLD}[8]{RESET} {notif_icon} {BOLD}{notif_label:<23}{RESET} {GRAY}Stop / enable desktop popups{RESET}")
    print(f"  {RED}{BOLD}[0]{RESET} 🚪 {BOLD}Exit{RESET}                    {GRAY}Quit MemorySpace{RESET}")
    print(f"{CYAN}─────────────────────────────────────────────────────────────{RESET}")


def interactive_dashboard():
    while True:
        render_dashboard_view(clear_screen=True)
        render_menu()
        try:
            choice = input(f"{BOLD}Select an option [0-8] (or press Enter to refresh): {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{CYAN}Exiting MemorySpace. Background daemon continues guarding your tasks. 👋{RESET}\n")
            sys.exit(0)

        if not choice:
            continue

        if choice == "1":
            # Manual Boost
            print(f"\n{CYAN}⚡ Running memory boost & buffer flush...{RESET}")
            res = manual_boost_memory()
            print(f"\n{GREEN}{BOLD}✔ Memory Boost Complete!{RESET}")
            print(f"  • RAM Reclaimed:     {GREEN}{res['freed_mb']} MB{RESET}")
            print(f"  • RAM Usage Now:     {res['before_used_gb']} GB ➔ {GREEN}{res['after_used_gb']} GB{RESET} ({res['percent_after']}%)")
            print(f"  • Available RAM:     {GREEN}{res['available_gb']} GB{RESET}")
            for act in res["actions"]:
                print(f"  • {GREEN}✔{RESET} {act}")
            print(f"{GRAY}Active applications and IDE are running smoothly.{RESET}")
            input(f"\n{BOLD}Press Enter to return to Dashboard...{RESET}")

        elif choice == "2":
            # Protect an App
            config = load_config()
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
            print(f"{GRAY}Or type any app/binary name (e.g. android-studio, blender, godot):{RESET}")

            try:
                target = input(f"\nEnter choice: ").strip()
            except (KeyboardInterrupt, EOFError):
                continue

            if not target:
                continue

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
            # ZRAM Status & Setup
            zram = get_zram_info()
            print(f"\n{BOLD}🚀 In-Memory ZRAM (Double RAM Accelerator):{RESET}")
            if zram["active"]:
                print(f"{GREEN}✔ ZRAM is ALREADY ACTIVE and accelerating your system!{RESET}")
                print(f"  • Compressed RAM size: {GREEN}{zram['size_gb']} GB{RESET}")
                print(f"  • Algorithm: LZ4 (ultra-fast near-memory speeds)")
                print(f"  • Your running tasks and compile jobs have tons of headroom.")
                subprocess.run(["swapon", "--show"])
            else:
                print(f"{YELLOW}ZRAM is not yet enabled.{RESET}")
                print("Enabling ZRAM compresses RAM in memory with fast LZ4, effectively doubling usable RAM!")
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

        elif choice == "8":
            # Toggle Notifications / Quiet Mode
            config = load_config()
            if "notifications" not in config:
                config["notifications"] = {}
            current_state = config["notifications"].get("enabled", False)
            new_state = not current_state
            config["notifications"]["enabled"] = new_state
            save_config(config)
            if new_state:
                print(f"\n{GREEN}✔ Desktop notifications enabled (critical alerts only).{RESET}")
            else:
                print(f"\n{GREEN}{BOLD}✔ QUIET MODE ACTIVATED! 🔕{RESET}")
                print(f"MemorySpace will guard your apps 100% silently in background with ZERO popups.")
            input(f"\n{BOLD}Press Enter to return to Dashboard...{RESET}")

        elif choice in ("0", "q", "exit"):
            print(f"\n{CYAN}Exiting MemorySpace. Background daemon continues guarding your tasks. Goodbye! 👋{RESET}\n")
            sys.exit(0)

        else:
            print(f"{RED}Invalid option. Please choose 0 to 8.{RESET}")
            time.sleep(1)


def cmd_status():
    render_dashboard_view(clear_screen=False)
    print(f" {GRAY}Tip: Type 'mem' to open the interactive control menu, or 'mem boost' for instant RAM reclaim.{RESET}\n")


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


def cmd_quiet():
    config = load_config()
    if "notifications" not in config:
        config["notifications"] = {}
    config["notifications"]["enabled"] = False
    save_config(config)
    print(f"{GREEN}{BOLD}✔ MemorySpace is now in QUIET MODE (🔕 Muted)!{RESET}")
    print(f"Background daemon will guard your applications silently with zero desktop popups.")


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

    # quiet / mute
    subparsers.add_parser("quiet", help="Mute all notifications (Quiet Mode)")

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
    elif args.command == "quiet":
        cmd_quiet()
    elif args.command == "protect":
        add_app_to_protection(args.app)
        print(f"{GREEN}✔ Successfully shielded '{args.app}'! MemorySpace will prevent it from ever being killed.{RESET}")
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
