# 🛡️ CYBERBREAK: MILITARY-GRADE SECURITY & ANTI-FORENSICS FORTRESS

```
   ______      __               ____                 __  
  / ____/_  __/ /_  ___  _____ / __ )________  ____ _/ /__
 / /   / / / / __ \/ _ \/ ___// __  / ___/ _ \/ __ `/ //_/
/ /___/ /_/ / /_/ /  __/ /   / /_/ / /  /  __/ /_/ / ,<   
\____/\__, /_.___/\___/_/   /_____/_/   \___/\__,_/_/|_|  
     /____/                                               
       HARDENED KICKSECURE SECURITY & DEFENSIVE SYSTEM
```

[![Platform](https://img.shields.io/badge/Platform-Kicksecure%20%7C%20Debian%20%7C%20Linux-00ff66?style=for-the-badge&logo=linux&logoColor=white)](https://www.kicksecure.com/)
[![GUI Engine](https://img.shields.io/badge/GUI-PyQt6%20Neon%20Dark%20QSS-00b8ff?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![VPN Integration](https://img.shields.io/badge/VPN-Proton%20VPN%20Official%20API-6d4aff?style=for-the-badge&logo=protonvpn&logoColor=white)](https://protonvpn.com/)
[![Privilege Model](https://img.shields.io/badge/Auth-Polkit%20pkexec%20Elevation-ff3344?style=for-the-badge&logo=debian&logoColor=white)](https://wiki.debian.org/PolicyKit)
[![Anti-Forensics](https://img.shields.io/badge/Anti--Forensics-LUKS%20Erase%20%2B%20Kernel%20Crash-ffaa00?style=for-the-badge&logo=gnu&logoColor=white)](https://gitlab.com/cryptsetup/cryptsetup)

**CyberBreak** is an advanced defensive workstation security suite and anti-forensics fortress built specifically for **Kicksecure Linux** and hardened Debian environments.

Unlike typical security tools that rely on mocked data, static scripts, or terminal-only interfaces, CyberBreak directly interfaces with Linux kernel subsystems, Netlink sockets, sysfs, procfs, Netfilter iptables, AppArmor, D-Bus, and block device controllers via an asynchronous, zero-freeze PyQt6 dark-theme workstation.

---

## ⚡ Instant Console / SSH Installation (One-Liner)

Copy and paste this single command into your Linux terminal or SSH console:

```bash
sudo apt-get update -y && sudo apt-get install -y git curl && rm -rf /tmp/cyberbreak_install && git clone https://github.com/hacker123as/CyberBreak.git /tmp/cyberbreak_install && sudo bash /tmp/cyberbreak_install/scripts/install.sh && rm -rf /tmp/cyberbreak_install
```

*(This command is also saved in the root repository file [`one line install`](one%20line%20install) and [`one_line_install.sh`](one_line_install.sh).)*

### What the Automated Installer Executes:
1. **Installs System Dependencies**: Resolves packages via `apt-get` / `pacman`:
   - `python3-pyqt6`, `python3-requests`, `python3-stem`, `python3-pip`
   - `macchanger`, `rfkill`, `iptables`, `network-manager`, `ethtool`, `cryptsetup`, `polkit-1`
2. **Deploys Multi-Account System Bundle (`/opt/cyberbreak`)**: Installs the core engine into `/opt/cyberbreak` with universal `755` read/execute permissions so **any user account on the machine can use it**.
3. **Creates Global Launcher (`/usr/local/bin/cyberbreak`)**: Any user can launch CyberBreak simply by running `cyberbreak` in the console.
4. **Registers into Application Grid**: Installs `/usr/share/applications/cyberbreak.desktop` and updates desktop databases so CyberBreak appears natively in the Kicksecure Whisker Menu, Application Finder, GNOME Dash, and KDE Kickoff.
5. **Places Desktop Shortcut**: Drops `cyberbreak.desktop` on your desktop (`~/Desktop/cyberbreak.desktop`), automatically marks it executable (`chmod +x`), and trusted (`gio set ... metadata::trusted true`) to allow 1-click launching with zero security prompts.
6. **Configures Native Polkit Policy**: Installs `/usr/share/polkit-1/actions/org.cyberbreak.security.policy` so regular non-root users receive a native graphical password prompt on launch for kernel-level operations without needing terminal root workarounds.

---

## 📑 Table of Contents
- [Executive Architecture](#-executive-architecture)
- [Proton VPN Integration & Exit Auditor](#-proton-vpn-integration--exit-auditor)
- [Core Modular Subsystems](#-core-modular-subsystems)
  - [1. Comprehensive Leak & Routing Auditor](#1-comprehensive-leak--routing-auditor)
  - [2. Hardware & Identity Spoofer](#2-hardware--identity-spoofer)
  - [3. Tor Controller & Decoy Cover Traffic](#3-tor-controller--decoy-cover-traffic)
  - [4. Hardened Firewall & Killswitch Profiles](#4-hardened-firewall--killswitch-profiles)
  - [5. BadUSB & Hardware Device Interlocks](#5-badusb--hardware-device-interlocks)
  - [6. Kernel Hardening & AppArmor Matrix](#6-kernel-hardening--apparmor-matrix)
  - [7. Metadata Stripper & Military File Shredder](#7-metadata-stripper--military-file-shredder)
  - [8. Auto-Cleaning Clipboard Memory Guard](#8-auto-cleaning-clipboard-memory-guard)
  - [9. Emergency "KILL IT ALL" Panic Center](#9-emergency-kill-it-all-panic-center)
  - [10. Native Linux Desktop & App Grid Manager](#10-native-linux-desktop--app-grid-manager)
  - [11. Live Forensic Terminal & Subprocess Audit Log](#11-live-forensic-terminal--subprocess-audit-log)
- [Complete Master Catalog (73+ Features)](#-complete-master-catalog-73-features)
- [Codebase Structure](#-codebase-structure)
- [Manual Execution & Development](#-manual-execution--development)
- [Threat Model & Security Principles](#-threat-model--security-principles)

---

## 🔬 Executive Architecture

CyberBreak is engineered with strict production principles:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CYBERBREAK PYQT6 WORKSTATION                     │
│  [Dark QSS #121214]  [Sidebar QListWidget]  [Pages QStackedWidget]      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Qt Signals / Slots
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        ASYNC EXECUTOR ENGINE                           │
│  [Non-blocking QThread] [Threadpool] [ANSI Log Emitter] [Error Trap]   │
└───────┬──────────────┬──────────────┬──────────────┬─────────────┬─────┘
        │              │              │              │             │
        ▼              ▼              ▼              ▼             ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌───────────┐┌───────────┐
│ Netlink Sockets││Sysfs & D-Bus ││Netfilter     ││AppArmor & ││Block Storage│
│ IP/DNS/IPv6  ││MAC / Hostname││iptables/nft   ││Sysctl     ││LUKS / TRIM│
│ Route Tables ││USBGuard / HW ││Killswitches   ││Sandbox    ││Sysrq Panic│
└──────────────┘└──────────────┘└──────────────┘└───────────┘└───────────┘
```

