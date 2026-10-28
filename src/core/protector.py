"""
MemorySpace Process & Scope Protector
Protects running user applications and scopes from systemd-oomd and kernel kills.
"""

import subprocess
import re
from typing import Dict, List, Set
from ..config import load_config, save_config, is_protected

_already_protected_units: Set[str] = set()


def get_active_user_scopes() -> List[str]:
    """
    Returns list of currently active user scopes.
    """
    try:
        res = subprocess.run(
            ["systemctl", "--user", "list-units", "--type=scope", "--state=running", "--no-legend"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        scopes = []
        for line in res.stdout.strip().splitlines():
            parts = line.strip().split()
            if parts:
                unit = parts[0]
                if unit.endswith(".scope"):
                    scopes.append(unit)
        return scopes
    except Exception:
        return []


def protect_scope(unit_name: str) -> bool:
    """
    Tells systemd-oomd to NEVER kill this unit:
    sets ManagedOOMPreference=omit
    """
    try:
        res = subprocess.run(
            ["systemctl", "--user", "set-property", unit_name, "ManagedOOMPreference=omit"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return res.returncode == 0
    except Exception:
        return False


def get_scope_oom_preference(unit_name: str) -> str:
    """
    Queries ManagedOOMPreference for a given unit.
    """
    try:
        res = subprocess.run(
            ["systemctl", "--user", "show", unit_name, "-p", "ManagedOOMPreference"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in res.stdout.strip().splitlines():
            if line.startswith("ManagedOOMPreference="):
                return line.split("=", 1)[1].strip()
        return "none"
    except Exception:
        return "unknown"


def protect_all_configured_apps() -> Dict[str, any]:
    """
    Scans active scopes and applies ManagedOOMPreference=omit to all matching protected patterns.
    """
    global _already_protected_units
    config = load_config()
    protected_apps = config.get("protected_apps", [])
    active_scopes = get_active_user_scopes()

    newly_protected = []
    currently_protected = []

    for scope in active_scopes:
        clean_name = re.sub(r"\\x2d", "-", scope).lower()
        if is_protected(clean_name, protected_apps):
            pref = get_scope_oom_preference(scope)
            if pref != "omit":
                if protect_scope(scope):
                    newly_protected.append(scope)
                    _already_protected_units.add(scope)
            else:
                currently_protected.append(scope)
                _already_protected_units.add(scope)

    return {
        "newly_protected": newly_protected,
        "currently_protected": currently_protected,
        "total_active_scopes": len(active_scopes),
    }


def add_app_to_protection(app_name: str) -> bool:
    """
    Adds an app name pattern to the persistent protected apps list and protects active instances.
    """
    config = load_config()
    apps = config.get("protected_apps", [])
    app_lower = app_name.strip().lower()
    if app_lower not in [a.lower() for a in apps]:
        apps.append(app_lower)
        config["protected_apps"] = apps
        save_config(config)
    protect_all_configured_apps()
    return True


def remove_app_from_protection(app_name: str) -> bool:
    """
    Removes an app from the protected apps list.
    """
    config = load_config()
    apps = config.get("protected_apps", [])
    app_lower = app_name.strip().lower()
    updated = [a for a in apps if a.lower() != app_lower]
    config["protected_apps"] = updated
    save_config(config)
    return True
