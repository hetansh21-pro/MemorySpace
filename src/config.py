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
    "version": "1.0.0",
    "check_interval_seconds": 3,
    "notification_cooldown_seconds": 90,
    "thresholds": {
        "warning_percent": 80.0,
        "optimize_percent": 88.0,
        "critical_percent": 94.0,
        "psi_pressure_threshold": 35.0,
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
