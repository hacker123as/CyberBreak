#!/usr/bin/env bash

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
        echo -e "On Kicksecure, please run installation from your 'sysmaint' account: sudo bash scripts/install.sh"
        exit 1
    fi
fi

echo -e "${CYAN}[*] Updating package repositories and installing dependencies...${NC}"

if command -v apt-get >/dev/null 2>&1; then
    $SUDO_CMD apt-get update -y
    $SUDO_CMD apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-pyqt6 \
        python3-pyqt6.qtsvg \
        python3-pyqt6.qtwebengine \
        libqt6svg6 \
        python3-requests \
        python3-stem \
        macchanger \
        rfkill \
        iptables \
        network-manager \
        ethtool \
        cryptsetup \
        dosfstools \
        e2fsprogs \
        tar \
        zstd \
        fdisk \
        util-linux \
        btrfs-progs \
        curl \
        git \
        pkexec \
        policykit-1 || true
elif command -v pacman >/dev/null 2>&1; then
    $SUDO_CMD pacman -Sy --noconfirm \
        python \
        python-pip \
        python-pyqt6 \
        python-pyqt6-webengine \
        qt6-svg \
        python-requests \
        macchanger \
        rfkill \
        iptables \
        networkmanager \
        ethtool \
        cryptsetup \
        dosfstools \
        e2fsprogs \
        tar \
        zstd \
        btrfs-progs \
        curl \
        git \
        polkit || true
elif command -v dnf >/dev/null 2>&1; then
    $SUDO_CMD dnf install -y \
        python3 \
        python3-pip \
        python3-pyqt6 \
        python3-pyqt6-webengine \
        qt6-qtsvg \
        python3-requests \
        python3-stem \
        macchanger \
        rfkill \
        iptables \
        NetworkManager \
        ethtool \
        cryptsetup \
        dosfstools \
        e2fsprogs \
        tar \
        zstd \
        btrfs-progs \
        curl \
        git \
        polkit || true
fi

APP_DIR="/opt/cyberbreak"
HELPER_DIR="/usr/local/lib/cyberbreak"
LIBEXEC_DIR="/usr/libexec/cyberbreak"

echo -e "${CYAN}[*] Deploying application files into ${APP_DIR}...${NC}"
$SUDO_CMD mkdir -p "$APP_DIR" "$HELPER_DIR" "$LIBEXEC_DIR"

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

