"""
MemorySpace Desktop Notification Manager
Provides silent, non-intrusive notification controls with long cooldowns.
"""

import subprocess
import time
from typing import Dict
from ..config import load_config

_last_notification_time: Dict[str, float] = {}


def send_desktop_notification(
    title: str,
    message: str,
    urgency: str = "normal",  # low, normal, critical
    category: str = "general",
    force: bool = False,
) -> bool:
    """
    Sends a desktop notification using notify-send only if notifications are enabled.
    Defaults to quiet mode to prevent annoying users while working.
    """
    global _last_notification_time
    config = load_config()
    notif_cfg = config.get("notifications", {})

    # Check if notifications are enabled
    if not notif_cfg.get("enabled", False) and not force:
        return False

    # If critical_only, block anything not marked critical
    if notif_cfg.get("critical_only", True) and urgency != "critical" and not force:
        return False

    cooldown = notif_cfg.get("cooldown_seconds", 1800)
    now = time.time()

    if not force:
        last_time = _last_notification_time.get(category, 0.0)
        if now - last_time < cooldown:
            return False  # In cooldown

    _last_notification_time[category] = now

    icon = "dialog-information"
    if urgency == "critical":
        icon = "dialog-warning"
    elif urgency == "low":
        icon = "info"

    try:
        subprocess.run(
            [
                "notify-send",
                "-a", "MemorySpace",
                "-u", urgency,
                "-i", icon,
                title,
                message,
            ],
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception:
        return False
