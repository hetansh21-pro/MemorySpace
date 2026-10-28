"""
MemorySpace Configuration Loader and Defaults
"""

import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "memoryspace.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "system_name": "MemorySpace",
    "version": "1.0.1",
    "check_interval_seconds": 3,
    "notifications": {
        "enabled": False,  # Quiet mode by default - no annoying popups!
        "critical_only": True,
        "cooldown_seconds": 1800,  # 30 minutes cooldown
    },
    "thresholds": {
        "warning_percent": 85.0,
        "optimize_percent": 90.0,
        "critical_percent": 95.0,
        "psi_pressure_threshold": 45.0,
    },
    "protected_apps": [
        "antigravity",
        "brave",
        "chrome",
        "chromium",
        "firefox",
        "code",
        "cursor",
        "studio.sh",
        "android-studio",
        "java",
        "gradle",
        "node",
        "python3",
        "bash",
        "zsh",
        "ptyxis",
        "gnome-terminal",
        "alacritty",
    ],
    "web": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 7890,
    },
}


def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                # Ensure nested dicts are merged
                if "notifications" in data:
                    notif_cfg = DEFAULT_CONFIG["notifications"].copy()
                    notif_cfg.update(data["notifications"])
                    config["notifications"] = notif_cfg
                return config
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def is_protected(name_or_cmd: str, protected_list: List[str]) -> bool:
    target = name_or_cmd.lower()
    for item in protected_list:
        if item.lower() in target:
            return True
    return False