- **Zero GUI Freezes**: Probes and commands execute in worker threads with structured Qt signals.
- **Raw Low-Level Syscalls**: Directly parses `/proc/net/route`, `/sys/class/net/*`, `/etc/resolv.conf`, `/proc/net/if_inet6`, and `/proc/sys/*`.
- **Fail-Safe Exception Trapping**: Every subshell execution gracefully intercepts `CalledProcessError`, standard error, and Linux errno codes, streaming them into the live audit terminal.

---

## 🌐 Proton VPN Integration & Exit Auditor

CyberBreak features native integration with **Proton VPN**:

- **Official API Validation**: Directly probes Proton's production location and validation endpoints (`https://api.protonvpn.ch/vpn/location` and `https://api.protonmail.ch/vpn/location`).
- **Autonomous Exit Verification**: Validates whether your public IP belongs to a legitimate Proton VPN exit node, cross-referencing ISP ASN (Proton AG) and server exit coordinates.
- **Interface Sensor**: Audits active Linux network adapters for Proton interfaces (`proton0`, `pvpn*`, `wg-proton*`).
- **Dedicated Proton Killswitch Profile**: Restricts all outbound system traffic exclusively to Proton VPN tunnel interfaces and WireGuard/OpenVPN ports (UDP `51820`, UDP/TCP `1194`, `443`, `8443`), dropping raw physical adapter leaks.
- **Visual Status Badging**: Displays a vivid mint **`PROTON VPN SECURE`** indicator in the dashboard. If Proton disconnects, the UI immediately alerts with a crimson **`BYPASS DETECTED`** warning.