echo -e "${CYAN}[*] Enforcing secure Kicksecure ownership and file permissions...${NC}"
$SUDO_CMD chown -R root:root "$APP_DIR"
$SUDO_CMD find "$APP_DIR" -type d -exec chmod 755 {} +
$SUDO_CMD find "$APP_DIR" -type f -exec chmod 644 {} +
$SUDO_CMD chmod 755 "$APP_DIR/cyberbreak/core/helper.py" 2>/dev/null || true
$SUDO_CMD chmod 755 "$APP_DIR/cyberbreak/main.py" 2>/dev/null || true
$SUDO_CMD chmod 755 "$APP_DIR/scripts"/*.sh 2>/dev/null || true

if [ -f "${APP_DIR}/requirements.txt" ]; then
    echo -e "${CYAN}[*] Checking Python dependencies...${NC}"
    python3 -m pip install -r "${APP_DIR}/requirements.txt" --break-system-packages 2>/dev/null || \
    python3 -m pip install -r "${APP_DIR}/requirements.txt" 2>/dev/null || true
fi

echo -e "${CYAN}[*] Verifying critical GUI modules (PyQt6, QtSvg, QtWebEngine)...${NC}"
if ! python3 -c "import PyQt6; from PyQt6.QtSvg import QSvgRenderer" >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] PyQt6-QtSvg module missing; installing via pip...${NC}"
    python3 -m pip install PyQt6-QtSvg --break-system-packages 2>/dev/null || \
    python3 -m pip install PyQt6-QtSvg 2>/dev/null || true
fi
if ! python3 -c "from PyQt6.QtWebEngineWidgets import QWebEngineView" >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] PyQt6-WebEngine module missing; installing via pip...${NC}"
    python3 -m pip install PyQt6-WebEngine --break-system-packages 2>/dev/null || \
    python3 -m pip install PyQt6-WebEngine 2>/dev/null || true
fi
if ! python3 -c "import requests, stem" >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] Core networking modules missing; installing via pip...${NC}"
    python3 -m pip install requests stem --break-system-packages 2>/dev/null || \
    python3 -m pip install requests stem 2>/dev/null || true
fi

echo -e "${CYAN}[*] Validating Python bytecode compilation...${NC}"
python3 -m compileall -q "$APP_DIR/cyberbreak" 2>/dev/null || true

echo -e "${CYAN}[*] Installing narrowly scoped privileged helper...${NC}"
HELPER_BIN="${HELPER_DIR}/cyberbreak-helper"
$SUDO_CMD cp "${APP_DIR}/cyberbreak/core/helper.py" "$HELPER_BIN"
$SUDO_CMD chown root:root "$HELPER_BIN"
$SUDO_CMD chmod 755 "$HELPER_BIN"

$SUDO_CMD ln -sf "$HELPER_BIN" "${LIBEXEC_DIR}/cyberbreak-helper"

echo -e "${CYAN}[*] Configuring 'cyberbreak' system group and user accounts...${NC}"
if ! getent group cyberbreak >/dev/null 2>&1; then
    $SUDO_CMD groupadd -r cyberbreak
fi

for u in $(awk -F: '$3 >= 1000 && $3 < 60000 {print $1}' /etc/passwd); do
    echo -e "    -> Enrolling user '${BOLD}${u}${NC}' into cyberbreak security group"
    $SUDO_CMD usermod -aG cyberbreak "$u" 2>/dev/null || true
done

echo -e "${CYAN}[*] Installing scoped sudoers privilege rule (/etc/sudoers.d/cyberbreak)...${NC}"
$SUDO_CMD mkdir -p /etc/sudoers.d
$SUDO_CMD tee /etc/sudoers.d/cyberbreak > /dev/null << EOF
%cyberbreak ALL=(root) NOPASSWD: ${HELPER_BIN}, ${LIBEXEC_DIR}/cyberbreak-helper
EOF
$SUDO_CMD chmod 0440 /etc/sudoers.d/cyberbreak
if command -v visudo >/dev/null 2>&1; then
    $SUDO_CMD visudo -cf /etc/sudoers.d/cyberbreak >/dev/null 2>&1 || {
        echo -e "${RED}[WARN] visudo check flagged /etc/sudoers.d/cyberbreak. Reverting...${NC}"
        $SUDO_CMD rm -f /etc/sudoers.d/cyberbreak
    }
fi

echo -e "${CYAN}[*] Installing Polkit policies and rules...${NC}"
$SUDO_CMD mkdir -p /usr/share/polkit-1/actions
if [ -f "${APP_DIR}/polkit/org.cyberbreak.security.policy" ]; then
    $SUDO_CMD cp "${APP_DIR}/polkit/org.cyberbreak.security.policy" /usr/share/polkit-1/actions/
fi

if [ -d /etc/polkit-1/rules.d ]; then
    $SUDO_CMD tee /etc/polkit-1/rules.d/50-cyberbreak.rules > /dev/null << 'EOF'
// Allow members of cyberbreak group to run cyberbreak-helper without authentication
polkit.addRule(function(action, subject) {
    if ((action.id == "org.cyberbreak.security.helper" || action.id == "org.cyberbreak.security.libexec") &&
        subject.isInGroup("cyberbreak")) {
        return polkit.Result.YES;
    }
});
EOF
    $SUDO_CMD chmod 0644 /etc/polkit-1/rules.d/50-cyberbreak.rules
fi

echo -e "${CYAN}[*] Creating global launcher wrapper /usr/local/bin/cyberbreak...${NC}"
$SUDO_CMD tee /usr/local/bin/cyberbreak > /dev/null << 'EOF'
#!/usr/bin/env bash
export PYTHONPATH="/opt/cyberbreak:${PYTHONPATH:-}"
export QTWEBENGINE_CHROMIUM_FLAGS="${QTWEBENGINE_CHROMIUM_FLAGS:-} --disable-gpu-compositing"
exec /usr/bin/python3 -m cyberbreak.main "$@"
EOF
$SUDO_CMD chmod 755 /usr/local/bin/cyberbreak
$SUDO_CMD ln -sf /usr/local/bin/cyberbreak /usr/bin/cyberbreak

$SUDO_CMD mkdir -p /var/log/cyberbreak
$SUDO_CMD chown root:cyberbreak /var/log/cyberbreak 2>/dev/null || true
$SUDO_CMD chmod 775 /var/log/cyberbreak 2>/dev/null || true

echo -e "${CYAN}[*] Installing vector and high-DPI desktop icons...${NC}"
$SUDO_CMD mkdir -p /usr/share/icons/hicolor/scalable/apps
$SUDO_CMD mkdir -p /usr/share/icons/hicolor/256x256/apps
if [ -f "${APP_DIR}/cyberbreak/assets/cyberbreak.svg" ]; then
    $SUDO_CMD cp "${APP_DIR}/cyberbreak/assets/cyberbreak.svg" /usr/share/icons/hicolor/scalable/apps/cyberbreak.svg
    $SUDO_CMD cp "${APP_DIR}/cyberbreak/assets/cyberbreak.svg" /usr/share/icons/hicolor/256x256/apps/cyberbreak.svg
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    $SUDO_CMD gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi

echo -e "${CYAN}[*] Registering system-wide Application Grid launchers...${NC}"
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

$SUDO_CMD tee /usr/share/applications/cyberbreak-browser.desktop > /dev/null << 'EOF'
[Desktop Entry]
Name=CyberBreak Private Browser
GenericName=Zero-Tracking Web Browser
Comment=Hardened Titanium Web Browser with 100/100 PixelDefence Anti-Fingerprinting (By lilami only)
Exec=/usr/local/bin/cyberbreak --browser %u
Icon=cyberbreak
Terminal=false
Type=Application
Categories=Network;WebBrowser;Security;
StartupNotify=true
MimeType=x-scheme-handler/http;x-scheme-handler/https;text/html;
Keywords=browser;privacy;zero-tracking;pixeldefence;webrtc;canvas;fingerprint;
X-Kicksecure-Security-Level=Hardened
EOF
$SUDO_CMD chmod 644 /usr/share/applications/cyberbreak-browser.desktop

if command -v update-desktop-database >/dev/null 2>&1; then
    $SUDO_CMD update-desktop-database 2>/dev/null || true
fi

echo -e "${CYAN}[*] Initializing user config, keystores, and desktop shortcuts across user accounts...${NC}"
for user_home in /home/*; do
    if [ -d "$user_home" ]; then
        u=$(basename "$user_home")
        if id "$u" >/dev/null 2>&1; then
            # Initialize user keystore and header directories for encrypted USB vaults
            user_cb_cfg="${user_home}/.config/cyberbreak"
            user_keys="${user_cb_cfg}/vault_keys"
            user_headers="${user_cb_cfg}/vault_headers"
            user_backups="${user_cb_cfg}/vault_backups"
            $SUDO_CMD mkdir -p "$user_keys" "$user_headers" "$user_backups"
            $SUDO_CMD chown -R "$u:$u" "${user_home}/.config" 2>/dev/null || true
            $SUDO_CMD chmod 700 "$user_keys" "$user_headers" "$user_backups" 2>/dev/null || true

            # Deploy desktop launchers
            desktop_dir="${user_home}/Desktop"
            $SUDO_CMD mkdir -p "$desktop_dir"
            $SUDO_CMD cp /usr/share/applications/cyberbreak.desktop "${desktop_dir}/cyberbreak.desktop"
            $SUDO_CMD cp /usr/share/applications/cyberbreak-browser.desktop "${desktop_dir}/cyberbreak-browser.desktop"
            $SUDO_CMD chmod 755 "${desktop_dir}/cyberbreak.desktop" "${desktop_dir}/cyberbreak-browser.desktop"
            $SUDO_CMD chown "$u:$u" "${desktop_dir}/cyberbreak.desktop" "${desktop_dir}/cyberbreak-browser.desktop"
            echo -e "    -> Placed trusted shortcuts on ${BOLD}${desktop_dir}/${NC}"
            if command -v gio >/dev/null 2>&1; then
                su - "$u" -c "gio set '${desktop_dir}/cyberbreak.desktop' metadata::trusted true" 2>/dev/null || true
                su - "$u" -c "gio set '${desktop_dir}/cyberbreak-browser.desktop' metadata::trusted true" 2>/dev/null || true
            fi
        fi
    fi
done

$SUDO_CMD mkdir -p /etc/skel/Desktop
$SUDO_CMD cp /usr/share/applications/cyberbreak.desktop /etc/skel/Desktop/cyberbreak.desktop
$SUDO_CMD cp /usr/share/applications/cyberbreak-browser.desktop /etc/skel/Desktop/cyberbreak-browser.desktop
$SUDO_CMD chmod 755 /etc/skel/Desktop/cyberbreak.desktop /etc/skel/Desktop/cyberbreak-browser.desktop

echo -e "\n${GREEN}${BOLD}[SUCCESS] CyberBreak installed and configured successfully for Kicksecure!${NC}"
echo -e "${CYAN}----------------------------------------------------------------------${NC}"
echo -e "  * Crafted & Engineered exclusively by ${BOLD}lilami only${NC}."
echo -e "  * Kicksecure separation: Installed via ${BOLD}sysmaint${NC}, fully usable by ${BOLD}user${NC}."
echo -e "  * Ordinary features run directly in user-space without sudo."
echo -e "  * Privileged operations safely routed via scoped ${BOLD}cyberbreak-helper${NC}."
echo -e "  * USB Armory, LUKS2 Vault, Keystore & Formatter fully armed."
echo -e "  * Desktop shortcuts placed on all user accounts in /home/*/Desktop."
echo -e "  * Run from terminal: ${BOLD}cyberbreak${NC}"
echo -e "${CYAN}----------------------------------------------------------------------${NC}\n"
