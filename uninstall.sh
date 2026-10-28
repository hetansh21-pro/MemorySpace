#!/usr/bin/env bash
# ==============================================================================
#  🧠 MemorySpace Clean Uninstaller
# ==============================================================================

set -e

echo "Uninstalling MemorySpace..."

# 1. Stop and disable systemd service
if systemctl --user is-active --quiet memoryspace.service 2>/dev/null; then
  echo "Stopping user service..."
  systemctl --user stop memoryspace.service || true
fi
systemctl --user disable memoryspace.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/memoryspace.service"
rm -f "$HOME/.config/systemd/user/default.target.wants/memoryspace.service"
systemctl --user daemon-reload 2>/dev/null || true

# 2. Remove symlinks
rm -f "$HOME/.local/bin/memoryspace"
rm -f "$HOME/.local/bin/mem"
rm -f "$HOME/.local/bin/msp"

# 3. Remove state
rm -rf "$HOME/.local/state/memoryspace"

# 4. Remove installation directory if installed in ~/.local/share/memoryspace
if [ -d "$HOME/.local/share/memoryspace" ]; then
  rm -rf "$HOME/.local/share/memoryspace"
fi

echo "✔ MemorySpace uninstalled cleanly. (Your system packages and kernel configs remain intact)."