---

## 🧩 Core Modular Subsystems

### 1. Comprehensive Leak & Routing Auditor
- **Triple-Redundant IP/ASN Geo-Resolver**: Queries Proton VPN API, Mullvad, ifconfig.me, and ipify.
- **Default Gateway Route Inspector**: Parses `/proc/net/route` and default gateway tables to ensure traffic exits through encrypted tunnels rather than unencrypted physical NICs (`eth0`, `wlan0`).
- **Active DNS Leak & Ownership Sensor**: Inspects `/etc/resolv.conf`, queries upstream nameservers, and warns if DNS lookups are hijacked by local ISP resolvers.
- **Raw IPv6 Exposure Probe**: Binds to `AF_INET6` sockets and monitors `/proc/net/if_inet6` to detect routable global IPv6 packets (2000::/3) that escape IPv4 VPN tunnels.

### 2. Hardware & Identity Spoofer
- **Physical Network Adapter Randomization**: Enumerates all adapters in `/sys/class/net/*`. Automatically cycles `ip link down` -> `macchanger -r` -> `ip link up` -> `nmcli device reapply`.
- **Wi-Fi Probe Request Randomizer**: Enables `wifi.scan-rand-mac-address = yes` in NetworkManager to defeat passive Wi-Fi location tracking.
- **Dynamic OEM Hostname Generator**: Generates realistic corporate hostnames (`DESKTOP-7F9A2B`, `THINKPAD-E14`) and updates `/etc/hostname` and `/etc/hosts` via `hostnamectl`.
- **Machine-ID Auto-Reseeder**: Overwrites `/etc/machine-id` and `/var/lib/dbus/machine-id` with random entropy from `/dev/urandom`.
- **UTC Timezone Cloaker**: Locks system timezone to UTC (`timedatectl set-timezone UTC`) to neutralize browser JavaScript clock fingerprinting.

### 3. Tor Controller & Decoy Cover Traffic
- **Tor Control Port Interlink (9051)**: Connects to Tor's authenticated control port, inspecting circuits (Guard -> Middle -> Exit).
- **1-Click Identity Renewal**: Dispatches `SIGNAL NEWNYM` to force immediate Tor circuit reconstruction.
- **Kicksecure Stream Isolation**: Configures distinct SOCKS5 authentication credentials per application so applications never share Tor circuits.
- **Synthetic Cover Traffic Generator**: Emits background dummy HTTPS requests to high-traffic domains with randomized packet intervals and sizes to disrupt ISP packet-timing correlation analysis.

### 4. Hardened Firewall & Killswitch Profiles
- **Strict Workstation Shield**: Drops all unrequested incoming packets while permitting stateful outbound traffic; drops all IPv6.
- **Dedicated Proton VPN Killswitch**: Drops all traffic on physical interfaces, strictly allowing traffic over `proton+`, `pvpn+`, `wg+`, `tun+` and WireGuard UDP `51820`.
- **Universal VPN/WireGuard Killswitch**: Enforces strict tunnel-only routing across any VPN configuration.
- **Tor-Only TransPort Profile**: Blocks all system traffic not destined for local Tor TransPort (9040/9050).
- **DNS Hijack Redirector**: Intercepts unencrypted port 53 UDP/TCP traffic and routes it to local encrypted stubs.

### 5. BadUSB & Hardware Device Interlocks
- **BadUSB / Rubber Ducky Defense**: Writes `0` to sysfs `authorized_default` across USB controllers, preventing newly connected USB devices from initializing HID keyboard/mouse inputs.
- **USBGuard Whitelist Manager**: Integrates with the `usbguard` daemon to authorize trusted devices (e.g. YubiKeys).
- **Webcam Hardware Driver Kill**: Unloads `uvcvideo` kernel driver, rendering `/dev/video*` devices completely inaccessible.
- **Microphone Hardware Mute**: Zeroes hardware input capture gain in ALSA, PulseAudio, and PipeWire.

