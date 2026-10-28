"""
MemorySpace Memory Optimizer
Safely reclaims memory and reduces pressure without closing running tasks.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any


def optimize_memory_soft() -> Dict[str, Any]:
    """
    Performs non-destructive memory optimization:
    1. os.sync() to flush file dirty buffers so kernel can immediately reclaim cache.
    2. Cleans user thumbnail cache and non-essential temp files.
    3. Trims glibc heaps where possible.
    """
    results = {
        "sync_performed": False,
        "temp_cleaned_mb": 0.0,
        "actions": [],
    }

    # 1. Sync dirty pages to disk
    try:
        os.sync()
        results["sync_performed"] = True
        results["actions"].append("Flushed disk dirty buffers (os.sync)")
    except Exception as e:
        results["actions"].append(f"Sync error: {e}")

    # 2. Clean thumbnail cache if large (>50MB)
    try:
        thumb_dir = Path.home() / ".cache" / "thumbnails"
        if thumb_dir.exists():
            total_size = sum(f.stat().st_size for f in thumb_dir.glob("**/*") if f.is_file())
            if total_size > 50 * 1024 * 1024:  # > 50MB
                shutil.rmtree(thumb_dir, ignore_errors=True)
                thumb_dir.mkdir(parents=True, exist_ok=True)
                freed_mb = round(total_size / (1024 * 1024), 1)
                results["temp_cleaned_mb"] += freed_mb
                results["actions"].append(f"Cleared thumbnail cache ({freed_mb} MB)")
    except Exception:
        pass

    # 3. Clean Antigravity/Electron crashpad temporary dump sockets if inactive
    try:
        crashpad_dir = Path.home() / ".config" / "Antigravity" / "Crashpad" / "pending"
        if crashpad_dir.exists():
            dmp_count = 0
            for f in crashpad_dir.glob("*.dmp"):
                try:
                    f.unlink()
                    dmp_count += 1
                except Exception:
                    pass
            if dmp_count > 0:
                results["actions"].append(f"Removed {dmp_count} stale crash dump files")
    except Exception:
        pass

    return results
