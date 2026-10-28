#!/usr/bin/env bash
# ==============================================================================
#  🧠 MemorySpace Universal 1-Line Installer
#  Usage: curl -fsSL https://raw.githubusercontent.com/hetansh-patel/MemorySpace/main/install.sh | bash
# ==============================================================================

set -e

# Colors
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_GREEN="\033[32m"
C_CYAN="\033[36m"
C_YELLOW="\033[33m"
C_RED="\033[31m"
C_PURPLE="\033[35m"

print_banner() {
  echo -e "${C_CYAN}${C_BOLD}"
  echo "  __  __                               ____                       "
  echo " |  \/  | ___ _ __ ___   ___  _ __ _   / ___| _ __   __ _  ___ ___ "
  echo " | |\/| |/ _ \ '_ \` _ \ / _ \| '__| | |\___ \| '_ \ / _\` |/ __/ _ \\"
  echo " | |  | |  __/ | | | | | (_) | |  |_| | ___) | |_) | (_| | (_|  __/"
  echo " |_|  |_|\___|_| |_| |_|\___/|_|   \__, |____/| .__/ \__,_|\___\___|"
  echo "                                   |___/      |_|                   "
  echo -e "${C_RESET}"
  echo -e "${C_BOLD}  🛡️  Zero-Crash Memory Guard & RAM Optimizer for Linux${C_RESET}"
  echo -e "  ---------------------------------------------------------------"
}

print_banner

# Step 1: OS Check
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
  echo -e "${C_RED}❌ Error: MemorySpace is designed specifically for Linux (Ubuntu, Debian, Fedora, Arch).${C_RESET}"
  exit 1
fi

echo -e "\n${C_CYAN}[1/5] Checking system dependencies...${C_RESET}"

# Python check
if ! command -v python3 &> /dev/null; then
  echo -e "${C_RED}❌ python3 is required. Please install python3 and rerun.${C_RESET}"
  exit 1
fi

# psutil check / install
if ! python3 -c "import psutil" 2>/dev/null; then
  echo -e "${C_YELLOW}⚠ psutil not detected. Installing psutil via pip...${C_RESET}"
  python3 -m pip install psutil --quiet 2>/dev/null || {
    echo -e "${C_YELLOW}Trying apt-get for python3-psutil...${C_RESET}"
    sudo apt-get install -y python3-psutil 2>/dev/null || true
  }
fi
echo -e "${C_GREEN}✔ Dependencies verified!${C_RESET}"

# Step 2: Determine installation source directory
INSTALL_DIR="$HOME/.local/share/memoryspace"
CURRENT_DIR="$(pwd)"

if [ -f "$CURRENT_DIR/bin/memoryspace" ] && [ -f "$CURRENT_DIR/pyproject.toml" ]; then
  # Running from within cloned repo
  SOURCE_DIR="$CURRENT_DIR"
  echo -e "\n${C_CYAN}[2/5] Installing from current directory: ${SOURCE_DIR}${C_RESET}"
else
  # Running via curl / remote
  echo -e "\n${C_CYAN}[2/5] Downloading latest MemorySpace from GitHub...${C_RESET}"
  mkdir -p "$INSTALL_DIR"
  if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Updating existing installation..."
    git -C "$INSTALL_DIR" pull --quiet
  else
    git clone --depth 1 https://github.com/hetansh-patel/MemorySpace.git "$INSTALL_DIR" --quiet
  fi
  SOURCE_DIR="$INSTALL_DIR"
fi

# Step 3: Global Symlink Setup
echo -e "\n${C_CYAN}[3/5] Setting up global CLI binary...${C_RESET}"
mkdir -p "$HOME/.local/bin"
chmod +x "$SOURCE_DIR/bin/memoryspace"
ln -sf "$SOURCE_DIR/bin/memoryspace" "$HOME/.local/bin/memoryspace"

# Ensure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  SHELL_RC=""
  if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
  elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
  fi
  if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    echo -e "${C_YELLOW}Added ~/.local/bin to PATH in $SHELL_RC${C_RESET}"
  fi
fi
echo -e "${C_GREEN}✔ Global binary ready at ~/.local/bin/memoryspace!${C_RESET}"

# Step 4: Background Service Setup
echo -e "\n${C_CYAN}[4/5] Activating background Memory Guard service...${C_RESET}"
chmod +x "$SOURCE_DIR/scripts/install_service.sh"
"$SOURCE_DIR/scripts/install_service.sh" > /dev/null

echo -e "${C_GREEN}✔ MemorySpace daemon is active and shielding your running apps!${C_RESET}"

# Step 5: Optional Permanent Fix (ZRAM + OOM Taming)
echo -e "\n${C_CYAN}[5/5] Optional Permanent System Boost:${C_RESET}"
echo -e "Would you like to tame Ubuntu's 50% OOM Killer and enable ZRAM (Double RAM)?"
echo -e "${C_YELLOW}(Requires sudo password)${C_RESET}"
read -r -p "Apply permanent system optimization now? [y/N]: " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
  sudo "$SOURCE_DIR/scripts/fix_ubuntu_oomd.sh"
else
  echo -e "${C_YELLOW}Skipped. You can run it anytime later via:${C_RESET}"
  echo -e "  sudo $SOURCE_DIR/scripts/fix_ubuntu_oomd.sh"
fi

# Final Welcome
echo -e "\n${C_GREEN}${C_BOLD}🎉 MemorySpace installed successfully!${C_RESET}"
echo -e "\nTry these commands now:"
echo -e "  ${C_BOLD}memoryspace status${C_RESET}     → View RAM, Swap, PSI pressure & protected apps"
echo -e "  ${C_BOLD}memoryspace monitor${C_RESET}    → Real-time visual terminal dashboard"
echo -e "  ${C_BOLD}memoryspace optimize${C_RESET}   → 1-click safe memory cleanup"
echo -e "  ${C_BOLD}memoryspace web${C_RESET}        → Launch Web UI at http://localhost:7890"
echo -e "  ${C_BOLD}memoryspace protect <app>${C_RESET} → Never allow <app> to be killed"
echo -e "\nStar us on GitHub: ${C_PURPLE}https://github.com/hetansh-patel/MemorySpace${C_RESET}\n"