### 6. Kernel Hardening & AppArmor Matrix
- **Kicksecure Kernel Sysctl Enforcement**: Real-time auditing and 1-click enforcement of:
  * `kernel.yama.ptrace_scope = 3` (stops debuggers from memory sniffing)
  * `kernel.unprivileged_bpf_disabled = 1` (kills unprivileged eBPF microcode exploits)
  * `kernel.kptr_restrict = 2` (zeroes kernel memory symbols in `/proc/kallsyms`)
  * `kernel.dmesg_restrict = 1` (blocks unprivileged `dmesg` reading)
  * `net.ipv4.tcp_syncookies = 1` & `net.ipv4.tcp_rfc1337 = 1` (SYN flood & TIME-WAIT protection)
  * `fs.protected_fifos = 2` & `fs.protected_regular = 2` (kills symlink attacks)
- **AppArmor Profile Matrix**: Parses `aa-status` in real time with 1-click enforcement across all profiles in `/etc/apparmor.d/`.

### 7. Metadata Stripper & Military File Shredder
- **In-App `mat2` Sanitizer**: Strips author, GPS, device, and software metadata from PDFs, Office documents, and EXIF image files.
- **DoD 5220.22-M File Shredder**: Cryptographically overwrites files with multiple random byte passes and zeroes (`shred -u -z -n 3`) before unlinking filesystem inodes.
- **RAM Cache Purge**: Flushes file system buffers and drops pagecache, dentries, and inodes via `sync && echo 3 > /proc/sys/vm/drop_caches`.

### 8. Auto-Cleaning Clipboard Memory Guard
- Background daemon monitoring system clipboard memory. Automatically zeroes clipboard contents after a configurable timeout (15s, 30s, or 60s) or whenever the window loses focus, stopping clipboard-stealing malware.

### 9. Emergency "KILL IT ALL" Panic Center
- **Action 1: Sub-50ms Network Blackout ("ISOLATE NOW")**:
  * Fires kernel `rfkill block all` (kills Wi-Fi, Bluetooth, WWAN transmitters).
  * Shuts down NetworkManager (`nmcli networking off`) and takes down all physical NICs.
  * Flushes and locks down iptables/ip6tables with unconditional `DROP` policies.
  * Terminates active browsers, VPNs, Tor, SSH, and messenger processes (`pkill -9`).
- **Action 2: Master Cryptographic Nuke ("NUKE SYSTEM")**:
  * Protected by a high-contrast crimson password authorization modal (requires master passphrase such as `1234567890` or root password).
  * **LUKS Header Obliteration (<100ms)**: Destroys encryption keyslots via `cryptsetup luksErase` and random `dd` overwrite on the first 16MB of block devices, rendering AES ciphertext mathematically irrecoverable.
  * **Hardware NVMe/SSD Discard**: Issues `blkdiscard -f -z` across all physical disks to force hardware flash cell erasure.
  * **Partition Table Zapping**: `sgdisk --zap-all` clears MBR/GPT structures.
  * **Intentional Hard Kernel Panic**: Enables sysrq (`echo 1 > /proc/sys/kernel/sysrq`) and crashes the kernel immediately (`echo c > /proc/sysrq-trigger`), cutting power before DRAM decay can be imaged in cold-boot forensic attacks.

### 10. Native Linux Desktop & App Grid Manager
- 1-click controls to register into the system Application Grid (`/usr/share/applications/`), generate trusted Desktop shortcuts (`~/Desktop/cyberbreak.desktop`), or toggle system autostart on boot.

### 11. Live Forensic Terminal & Subprocess Audit Log
- Dedicated `#09090b` dark monospace terminal capturing all subshell commands, stdout, and stderr with millisecond timestamps (`[HH:MM:SS] [LEVEL]`).

---

## 📋 Complete Master Catalog (73+ Features)

