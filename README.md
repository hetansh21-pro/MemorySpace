# 🧠 MemorySpace

> **Intelligent RAM Optimizer & Running Task Protector for Linux/Ubuntu**  
> Never let Ubuntu's OOM Killer or `systemd-oomd` abruptly force-stop your IDE (Antigravity, VS Code), Web Browsers, or build tasks again.

---

## 🔍 The Root Cause: Why Did Antigravity & Apps Force Stop?

### 1. Ubuntu's Aggressive `systemd-oomd` Policy
On Ubuntu, `systemd-oomd` runs by default with an aggressive configuration:
```ini
# /usr/lib/systemd/system/user@.service.d/10-oomd-user-service-defaults.conf
[Service]
ManagedOOMMemoryPressure=kill
ManagedOOMMemoryPressureLimit=50%
```
Whenever memory pressure exceeds **50% for 20 seconds** (even when swap is still empty and system has plenty of free swap space), `systemd-oomd` sends a `SIGKILL` to whichever application is using the most memory.

In system logs, this appears as:
```text
Killed .../app-antigravity-7825.scope due to memory pressure being 57.22% > 50.00% for > 20s
Killed .../app-gnome-brave-browser-6289.scope due to memory pressure being 71.32% > 50.00%
```
Followed by the notification:
> *"Device memory is nearly full. Antigravity was using a lot of memory and was forced to stop."*

### 2. Physical RAM Limitations
With ~5.2 GB of physical RAM, running GNOME Shell (1.5 GB) + Antigravity IDE (2-3 GB) + Browser tabs (1 GB) quickly pushes pressure above the 50% mark during code compilation, indexing, or browsing.

---

## 🛡️ How MemorySpace Solves This Problem

MemorySpace operates on two powerful levels:

### Level 1: Automatic User-level Task Shield (Active Now!)
* **OOM Immunity Shield**: Sets `ManagedOOMPreference=omit` on Antigravity and user workflows so `systemd-oomd` will **never** select them for killing.
* **Intelligent Daemon (`memoryspace.service`)**: Runs in the background (using only ~14 MB RAM). It monitors RAM & Kernel PSI pressure every 3 seconds.
* **Proactive Memory Optimization**: Flushes dirty page buffers (`os.sync`) and cleans stale caches non-destructively before pressure causes slowdowns.
* **Gentle Desktop Notifications**: Alerts you via desktop notifications before memory runs out.

### Level 2: 1-Click System Permanent Fix (ZRAM + OOM Tamer)
Run the included root optimization script to effectively double your usable RAM and prevent kernel stalls:
```bash
cd /home/hetansh-patel/Projects/MemorySpace
sudo ./scripts/fix_ubuntu_oomd.sh
```
What this script does:
1. **Raises `systemd-oomd` limit from 50% to 90%** so it stops killing development tools.
2. **Installs ZRAM**: In-memory compressed RAM swap using fast LZ4 compression. Effectively expands 5.2GB RAM to ~9-10GB without disk thrashing.
3. **Tunes Linux VM**: Optimizes swappiness and cache retention.

---

## 🚀 Quick Usage Guide

MemorySpace is installed globally at `~/.local/bin/memoryspace`. You can run it from any terminal:

### 1. View System Status
```bash
memoryspace status
```
Displays physical RAM, Swap, Kernel PSI Pressure stall meters, and protected running applications.

### 2. Live Terminal Monitor
```bash
memoryspace monitor
```
Real-time updating dashboard directly in your terminal.

### 3. Immediate Memory Cleanup
```bash
memoryspace optimize
```
Safely reclaims cache, cleans stale crash logs, and syncs dirty write buffers.

### 4. Protect Custom Apps
```bash
# Pin any application or build tool so it is never killed
memoryspace protect android-studio
memoryspace protect node
memoryspace protect cargo

# List all protected apps
memoryspace list
```

### 5. Launch Modern Web Dashboard
```bash
memoryspace web --port 7890
```
Open [http://localhost:7890](http://localhost:7890) in your browser for a graphical dashboard with live memory gauges, protected app management, and 1-click optimization.

### 6. Control Background Daemon
```bash
memoryspace daemon status
memoryspace daemon restart
systemctl --user status memoryspace.service
```

---

## 📁 Project Architecture

```text
MemorySpace/
├── bin/
│   └── memoryspace         # Main CLI executable
├── config/
│   └── memoryspace.json    # Thresholds & protected application list
├── scripts/
│   ├── fix_ubuntu_oomd.sh  # Sudo script: Tames systemd-oomd & installs ZRAM
│   └── install_service.sh  # Installs background user systemd service
├── src/
│   ├── cli.py              # Terminal user interface
│   ├── daemon.py           # Background monitoring & protection loop
│   ├── core/
│   │   ├── monitor.py      # Kernel PSI & memory metrics
│   │   ├── protector.py    # systemd scope shield (ManagedOOMPreference=omit)
│   │   ├── optimizer.py    # Non-destructive memory trimmer
│   │   └── notifier.py     # Desktop alert manager
│   └── web/
│       ├── server.py       # Zero-dependency HTTP server & REST API
│       └── static/         # HTML/CSS/JS Web Dashboard
└── README.md
```
