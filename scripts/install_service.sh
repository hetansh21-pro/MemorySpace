#!/usr/bin/env bash
set -e

SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/memoryspace.service"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$(which python3)"

mkdir -p "$SERVICE_DIR"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=MemorySpace - Intelligent Memory & Task Guard Daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=$PYTHON_BIN $PROJECT_DIR/bin/memoryspace daemon-run
Restart=on-failure
RestartSec=5
ManagedOOMPreference=omit

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable memoryspace.service
systemctl --user restart memoryspace.service

echo "✔ MemorySpace systemd user service installed and started successfully!"
echo "Check status anytime with: systemctl --user status memoryspace.service"
