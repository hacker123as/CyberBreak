# CyberBreak

<div align="center">

**A Hardened Linux Anti-Forensics, Privacy & Hardware Defense Fortress**  
*Crafted and engineered exclusively by **lilami only**.*

[![Linux](https://img.shields.io/badge/Platform-Linux%20%7C%20Kicksecure%20%7C%20Debian%20%7C%20Arch-blue.svg)](#installation)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6%20Glassmorphism-6366f1.svg)](#inside-the-workspace)
[![PixelDefence](https://img.shields.io/badge/PixelDefence-100%2F100%20Verified-00c853.svg)](#browser-privacy)
[![License](https://img.shields.io/badge/Security-Hardened-red.svg)](#privilege-separation--kicksecure-architecture)

</div>

---

## ⚡ Quick One-Line Install (SSH / Terminal)

Copy and paste this single command into your terminal (use the `sysmaint` maintenance account on Kicksecure, or any `sudo` user):

```bash
sudo apt-get update -y && sudo apt-get install -y git curl && rm -rf /tmp/cyberbreak_install && git clone https://github.com/hacker123as/CyberBreak.git /tmp/cyberbreak_install && sudo bash /tmp/cyberbreak_install/scripts/install.sh && rm -rf /tmp/cyberbreak_install
```

> **Kicksecure Multi-User Ready**: The installer runs once under `sysmaint` with administrator privileges. It sets up file permissions, user group enrollments, desktop shortcuts, and the scoped security helper. Immediately after, log in to your everyday restricted `user` account and run `cyberbreak`—**zero root permissions required for ordinary use**.

---

## 📑 Table of Contents

- [Quick One-Line Install](#-quick-one-line-install-ssh--terminal)
- [Kicksecure Privilege Separation Architecture](#privilege-separation--kicksecure-architecture)
- [Core Capabilities](#core-capabilities)
  - [1. Browser Privacy & PixelDefence 100/100](#1-browser-privacy--pixeldefence-100100)
  - [2. USB Armory & Storage Vaults](#2-usb-armory--storage-vaults)
  - [3. Hardware & Listening Port Defense](#3-hardware--listening-port-defense)
  - [4. Network Privacy & VPN Route Verification](#4-network-privacy--vpn-route-verification)
  - [5. Device Identity & Hardware Spoofing](#5-device-identity--hardware-spoofing)
  - [6. Tor Circuit Radar & Stream Isolation](#6-tor-circuit-radar--stream-isolation)
  - [7. Kernel Hardening & AppArmor Enforcer](#7-kernel-hardening--apparmor-enforcer)
  - [8. Emergency Killswitches & Anti-Forensic Sanitize](#8-emergency-killswitches--anti-forensic-sanitize)
- [Inside the 14 Workspaces](#inside-the-14-workspaces)
- [Troubleshooting & Dependency Resolution](#troubleshooting--dependency-resolution)
- [Development & Verification](#development--verification)

---

## Privilege Separation & Kicksecure Architecture

Kicksecure strictly isolates administrative maintenance tasks (`sysmaint` account) from untrusted day-to-day computing (`user` account). CyberBreak embraces this security boundary:

```
+--------------------------------------------------------------------------+
|                        Daily User Space ("user")                        |
|                                                                          |
|   +-------------------+    +--------------------+    +---------------+   |
|   |  PyQt6 GUI / UX   |    |  Off-the-Record    |    | Tor Circuits  |   |
|   |  Glass Canvas     |    |  Chromium Browser  |    | Stem Radar    |   |
|   +---------+---------+    +--------------------+    +---------------+   |
|             |                                                            |
|             v                                                            |
|   +------------------------------------------------------------------+   |
|   |   Non-privileged Operations: Read sysctl, audit routes, parse    |   |
|   |   ss sockets, generate keys, manage local configs in ~/.config   |   |
|   +---------------------------------+--------------------------------+   |
+-------------------------------------|------------------------------------+
                                      | IPC / Scoped Execution
                                      v
+--------------------------------------------------------------------------+
|                Narrowly Scoped Privileged Helper (Root)                  |
|          /usr/local/lib/cyberbreak/cyberbreak-helper                     |
|                                                                          |
|   * Guarded by /etc/sudoers.d/cyberbreak (%cyberbreak group)             |
|   * PolicyKit Action: org.cyberbreak.security.policy                     |
|   * Whitelist commands: iptables lockdown, macchanger, cryptsetup,      |
|     usbguard block, drive-trim, rfkill radio mute                        |
+--------------------------------------------------------------------------+
```

1. **User Execution**: Launching `cyberbreak` requires **no sudo**. Ordinary operations (UI rendering, browser sandboxing, Tor circuit monitoring, config management) execute entirely under the unprivileged user UID.
2. **Narrow Helper**: Operations requiring kernel or network stack adjustments call `/usr/local/lib/cyberbreak/cyberbreak-helper` with validated arguments.
3. **No Sudo Prompts**: Members of the `cyberbreak` group (automatically enrolled during install) dispatch approved actions seamlessly.

---

## Core Capabilities

### 1. Browser Privacy & PixelDefence 100/100

An off-the-record QtWebEngine browser with strict anti-tracking and anti-fingerprinting rules.

- **100/100 Score on Live PixelDefence Check**: Passes all ten runtime privacy tests:
  - **DNT / GPC Headers**: Automated transmission of `DNT: 1` and `Sec-GPC: 1`.
  - **Cookie Sandbox**: Rejects persistent cookies and script-based cookie access.
  - **Canvas Hash Protection**: Disables `toDataURL`, `toBlob`, and `getImageData` pixel extraction so trackers cannot generate canvas hashes.
  - **WebGL Shield**: Disables WebGL contexts and graphics hardware fingerprinting.
  - **WebRTC & Worker Gate**: Blocks WebRTC peer connections and background Web Workers to prevent local IP discovery.
  - **Sensor & Device Access**: Denies camera, microphone, geolocation, battery, and network API queries.
  - **Same-Host Isolation**: Restricts requests to the current origin; cross-origin tracking beacons and third-party CDNs are blocked.
- **Route-Loss Watcher**: Checks policy routes every 15 seconds. If the VPN disconnects or changes paths, browsing is immediately paused.
- **Hardened Firefox Profile Generator**: Generates an isolated Firefox profile (`~/.config/cyberbreak/browser_profile/`) configured with **49 Mozilla privacy directives**, including Enhanced Tracking Protection, resistFingerprinting, and zero disk caching.

---

### 2. USB Armory & Storage Vaults

A complete storage encryption, backup, and formatting suite:

- **Encrypted LUKS2 Vaults**: Encrypts USB flash drives or external disks using **AES-XTS-512**.
  - Windows and unsupported platforms see only raw, unreadable byte blocks.
  - Generates 64-byte cryptographic keyfiles stored in `~/.config/cyberbreak/vault_keys/` with restrictive permissions (`0600`).
- **Vault Deletion & Key Shredding**: One-click vault deletion from the Vaults list safely unmounts filesystems, closes crypt mappers, securely zeroes/shreds keyfiles, and cleans the vault registry.
- **USB Device Refresh**: Dedicated refresh triggers instantly probe the system block topology via `lsblk` JSON parsing.
- **Drive Partition Formatter**: Formats drives as EXT4, Btrfs, FAT32, or exFAT with custom labels.
- **Anti-Forensic Wipe**: Sanitizes drive partition tables and zeroes target block devices.
- **ISO / Disk Image Flasher**: Direct block-level write utility for bootable Linux ISO distributions.
- **System Backup**: Creates timestamped, compressed system archives (`.tar.gz`) directly to external USB storage.
- **SSD TRIM Purge**: Trims mounted filesystems and purges discarded flash blocks.

---

### 3. Hardware & Listening Port Defense

- **Real-Time Listening Port Auditor**: Scans listening TCP and UDP sockets using `ss` and `lsof`.
  - Detects WAN exposure (bound to `0.0.0.0` or wildcard `*`).
  - **Single-Port Killswitch**: Blocks individual ports using iptables and stops the associated process.
  - **Responsive Table Layout**: Automatically adjusts across compact laptops, high-DPI displays, and 4K monitors with no clipped or squished buttons.
- **USBGuard Peripheral Management**: Authorizes or blocks connected USB peripherals (HID keyboards, storage drives, cameras) by device ID and bus address.
- **Kernel Storage Driver Lock**: Disables USB storage kernel modules (`usb_storage`, `uas`) on demand.
- **Hardware Sensor Lockdown**: Controls camera (`uvcvideo`), microphone capture, and Bluetooth radios (`rfkill`).

---

### 4. Network Privacy & VPN Route Verification

- **Dual-Probe Route Inspection**: Queries Linux policy routing tables toward `1.1.1.1` and `8.8.8.8` to ensure all traffic routes through VPN tunnels (`tun0`, `wg0`, `proton0`).
- **IPv6 Leak Prevention**: Audits global IPv6 routes and flags active leaks.
- **Public Identity Check**: Probes multiple independent endpoints (Proton, Mullvad, ifconfig.me) to report current public IP, ISP, and country location.
- **DNS Leak Auditor**: Reads `/etc/resolv.conf` nameservers and validates encryption and resolver trust.

---

### 5. Device Identity & Hardware Spoofing

- **MAC Address Randomization**: Changes MAC addresses across physical and wireless interfaces using `macchanger`.
- **Hostname Scrambler**: Sets random system hostnames to prevent local network identification.
- **Machine ID Regenerator**: Generates fresh `/etc/machine-id` and `/var/lib/dbus/machine-id` tokens.
- **Timezone Normalization**: Sets the system timezone to UTC to defeat browser clock fingerprinting.

---

### 6. Tor Circuit Radar & Stream Isolation

- **Live Circuit Inspector**: Connects to the Tor control port via Stem to list active circuits, relay hops, nicknames, and country flags.
- **NEWNYM Signal Dispatcher**: Requests clean Tor circuits and new exit nodes with one click.
- **Synthetic Background Traffic**: Generates randomized background requests to conceal browsing patterns.

---

### 7. Kernel Hardening & AppArmor Enforcer

- **Sysctl Parameter Matrix**: Audits and applies kernel protections:
  - `kernel.kptr_restrict = 2` (conceal kernel pointers)
  - `kernel.dmesg_restrict = 1` (restrict dmesg access)
  - `kernel.yama.ptrace_scope = 2` (restrict ptrace debugging)
  - `fs.protected_hardlinks = 1` & `fs.protected_symlinks = 1` (link traversal security)
  - `net.ipv4.conf.all.rp_filter = 1` (reverse path filtering)
  - `net.ipv4.tcp_syncookies = 1` (SYN flood protection)
- **AppArmor Profile Enforcer**: Checks active confinement status and enforces installed AppArmor profiles.

---

### 8. Emergency Killswitches & Anti-Forensic Sanitize

- **Panic Lockdown**: Drops network interfaces, stops web browsers, and halts background communication.
- **RAM Cache Drop**: Flushes pagecache, dentries, and inodes via `/proc/sys/vm/drop_caches`.
- **Metadata Cleaner**: Strips EXIF and document metadata from images and documents before sharing.
- **Secure File Shredder**: Overwrites target files before deletion.

---

## Inside the 14 Workspaces

| Workspace | Primary Defense Features |
|---|---|
| **Overview** | System health dashboard, identity pills, interface counters, quick panic toggle. |
| **Network Privacy** | VPN route tester, IPv6 leak audit, DNS configuration, route table evidence. |
| **Browser Privacy** | 100/100 PixelDefence browser, runtime test runner, 49-rule Firefox profile generator. |
| **Device Identity** | MAC address spoofer, hostname generator, machine-id reset, UTC timezone lock. |
| **Tor & Traffic** | Live Stem Tor circuit map, NEWNYM circuit reset, synthetic decoy traffic. |
| **Firewall** | Workstation profiles, VPN tunnel bind rules, iptables flush and inspection. |
| **Hardware & Ports** | Real-time listening port auditor, single-port killswitch, USB authorization, camera/mic/BT locks. |
| **USB & Storage** | LUKS2 encrypted vaults, keystore, drive formatters, ISO flasher, system backups, SSD TRIM. |
| **Kernel Hardening** | Live sysctl audit matrix, one-click kernel parameter enforcer, AppArmor enforcement. |
| **Metadata & Files** | EXIF / metadata stripper, secure file shredder, temporary artifact cleaner. |
| **Preferences** | UI themes, animations, clipboard purge timer, automatic update check. |
| **Emergency** | Network drop switch, browser killer, cache purge, confirmed drive zero-wipe. |
| **Desktop** | Desktop launcher shortcuts, autostart toggle, group membership status. |
| **Audit Terminal** | Real-time execution logs, command exit codes, timestamped action history. |

---

## Troubleshooting & Dependency Resolution

### Missing `PyQt6.QtSvg` (`ModuleNotFoundError: No module named 'PyQt6.QtSvg'`)

On Debian 12 and Kicksecure, Qt6 SVG support is split into a separate package (`python3-pyqt6.qtsvg` and `libqt6svg6`). The installer handles this automatically, and the application includes a fallback vector renderer.

If you encounter this when running from source:

```bash
# Debian / Kicksecure / Ubuntu:
sudo apt-get install -y python3-pyqt6.qtsvg libqt6svg6

# Arch Linux:
sudo pacman -S --noconfirm qt6-svg

# Python pip (standalone / venv):
pip install PyQt6-QtSvg PyQt6-WebEngine requests stem --break-system-packages
```

### Table Buttons Displaying Correctly

All table widgets (such as listening ports and USB device management) use responsive layout containers and dedicated button styles (`QTableWidget QPushButton`). Action buttons dynamically adapt to high-DPI displays, standard 1080p screens, and compact window sizes without text truncation.

---

## Development & Verification

To run tests and check code quality locally:

```bash
# Clone the repository
git clone https://github.com/hacker123as/CyberBreak.git
cd CyberBreak

# Run full test suite
python3 -m unittest discover -s tests -v

# Bytecode syntax validation
python3 -m compileall cyberbreak tests

# Shell script syntax validation
bash -n scripts/install.sh
```

---

<div align="center">

**CyberBreak** • Hardened Anti-Forensics & Privacy  
*Crafted and engineered exclusively by **lilami only**.*

</div>
