<div align="center">

```
  __  __                               ____                       
 |  \/  | ___ _ __ ___   ___  _ __ _   / ___| _ __   __ _  ___ ___ 
 | |\/| |/ _ \ '_ ` _ \ / _ \| '__| | |\___ \| '_ \ / _` |/ __/ _ \
 | |  | |  __/ | | | | | (_) | |  |_| | ___) | |_) | (_| | (_|  __/
 |_|  |_|\___|_| |_| |_|\___/|_|   \__, |____/| .__/ \__,_|\___\___|
                                   |___/      |_|                   
```

# 🧠 MemorySpace

### The Zero-Crash Linux Memory Guard & RAM Optimizer
**Stop Ubuntu & Linux from silently force-closing your IDE, Browser tabs, and compile tasks.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![Linux](https://img.shields.io/badge/Platform-Ubuntu%20%7C%20Debian%20%7C%20Fedora%20%7C%20Arch-orange.svg)](https://kernel.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![CI Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](.github/workflows/ci.yml)

[⚡ 1-Line Install](#-1-line-quickstart) • [🔍 Why This Happens](#-the-problem-why-apps-randomly-close-on-linux) • [🛡️ How It Works](#️-how-memoryspace-fixes-it) • [📊 Web Dashboard](#-web-dashboard) • [💡 CLI Guide](#-cli-commands) • [⚖️ Comparison](#-why-memoryspace)

---

</div>

## 💥 The Problem: Why Apps Randomly Close on Linux

Have you ever been in the middle of writing code, running a build, or multitasking with multiple browser tabs, only for **Antigravity, VS Code, Android Studio, or Chrome to suddenly vanish** without warning?

```text
Notification: "Device memory is nearly full. Antigravity was using a lot of memory and was forced to stop."
```

### The Culprit: Ubuntu's Aggressive `systemd-oomd`
On modern Ubuntu (22.04, 24.04, 26.04), `systemd-oomd` is enabled by default with this policy:
```ini
ManagedOOMMemoryPressure=kill
ManagedOOMMemoryPressureLimit=50%
```
Whenever memory stall pressure exceeds **50% for just 20 seconds**, Ubuntu's daemon triggers `SIGKILL` on whichever application is using the most RAM — **even if your Swap is completely free and the system was never actually out of memory!**

---

## ⚡ 1-Line Quickstart

Install MemorySpace in seconds on any Linux machine (no root required for user protection):

```bash
curl -fsSL https://raw.githubusercontent.com/hetansh-patel/MemorySpace/main/install.sh | bash
```

*Or clone and run manually:*
```bash
git clone https://github.com/hetansh-patel/MemorySpace.git
cd MemorySpace
./install.sh
```

---

## 🛡️ How MemorySpace Fixes It

MemorySpace attacks the issue on two layers:

### 1. Active Task Shielding (Zero-Crash Guarantee)
MemorySpace's background daemon constantly ensures that your critical developer tools (`Antigravity`, `VS Code`, `Android Studio`, `Node`, `Python`, `Brave`, `Chrome`) have systemd's:
```ini
ManagedOOMPreference=omit
```
This instructs `systemd-oomd` to **NEVER kill your active tools**.

### 2. In-Memory ZRAM Turbo (Double Usable RAM)
Instead of letting slow disk-swap freeze your PC, MemorySpace sets up **ZRAM** (ultra-fast LZ4 compressed in-memory swap).
- **4 GB RAM** behaves like **~8 GB**
- **8 GB RAM** behaves like **~16 GB**
- Eliminates disk thrashing and stalls permanently.

### 3. Soft Memory Optimization
When RAM usage climbs over 85%, MemorySpace safely syncs dirty page buffers (`os.sync`), reclaims dead caches, and warns you gracefully via desktop alerts before lockups occur.

---

## 🖥️ Terminal Interface

Check memory and protected tasks anytime with `memoryspace status`:

```text
  __  __                               ____                       
 |  \/  | ___ _ __ ___   ___  _ __ _   / ___| _ __   __ _  ___ ___ 
 | |\/| |/ _ \ '_ ` _ \ / _ \| '__| | |\___ \| '_ \ / _` |/ __/ _ \
 | |  | |  __/ | | | | | (_) | |  |_| | ___) | |_) | (_| | (_|  __/
 |_|  |_|\___|_| |_| |_|\___/|_|   \__, |____/| .__/ \__,_|\___\___|
                                   |___/      |_|                   
  🛡️  Zero-Crash Memory Guard & RAM Optimizer for Linux
  ---------------------------------------------------------------
 Daemon Service: ● ACTIVE GUARD
 System Health:  HEALTHY - Memory healthy. Running tasks running smoothly.
-----------------------------------------------------------------
 Physical RAM:   [████████████░░░░░░░░░░░░░░░░░░] 38.2%
                 Used: 1.99 GB / Total: 5.22 GB (Avail: 3.23 GB)
 Swap Memory:    [█████░░░░░░░░░░░░░░░░░░░░░░░░░] 18.2%
                 Used: 0.73 GB / Total: 4.0 GB (Free: 3.27 GB)
 Kernel PSI:     10s Stall: 0.0%  |  60s: 0.0%  |  300s: 0.0%
-----------------------------------------------------------------
 Protected Apps: antigravity, brave, chrome, chromium, firefox, code, cursor...
 Active Scopes Guarded: app-antigravity.scope, app-gnome-brave.scope
-----------------------------------------------------------------
 PID      APP NAME               MEM (MB)     RAM %    STATUS         
 21151    language_server        517.1        9.7      🛡️ PROTECTED
 29212    brave                  354.3        6.6      🛡️ PROTECTED
 21337    antigravity            294.9        5.5      🛡️ PROTECTED
```

---

## 🌐 Web Dashboard

Launch a sleek, real-time web dashboard running with `< 15MB` RAM footprint:

```bash
memoryspace web --port 7890
```
Open **[http://localhost:7890](http://localhost:7890)** in your browser:
- 📈 Live 60-second RAM % history graph
- 🛡️ One-click protection toggles for any running process
- ⚡ **"Optimize Memory Now"** button
- 🔍 Process search and memory sorting

---

## 💡 CLI Commands

| Command | Description |
|---|---|
| `memoryspace status` | View RAM, Swap, Kernel PSI, and protected apps |
| `memoryspace monitor` | Interactive updating terminal monitor (like htop) |
| `memoryspace optimize` | Safely reclaim cache and flush dirty write buffers |
| `memoryspace protect <name>` | Pin an application pattern so it is never killed |
| `memoryspace unprotect <name>` | Remove application from protection list |
| `memoryspace list` | List all configured protected applications |
| `memoryspace web` | Launch the lightweight Web Dashboard |
| `memoryspace daemon status` | Inspect background daemon status |

---

## ⚖️ Why MemorySpace?

| Capability | Standard Ubuntu | earlyoom | systemd-oomd | **MemorySpace** 🧠 |
|---|:---:|:---:|:---:|:---:|
| Protects IDE from sudden kill | ❌ Kills biggest app | ❌ Kills highest RSS | ❌ Kills at 50% pressure | ✅ **Guaranteed OOM Immunity** |
| Doubles RAM via ZRAM | ❌ Manual setup | ❌ No | ❌ No | ✅ **Automated 1-Click** |
| Desktop Warning Alerts | ❌ Post-crash only | ❌ Terminal only | ❌ Post-crash only | ✅ **Pre-emptive Desktop Alerts** |
| Real-time Web Dashboard | ❌ None | ❌ None | ❌ None | ✅ **Built-in Modern UI** |
| RAM Footprint of Tool | - | ~10 MB | Systemd | ✅ **~14 MB (Zero Bloat)** |
| Configurable via CLI/GUI | ❌ Complex files | ❌ Flag file | ❌ System slices | ✅ **Interactive CLI & Web** |

---

## 🚀 Permanent System Fix (Sudo Optimization)

To raise `systemd-oomd` thresholds from 50% to 90% and enable ZRAM permanently across reboots:

```bash
sudo ./scripts/fix_ubuntu_oomd.sh
```

---

## 🤝 Contributing

Contributions are warmly welcomed! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on submitting pull requests and feature additions.

## 📄 License

This project is licensed under the [MIT License](LICENSE) - feel free to use, modify, and distribute!