| # | Category | Feature Name | Low-Level Subsystem / Implementation |
|---|---|---|---|
| 1 | Network | External IP/Geo Resolver | Triple-endpoint query: Proton VPN API, Mullvad, ifconfig.me |
| 2 | Network | Proton VPN Connection Auditor | Queries `https://api.protonvpn.ch/vpn/location` |
| 3 | Network | ASN & ISP Ownership Resolver | Cross-references active IP against autonomous ASN databases |
| 4 | Network | Gateway Route Auditor | Parses `/proc/net/route` & `ip -j route show default` |
| 5 | Network | Gateway Bypass Sentinel | Flags traffic exiting raw physical adapters instead of tunnels |
| 6 | Network | Raw AF_INET6 Socket Probe | Tests raw IPv6 socket creation & audits `/proc/net/if_inet6` |
| 7 | Network | Nonce-Based DNS Leak Test | Dispatches unique UUID DNS queries to detect ISP proxies |
| 8 | Network | DNS Resolver Ownership Check | Inspects `/etc/resolv.conf` nameservers against Zero-Knowledge DNS |
| 9 | Network | WebRTC STUN Packet Sensor | Scans UDP port 3478 exposure to prevent real-IP leaks |
| 10 | Network | DNS-over-HTTPS/TLS Switcher | Switcher profiles for Proton, Mullvad, Quad9, Cloudflare |
| 11 | Network | DNSSEC Validation Check | Verifies cryptographic RRSIG DNS record signatures |
| 12 | Network | Covert ICMP Tunnel Detector | Monitors abnormal ICMP packet payload sizes via AF_PACKET |
| 13 | Network | Network MTU Normalizer | Normalizes MTU sizes to foil packet-size fingerprinting |
| 14 | Hardware | MAC Address Randomizer | Automated `ip link down` -> `macchanger -r` -> `ip link up` |
| 15 | Hardware | Vendor OUI Pool Spoofing | Emulates authentic Dell, Intel, or Apple network card pools |
| 16 | Hardware | Wi-Fi Probe MAC Randomizer | Enables `wifi.scan-rand-mac-address = yes` in NetworkManager |
| 17 | Hardware | Dynamic OEM Hostname Spoofer | Rotates system hostname via `hostnamectl` and syncs `/etc/hosts` |
| 18 | Hardware | Machine-ID Auto-Reseeder | Zeroes and re-generates `/etc/machine-id` with `/dev/urandom` |
| 19 | Hardware | DMI / SMBIOS UUID Auditor | Audits `/sys/devices/virtual/dmi/id/*` for tracking serials |
| 20 | Hardware | UTC Timezone Enforcer | Sets timezone to UTC (`timedatectl set-timezone UTC`) |
| 21 | Hardware | BLE Address Rotator | Rotates Bluetooth Low Energy MAC addresses via `btmgmt` |
| 22 | Hardware | Viewport Resolution Shield | Normalizes browser viewports to standard 1080p targets |
| 23 | Tor | Tor Control Port Inspector | Authenticated socket to port 9051 visualizes circuit hops |
| 24 | Tor | 1-Click Identity Rebuilder | Dispatches `SIGNAL NEWNYM` to force circuit reconstruction |
| 25 | Tor | Stream Isolation Manager | Assigns unique SOCKS5 authentication tags per process |
| 26 | Tor | Decoy Cover Traffic Generator | Emits synthetic dummy HTTPS requests to mask packet timing |
| 27 | Tor | Pluggable Transports Manager | Bridge configurations for obfs4, Snowflake, and Meek |
| 28 | Tor | Ephemeral .onion File Drop | Spins up temporary v3 hidden service for private transfers |
| 29 | Tor | Secure Time Sync (sdwdate) | HTTP-based anonymous time sync over Tor defeating NTP skew |
| 30 | Firewall | Strict Workstation Profile | Unconditional inbound drop, stateful outbound only |
| 31 | Firewall | Dedicated Proton Killswitch | Restricts traffic strictly to `proton+`, `pvpn+`, `wg+`, `tun+` |
| 32 | Firewall | Universal VPN Killswitch | Drops all traffic not exiting via `tun+`, `wg+`, or `proton+` |
| 33 | Firewall | Tor TransPort Profile | Enforces all system traffic to route exclusively through Tor |
| 34 | Firewall | DNS Hijack Redirector | Forces all port 53 traffic into local encrypted resolvers |
| 35 | Firewall | Dynamic Port Scan Blackhole | Null-routes IPs executing unauthorized port scans |
| 36 | Firewall | RFKILL Wireless Lockdown | Severs Wi-Fi, Bluetooth, and WWAN at kernel radio level |
| 37 | Defense | BadUSB / Rubber Ducky Shield | Sysfs `authorized_default = 0` blocks new USB HID devices |
| 38 | Defense | USBGuard Whitelist Policy | Approves trusted YubiKeys and storage tokens |
| 39 | Defense | Keystroke Injection Throttler | Rate-limits USB scancodes to foil automated keystroke injection |
| 40 | Defense | Webcam Hardware Driver Kill | Unloads `uvcvideo` kernel driver, locking `/dev/video*` |
| 41 | Defense | Microphone Hardware Mute | Zeroes hardware input capture gain in ALSA / PulseAudio |
| 42 | Defense | Ultrasonic Beacon Filter | Filters audio frequencies >18kHz used by tracking beacons |
| 43 | Defense | DMA Attack Shield | Verifies IOMMU bus protection and disables Thunderbolt |
| 44 | Defense | Anti-Extraction Tamper Trigger | Lid close / AC disconnect auto-triggers emergency isolation |
| 45 | Kernel | YAMA Ptrace Memory Lock | `kernel.yama.ptrace_scope = 3` stops memory sniffing |
| 46 | Kernel | Unprivileged eBPF Disabler | `kernel.unprivileged_bpf_disabled = 1` kills microcode exploits |
| 47 | Kernel | Kernel Pointer Leak Protection | `kernel.kptr_restrict = 2` zeroes symbols in `/proc/kallsyms` |
| 48 | Kernel | Kernel Ring Buffer Lock | `kernel.dmesg_restrict = 1` restricts `dmesg` logs to root |
| 49 | Kernel | TCP SYN & RFC-1337 Protection | Shields against SYN floods and TIME-WAIT assassination |
| 50 | Kernel | Procfs Process Hiding | `hidepid=2` mount option hides processes from other users |
| 51 | Kernel | Core Dump Scrambler | `prctl(PR_SET_DUMPABLE, 0)` stops memory dumps on crash |
| 52 | Kernel | AppArmor Profile Enforcer | Parses `aa-status` and enforces all profiles in `/etc/apparmor.d/` |
| 53 | Kernel | Bubblewrap (bwrap) Sandbox | Runs untrusted binaries in isolated mount namespaces |
| 54 | Kernel | LD_PRELOAD Hijack Scanner | Audits `/etc/ld.so.preload` and dynamic link integrity |
| 55 | Kernel | Process Title Camouflage | `prctl(PR_SET_NAME)` masks processes as `[kworker/u16:2]` |
| 56 | Kernel | Self-Trace Debugger Lock | `ptrace(PTRACE_TRACEME)` prevents debuggers from attaching |
| 57 | Shredding | Metadata Stripper (mat2) | In-app drag-and-drop sanitization of PDFs, docs, images |
| 58 | Shredding | Auto-Wiping Clipboard Guard | Zeroes clipboard contents after 15/30/60s or on window blur |
| 59 | Shredding | Multi-Pass File Shredder | Overwrites files with random bytes & zeroes (`shred -u -z -n 3`) |
| 60 | Shredding | Kernel RAM Cache Purge | `sync && echo 3 > /proc/sys/vm/drop_caches` |
| 61 | Shredding | Shell History Inoculator | Sets `HISTFILE=/dev/null` and cleans bash/zsh history records |
| 62 | Shredding | Journal Vacuum Sanitizer | Flushes event traces via `journalctl --vacuum-time=1s` |
| 63 | Shredding | File Timestomp Engine | Synchronizes/randomizes access, modify, and change timestamps |
| 64 | Shredding | Encrypted RAM Disk Creator | Creates ephemeral LUKS-encrypted containers inside volatile RAM |
| 65 | Panic | Sub-50ms Network Blackout | `rfkill block all` + `nmcli off` + iptables DROP-ALL |
| 66 | Panic | Process Neutralizer | `pkill -9` on browsers, VPNs, Tor, SSH, and messengers |
| 67 | Panic | Password-Gated Master Nuke | High-contrast modal requiring authorization passphrase |
| 68 | Panic | LUKS Header Obliteration | `cryptsetup luksErase` + random block write in <100ms |
| 69 | Panic | NVMe / SSD NAND Flash Discard | Controller-level block purge via `blkdiscard -f -z` |
| 70 | Panic | Partition Table Zapping | `sgdisk --zap-all` clears MBR/GPT records |
| 71 | Panic | Hard Kernel Crash Panic | `echo 1 > sysrq && echo c > sysrq-trigger` defeats cold-boot |
| 72 | Desktop | Live Forensic Terminal | Real-time subprocess capture with millisecond timestamps |
| 73 | Desktop | App Grid Integration | `/usr/share/applications/cyberbreak.desktop` FreeDesktop entry |
| 74 | Desktop | Trusted Desktop Shortcut | Executable `~/Desktop/cyberbreak.desktop` with trusted metadata |
| 75 | Desktop | Polkit Graphical Elevation | `org.cyberbreak.security.policy` native GUI password prompt |

