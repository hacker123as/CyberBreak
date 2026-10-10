#!/usr/bin/env bash
# ==============================================================================
# CyberBreak - Hardened Linux System-Wide Installer
# Target: Kicksecure / Debian / Ubuntu / Arch
# Supports: All user accounts & non-root desktops with Polkit privilege elevation
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
cat << "EOF"
   ______      __               ____                 __  
  / ____/_  __/ /_  ___  _____ / __ )________  ____ _/ /__
 / /   / / / / __ \/ _ \/ ___// __  / ___/ _ \/ __ `/ //_/
/ /___/ /_/ / /_/ /  __/ /   / /_/ / /  /  __/ /_/ / ,<   
\____/\__, /_.___/\___/_/   /_____/_/   \___/\__,_/_/|_|  
     /____/                                               
       HARDENED SECURITY & ANTI-FORENSICS FORTRESS
EOF
echo -e "${NC}"

# Detect execution privileges
IS_ROOT=false
if [ "$(id -u)" -eq 0 ]; then
    IS_ROOT=true
fi

SUDO_CMD=""
if [ "$IS_ROOT" = false ]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO_CMD="sudo"
        echo -e "${YELLOW}[!] Running with user privileges. Elevating with sudo...${NC}"
    else
        echo -e "${RED}[ERROR] Root privileges or sudo required for installation.${NC}"
        exit 1
    fi
fi

# Detect calling user and desktop path
CALLING_USER="${SUDO_USER:-$(whoami)}"
USER_HOME=$(getent passwd "$CALLING_USER" | cut -d: -f6)

echo -e "${CYAN}[*] Target user: ${BOLD}${CALLING_USER}${NC} (${USER_HOME})"
echo -e "${CYAN}[*] Updating package repositories and installing dependencies...${NC}"

# Debian / Kicksecure / Ubuntu package installation
if command -v apt-get >/dev/null 2>&1; then
    $SUDO_CMD apt-get update -y
    $SUDO_CMD apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-pyqt6 \
        python3-requests \
        python3-stem \
        macchanger \
        rfkill \
        iptables \
        network-manager \
        ethtool \
        cryptsetup \
        curl \
        git \
        pkexec \
        policykit-1 || true
elif command -v pacman >/dev/null 2>&1; then
    $SUDO_CMD pacman -Sy --noconfirm \
        python \
        python-pip \
        python-pyqt6 \
        python-requests \
        macchanger \
        rfkill \
        iptables \
        networkmanager \
        ethtool \
        cryptsetup \
        curl \
        git \
        polkit || true
fi

# Target application directories
APP_DIR="/opt/cyberbreak"
echo -e "${CYAN}[*] Installing CyberBreak into ${APP_DIR}...${NC}"

$SUDO_CMD mkdir -p "$APP_DIR"

