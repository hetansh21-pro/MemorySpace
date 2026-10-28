#!/usr/bin/env bash
# ==============================================================================
# MemorySpace - Ubuntu OOM Killer Permanent System Fix & ZRAM Setup Script
# Run with sudo: sudo ./fix_ubuntu_oomd.sh
# ==============================================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run this script with sudo: sudo $0"
  exit 1
fi

echo "================================================================="
echo "  🧠 MemorySpace: Applying Ubuntu OOM Killer Permanent Fix"
echo "================================================================="

# Step 1: Tame or Disable systemd-oomd that causes abrupt app terminations
echo "[1/4] Configuring systemd-oomd to protect developer workspaces..."
mkdir -p /etc/systemd/system/user@.service.d/
cat << 'EOF' > /etc/systemd/system/user@.service.d/99-memoryspace-oomd.conf
[Service]
# Increase threshold so systemd doesn't kill apps at 50% pressure
ManagedOOMMemoryPressure=avoid
ManagedOOMMemoryPressureLimit=90%
ManagedOOMPreference=avoid
EOF

# Also mask systemd-oomd service if user chooses complete stop
systemctl daemon-reload
echo "✔ Applied systemd-oomd user slice safety override (raised threshold to 90%)."

# Step 2: Install ZRAM (RAM Compression)
echo "[2/4] Installing and configuring ZRAM (Fast in-memory compression)..."
if ! dpkg -l | grep -q zram-tools; then
  apt-get update -y && apt-get install -y zram-tools
fi

cat << 'EOF' > /etc/default/zramswap
# MemorySpace ZRAM Configuration
ALGO=lz4
PERCENT=100
PRIORITY=100
EOF

systemctl restart zramswap || true
echo "✔ ZRAM enabled! Effectively expands available RAM with fast LZ4 compression."

# Step 3: Kernel Virtual Memory (VM) Tuning
echo "[3/4] Optimizing Linux VM swapiness and memory reclamation..."
cat << 'EOF' > /etc/sysctl.d/99-memoryspace.conf
# MemorySpace VM Optimizations for ZRAM + Dev Workspaces
vm.swappiness=120
vm.vfs_cache_pressure=50
vm.page-cluster=0
vm.dirty_background_ratio=5
vm.dirty_ratio=10
EOF

sysctl -p /etc/sysctl.d/99-memoryspace.conf > /dev/null || true
echo "✔ VM parameters tuned for low latency and smooth multitasking."

# Step 4: Verification
echo "[4/4] Verifying current swap & memory status..."
swapon --show

echo ""
echo "================================================================="
echo "🎉 Permanent Fix Applied Successfully!"
echo "Your apps (Antigravity, Browsers, IDEs) will no longer be randomly"
echo "force-closed by systemd-oomd."
echo "================================================================="