---

## 📂 Codebase Structure

```
CyberBreak/
├── cyberbreak/
│   ├── __init__.py                 # Root package metadata
│   ├── main.py                     # Application launcher & High-DPI setup
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py          # Left QListWidget navigation + QStackedWidget
│   │   ├── styles.py               # Complete dark modern QSS theme
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── status_card.py      # Metric cards with dynamic status pills
│   │   │   └── nuke_dialog.py      # Password-gated crimson emergency modal
│   │   └── pages/
│   │       ├── __init__.py
│   │       ├── dashboard_page.py   # Security status matrix & Proton VPN badge
│   │       ├── leak_page.py        # Real socket IP, route, DNS, & IPv6 auditor
│   │       ├── spoofer_page.py     # MAC, hostname, machine-id, timezone spoofer
│   │       ├── tor_cover_page.py   # Tor control port & synthetic cover traffic
│   │       ├── firewall_page.py    # Strict, Proton VPN, & universal killswitches
│   │       ├── usbguard_page.py    # BadUSB defense, webcam & mic hardware kill
│   │       ├── hardening_page.py   # Sysctl matrix & AppArmor enforcer
│   │       ├── metadata_page.py    # mat2 metadata stripper & file shredder
│   │       ├── panic_page.py       # "ISOLATE NOW" & "NUKE SYSTEM" panic center
│   │       ├── desktop_page.py     # Desktop shortcut & app grid manager
│   │       └── terminal_page.py    # Live full-screen forensic audit terminal
│   ├── core/
│   │   ├── __init__.py
│   │   ├── executor.py             # Asynchronous process runner with Qt signals
│   │   ├── desktop_integrator.py   # .desktop generation & polkit setup
│   │   ├── network_auditor.py      # Socket probes, Proton VPN API, route parser
│   │   ├── spoofer_engine.py       # macchanger, hostnamectl, machine-id logic
│   │   ├── tor_controller.py       # Tor stem control port & decoy cover traffic
│   │   ├── firewall_controller.py  # Iptables/nftables & Proton killswitch rules
│   │   ├── hardware_manager.py     # USBGuard D-Bus & webcam/mic modprobe
│   │   ├── kernel_hardening.py     # Sysctl parameters & aa-status parser
│   │   ├── metadata_cleaner.py     # mat2 wrapper & secure shredding
│   │   ├── clipboard_guard.py      # Auto-cleaning clipboard timer
│   │   ├── isolation.py            # Fast sub-50ms network blackout
│   │   └── nuke_engine.py          # LUKS erase, blkdiscard, sysrq kernel panic
│   └── assets/
│       ├── cyberbreak.svg          # Scalable vector application icon
│       └── cyberbreak.desktop      # FreeDesktop launcher template
├── polkit/
│   └── org.cyberbreak.security.policy # Native Polkit root authorization policy
├── scripts/
│   └── install.sh                  # One-step system-wide installer
├── one line install                # Raw single-line install command
├── one_line_install.sh             # Executable one-line script
├── requirements.txt                # Python package dependencies
├── README.md                       # Master documentation & catalog
└── .gitignore                      # Git ignore rules
```

---

## 🚀 Manual Execution & Development

### Running Directly from Source:
```bash
# 1. Install prerequisites
sudo apt-get install -y python3-pyqt6 python3-requests python3-stem macchanger rfkill iptables

# 2. Run application
python3 -m cyberbreak.main
```

### Running with Native Polkit Elevation:
```bash
pkexec python3 -m cyberbreak.main
```

### Launching Installed System Binary:
```bash
cyberbreak
```

---

## 🔒 Threat Model & Security Principles

1. **Anti-Fingerprinting**: System identifiers (MAC, hostname, machine-id, timezone) are decoupled from physical hardware, defeating cross-session device tracking.
2. **Strict Tunnel Containment**: Real sockets and route tables are audited continuously. If encrypted VPN or Tor interfaces drop, the killswitch immediately halts traffic to eliminate unencrypted leakage.
3. **Physical Interlocks**: Protects against physical hardware attacks (BadUSB/Rubber Ducky keystroke injection, rogue cameras, acoustic room eavesdropping).
4. **Anti-Cold Boot & Cryptographic Sanitization**: In physical seizure or raid scenarios, the Master Nuke system destroys LUKS header blocks and triggers an intentional kernel crash (`sysrq c`), cutting power to prevent memory decay extraction.