# If current directory contains cyberbreak package, copy from here; otherwise clone
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${PARENT_DIR}/cyberbreak/main.py" ]; then
    echo -e "${CYAN}[*] Deploying from local source tree...${NC}"
    $SUDO_CMD cp -r "${PARENT_DIR}"/* "$APP_DIR/"
else
    echo -e "${CYAN}[*] Cloning latest source from GitHub...${NC}"
    if [ -d "${APP_DIR}/.git" ]; then
        $SUDO_CMD git -C "$APP_DIR" pull origin main
    else
        $SUDO_CMD rm -rf "$APP_DIR"
        $SUDO_CMD git clone https://github.com/hacker123as/CyberBreak.git "$APP_DIR"
    fi
fi

# Ensure all users can read and execute the app bundle
$SUDO_CMD chmod -R 755 "$APP_DIR"

# Install python requirements fallback via pip if packages were missing from apt
if [ -f "${APP_DIR}/requirements.txt" ]; then
    echo -e "${CYAN}[*] Verifying Python library dependencies...${NC}"
    python3 -m pip install -r "${APP_DIR}/requirements.txt" --break-system-packages 2>/dev/null || \
    python3 -m pip install -r "${APP_DIR}/requirements.txt" 2>/dev/null || true
fi

# Create system launcher binary wrapper in /usr/local/bin
echo -e "${CYAN}[*] Creating global /usr/local/bin/cyberbreak binary...${NC}"
$SUDO_CMD tee /usr/local/bin/cyberbreak > /dev/null << 'EOF'
#!/usr/bin/env bash
# CyberBreak Unified Launcher Wrapper
export PYTHONPATH="/opt/cyberbreak:$PYTHONPATH"

# If running as root, directly run
if [ "$(id -u)" -eq 0 ]; then
    exec /usr/bin/python3 -m cyberbreak.main "$@"
fi

# If inside X11/Wayland desktop and not root, use pkexec for seamless graphical privilege elevation
if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
    if command -v pkexec >/dev/null 2>&1; then
        exec pkexec env DISPLAY="$DISPLAY" XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}" WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" PYTHONPATH="/opt/cyberbreak" /usr/bin/python3 -m cyberbreak.main "$@"
    fi
fi

# Fallback: run directly as current user (internal operations will request sudo/polkit when needed)
exec /usr/bin/python3 -m cyberbreak.main "$@"
EOF

$SUDO_CMD chmod 755 /usr/local/bin/cyberbreak

# Install Icon Assets
echo -e "${CYAN}[*] Installing vector & raster application icons...${NC}"
$SUDO_CMD mkdir -p /usr/share/icons/hicolor/scalable/apps
$SUDO_CMD mkdir -p /usr/share/icons/hicolor/256x256/apps
if [ -f "${APP_DIR}/cyberbreak/assets/cyberbreak.svg" ]; then
    $SUDO_CMD cp "${APP_DIR}/cyberbreak/assets/cyberbreak.svg" /usr/share/icons/hicolor/scalable/apps/cyberbreak.svg
    $SUDO_CMD cp "${APP_DIR}/cyberbreak/assets/cyberbreak.svg" /usr/share/icons/hicolor/256x256/apps/cyberbreak.svg
fi

# Update desktop icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    $SUDO_CMD gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi

# Install FreeDesktop .desktop entry for ALL users
echo -e "${CYAN}[*] Installing /usr/share/applications/cyberbreak.desktop for all users...${NC}"
$SUDO_CMD tee /usr/share/applications/cyberbreak.desktop > /dev/null << 'EOF'
[Desktop Entry]
Name=CyberBreak
GenericName=Security & Anti-Forensics Fortress
Comment=Hardened Privacy, Leak Detection, Hardware Spoofing & Panic Isolation
Exec=/usr/local/bin/cyberbreak
Icon=cyberbreak
Terminal=false
Type=Application
Categories=System;Security;Network;Settings;Qt;
StartupNotify=true
Keywords=security;privacy;spoofer;killswitch;tor;leak;firewall;kicksecure;
X-Kicksecure-Security-Level=Hardened
EOF
$SUDO_CMD chmod 644 /usr/share/applications/cyberbreak.desktop

if command -v update-desktop-database >/dev/null 2>&1; then
    $SUDO_CMD update-desktop-database 2>/dev/null || true
fi

# Install Desktop Shortcut for calling user
USER_DESKTOP="${USER_HOME}/Desktop"
if [ -d "$USER_DESKTOP" ]; then
    echo -e "${CYAN}[*] Placing CyberBreak shortcut on ${USER_DESKTOP}...${NC}"
    cp /usr/share/applications/cyberbreak.desktop "${USER_DESKTOP}/cyberbreak.desktop"
    chmod +x "${USER_DESKTOP}/cyberbreak.desktop"
    # Mark trusted in GNOME/XFCE if gio exists
    if command -v gio >/dev/null 2>&1; then
        gio set "${USER_DESKTOP}/cyberbreak.desktop" metadata::trusted true 2>/dev/null || true
    fi
    chown "$CALLING_USER":"$CALLING_USER" "${USER_DESKTOP}/cyberbreak.desktop" 2>/dev/null || true
fi

# Also place in /etc/skel/Desktop for any future new accounts created on the machine
$SUDO_CMD mkdir -p /etc/skel/Desktop
$SUDO_CMD cp /usr/share/applications/cyberbreak.desktop /etc/skel/Desktop/cyberbreak.desktop
$SUDO_CMD chmod 755 /etc/skel/Desktop/cyberbreak.desktop

# Install Polkit Policy
echo -e "${CYAN}[*] Registering Polkit privilege policy...${NC}"
$SUDO_CMD mkdir -p /usr/share/polkit-1/actions
if [ -f "${APP_DIR}/polkit/org.cyberbreak.security.policy" ]; then
    $SUDO_CMD cp "${APP_DIR}/polkit/org.cyberbreak.security.policy" /usr/share/polkit-1/actions/
fi

echo -e "\n${GREEN}${BOLD}[SUCCESS] CyberBreak has been installed successfully!${NC}"
echo -e "${CYAN}------------------------------------------------------------${NC}"
echo -e "  * Available in ${BOLD}Application Grid / Whisker Menu${NC} for all users"
echo -e "  * Desktop icon created on ${BOLD}${USER_DESKTOP}/cyberbreak.desktop${NC}"
echo -e "  * Launch from terminal: run ${BOLD}cyberbreak${NC}"
echo -e "${CYAN}------------------------------------------------------------${NC}\n"
