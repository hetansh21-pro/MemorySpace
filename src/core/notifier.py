"""
MemorySpace Desktop Notification Manager
Sends non-intrusive notifications with cooldowns.
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
    Sends a desktop notification using notify-send with cooldown protection.
    """
    global _last_notification_time
    config = load_config()
    cooldown = config.get("notification_cooldown_seconds", 90)
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
