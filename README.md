# 🛡️ CYBERBREAK: MILITARY-GRADE DEFENSIVE FORTRESS & ANTI-FORENSICS
### ⚡ CRAFTED & ENGINEERED EXCLUSIVELY BY LILAMI

```
   ______      __               ____                 __  
  / ____/_  __/ /_  ___  _____ / __ )________  ____ _/ /__
 / /   / / / / __ \/ _ \/ ___// __  / ___/ _ \/ __ `/ //_/
/ /___/ /_/ / /_/ /  __/ /   / /_/ / /  /  __/ /_/ / ,<   
\____/\__, /_.___/\___/_/   /_____/_/   \___/\__,_/_/|_|  
     /____/                                               
       HARDENED DEFENSIVE WORKSTATION • BY LILAMI ONLY
```

[![Architect](https://img.shields.io/badge/Architect-lilami%20Only-00ff66?style=for-the-badge&logo=target&logoColor=black)](https://github.com/hacker123as/CyberBreak)
[![Platform](https://img.shields.io/badge/Platform-Kicksecure%20%7C%20Debian%20%7C%20Linux-00ff66?style=for-the-badge&logo=linux&logoColor=white)](https://www.kicksecure.com/)
[![GUI Engine](https://img.shields.io/badge/GUI-PyQt6%20Neon%20Dark%20QSS-00b8ff?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Storage Armory](https://img.shields.io/badge/Storage-LUKS2%20Vault%20%2B%20ISO%20Burner-6d4aff?style=for-the-badge&logo=usb&logoColor=white)](https://gitlab.com/cryptsetup/cryptsetup)
[![Privilege Model](https://img.shields.io/badge/Auth-Scoped%20Helper%20%2B%20Polkit%20%2F%20Sudoers-00ff66?style=for-the-badge&logo=gnu&logoColor=white)](https://wiki.debian.org/PolicyKit)
[![Anti-Forensics](https://img.shields.io/badge/Anti--Forensics-LUKS%20Erase%20%2B%20Kernel%20Crash-ffaa00?style=for-the-badge&logo=gnu&logoColor=white)](https://gitlab.com/cryptsetup/cryptsetup)

**CyberBreak** is an advanced defensive workstation security fortress, storage armory, and anti-forensics system engineered **by lilami** specifically for **Kicksecure Linux** and hardened Debian environments.

Unlike typical security tools that rely on mocked data, static scripts, or terminal-only interfaces, CyberBreak directly interfaces with Linux kernel subsystems, Netlink sockets, sysfs, procfs, Netfilter iptables, AppArmor, D-Bus, block storage encryption, and disk formatting controllers via an asynchronous, zero-freeze PyQt6 dark neon cyber workstation.

---

## ⚡ Instant Console / SSH Installation (One-Liner)

Copy and paste this single command into your Linux terminal or SSH console (execute via administrator account `sysmaint` with sudo):

```bash
sudo apt-get update -y && sudo apt-get install -y git curl && rm -rf /tmp/cyberbreak_install && git clone https://github.com/hacker123as/CyberBreak.git /tmp/cyberbreak_install && sudo bash /tmp/cyberbreak_install/scripts/install.sh && rm -rf /tmp/cyberbreak_install
```

*(This command is also saved in the root repository file [`one line install`](one%20line%20install) and [`one_line_install.sh`](one_line_install.sh).)*

### What the Automated Installer Executes:
1. **Installs System Dependencies**: Resolves packages via `apt-get` / `pacman`:
   - `python3-pyqt6`, `python3-requests`, `python3-stem`, `python3-pip`
   - `macchanger`, `rfkill`, `iptables`, `network-manager`, `ethtool`, `cryptsetup`, `dosfstools`, `e2fsprogs`, `tar`, `zstd`, `fdisk`, `btrfs-progs`, `polkit-1`
2. **Deploys Multi-Account System Bundle (`/opt/cyberbreak`)**: Installs the core engine into `/opt/cyberbreak` with clean `root:root` `755` permissions so **any user account on the machine can execute the code**.
3. **Installs Scoped Privileged Helper (`/usr/local/lib/cyberbreak/cyberbreak-helper`)**: Hardened root-owned Python dispatcher restricted strictly to whitelisted actions (MAC spoofing, firewall profiles, hardware locks, sysctl enforcement, USB LUKS encryption, ISO burning, OS backup, emergency blackout, and panic wipes).
4. **Enrolls Restricted Users in `cyberbreak` Group**: Automatically creates system group `cyberbreak` and adds all desktop accounts (including `user` and `sysmaint`) and `/etc/skel`.
5. **Configures Least-Privilege Sudoers & Polkit**: Drops `/etc/sudoers.d/cyberbreak` granting members passwordless execution *strictly* to `/usr/local/lib/cyberbreak/cyberbreak-helper` (no arbitrary root commands), with backup Polkit policy and rule (`/usr/share/polkit-1/actions/org.cyberbreak.security.policy` and `/etc/polkit-1/rules.d/50-cyberbreak.rules`).
6. **Creates Unprivileged Global Launcher (`/usr/local/bin/cyberbreak`)**: Launches directly as the calling user—never wraps the entire Qt GUI in `pkexec` or `sudo`, avoiding Wayland/X11 socket permission issues and unwanted root desktop environments.
7. **Registers Global Desktop Application**: Installs `/usr/share/applications/cyberbreak.desktop` and `/usr/share/icons/hicolor/scalable/apps/cyberbreak.svg`, updating XDG application databases.
8. **Configures 1-Click Trusted Desktop Launchers**: Iterates through all `/home/*` desktop directories (e.g. `/home/user/Desktop`, `/home/sysmaint/Desktop`, and `/etc/skel/Desktop`), marking shortcuts trusted (`gio set metadata::trusted true`) and executable for instant non-root launching.

---

## 🔐 Kicksecure Multi-Account Security Model (sysmaint vs user)

Kicksecure enforces strict privilege separation between:
- **`sysmaint`**: The dedicated system maintenance account possessing `sudo` rights for software installation, package updates, and system configuration.
- **`user`**: The unprivileged everyday workstation account used for browsing, terminal activity, and general application execution.

### How CyberBreak Seamlessly Bridges This Boundary
1. **Zero Root GUI Execution**: Running PyQt6/Wayland under `sudo` or `pkexec` breaks display access, corrupts user config ownership, and violates Kicksecure hardening. CyberBreak GUI runs 100% as the unprivileged desktop `user`.
2. **Secure Privileged Helper**: Operations requiring kernel or network configuration are dispatched to `/usr/local/lib/cyberbreak/cyberbreak-helper`. The helper validates every parameter with strict regular expressions and only executes pre-approved defensive actions.
3. **No Blanket Sudo**: The `user` account is never given general root access. `/etc/sudoers.d/cyberbreak` only authorizes execution of the single binary path `/usr/local/lib/cyberbreak/cyberbreak-helper`.
4. **Maintenance Task Guidance**: System-level administrative actions (such as installing new system-wide packages or performing base OS upgrades) display clean instructional dialogues prompting the operator to switch to `sysmaint` rather than failing with silent permission errors.

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
  - [6. USB & Storage Armory (Swiss Army Knife by lilami)](#6-usb--storage-armory-swiss-army-knife-by-lilami)
  - [7. Kernel Hardening & AppArmor Matrix](#7-kernel-hardening--apparmor-matrix)
  - [8. Metadata Stripper & Military File Shredder](#8-metadata-stripper--military-file-shredder)
  - [9. Auto-Cleaning Clipboard Memory Guard](#9-auto-cleaning-clipboard-memory-guard)
  - [10. Control Center & Global Automation Settings](#10-control-center--global-automation-settings)
  - [11. Emergency "KILL IT ALL" Panic Center](#11-emergency-kill-it-all-panic-center)
  - [12. Native Linux Desktop & App Grid Manager](#12-native-linux-desktop--app-grid-manager)
  - [13. Live Forensic Terminal & Subprocess Audit Log](#13-live-forensic-terminal--subprocess-audit-log)
- [Complete Master Catalog (150+ Features)](#-complete-master-catalog-150-features)
- [Codebase Structure](#-codebase-structure)
- [Manual Execution & Development](#-manual-execution--development)
- [Threat Model & Security Principles](#-threat-model--security-principles)

---

## 🔬 Executive Architecture

CyberBreak is engineered with strict production principles:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CYBERBREAK PYQT6 WORKSTATION                     │
│  [Dark Neon #0b0c10] [Sidebar QListWidget] [13 Pages QStackedWidget]   │
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
│ IP/DNS/IPv6  ││MAC / Hostname││iptables/nft   ││Sysctl     ││LUKS2 / TRIM│
│ Route Tables ││USBGuard / HW ││Killswitches   ││Sandbox    ││ISO & Backup│
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
- **Real IP Exposure Warning Banner**: Giant pulsating red indicator whenever your direct connection or real IP is revealed to external servers:
  ```
  ⚠️ WARNING: YOUR REAL IP IS REVEALED!
  Physical location (City, State, Country) and ISP exposed.
  ```
- **Triple-Redundant IP/ASN Geo-Resolver**: Queries Proton VPN API, Mullvad, ipapi.co, ifconfig.me, and ipify.
- **Full Geolocation Coordinates**: Displays City, State/Region, Country, Postal Code, ASN, and Timezone.
- **Default Gateway Route Inspector**: Parses `/proc/net/route` and default gateway tables to ensure traffic exits through encrypted tunnels rather than unencrypted physical NICs (`eth0`, `wlan0`).
- **Active DNS Leak & Ownership Sensor**: Inspects `/etc/resolv.conf`, queries upstream nameservers, and warns if DNS lookups are hijacked by local ISP resolvers.
- **Raw IPv6 Exposure Probe**: Binds to `AF_INET6` sockets and monitors `/proc/net/if_inet6` to detect routable global IPv6 packets (2000::/3) that escape IPv4 VPN tunnels.
- **1-Click Instant Seal Button**: Instantly engages the VPN killswitch to plug leaks on demand.

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

### 6. USB & Storage Armory (Swiss Army Knife by lilami)
- **LUKS2 Hardware Vault Encoder**: Formats USB drives with military AES-XTS-512 LUKS2 encryption.
- **App Keystore Integration**: Generates 512-bit cryptographic keys and stores them securely inside `~/.config/cyberbreak/vault_keys/` (`0600` permissions).
- **Windows Stealth Guarantee**: When plugged into Windows, Windows sees NO readable partition, file table, or OS data—it is completely unreadable, unparseable, and prompts "Format Disk", protecting your secret data from forensic preview!
- **1-Click Decoder & Mount**: Auto-detects connected encrypted drives, matches stored app keys, and mounts them to `/media/$USER/<label>` with 1 click.
- **Universal Drive Formatter**: Formats partitions to EXT4, Btrfs, FAT32 (`vfat`), or ExFAT with custom labels.
- **DoD Partition Table Sanitizer**: Zero-fills MBR/GPT and raw initial sectors to defeat partition table recovery.
- **Live ISO Burner / Flasher**: Writes bootable ISOs (Kicksecure, Whonix, Tails, Arch, Debian) directly to raw USB flash devices with unbuffered `conv=fdatasync` streaming.
- **Full OS / System Backup to USB**: Creates a live compressed snapshot archive (`.tar.gz`) of user files (`/home/$USER`) or essential system configurations (`/etc`, `/usr/local/bin`, `~`) directly onto USB storage.
- **Supercharged SSD TRIM Engine**: Issues `fstrim -av` discards across all SSDs, NVMe drives, and dm-crypt LUKS volumes.

### 7. Kernel Hardening & AppArmor Matrix
- **Kicksecure Kernel Sysctl Enforcement**: Real-time auditing and 1-click enforcement of:
  * `kernel.yama.ptrace_scope = 3` (stops debuggers from memory sniffing)
  * `kernel.unprivileged_bpf_disabled = 1` (kills unprivileged eBPF microcode exploits)
  * `kernel.kptr_restrict = 2` (zeroes kernel memory symbols in `/proc/kallsyms`)
  * `kernel.dmesg_restrict = 1` (blocks unprivileged `dmesg` reading)
  * `net.ipv4.tcp_syncookies = 1` & `net.ipv4.tcp_rfc1337 = 1` (SYN flood & TIME-WAIT protection)
  * `fs.protected_fifos = 2` & `fs.protected_regular = 2` (kills symlink attacks)
- **AppArmor Profile Matrix**: Parses `aa-status` in real time with 1-click enforcement across all profiles in `/etc/apparmor.d/`.

### 8. Metadata Stripper & Military File Shredder
- **In-App `mat2` Sanitizer**: Strips author, GPS, device, and software metadata from PDFs, Office documents, and EXIF image files.
- **DoD 5220.22-M File Shredder**: Cryptographically overwrites files with multiple random byte passes and zeroes (`shred -u -z -n 3`) before unlinking filesystem inodes.
- **RAM Cache Purge**: Flushes file system buffers and drops pagecache, dentries, and inodes via `sync && echo 3 > /proc/sys/vm/drop_caches`.

### 9. Auto-Cleaning Clipboard Memory Guard
- Background daemon monitoring system clipboard memory. Automatically zeroes clipboard contents after a configurable timeout (15s, 30s, 60s, or 120s) or whenever the window loses focus, stopping clipboard-stealing malware.

### 10. Control Center & Global Automation Settings
- **Defensive Automation Switches**:
  * Auto-Arm Killswitch on Boot
  * Auto-Randomize MAC on Network Connect
  * Auto-Isolate on IP/DNS Leak Detection
  * Strict BadUSB on Idle
  * Blacklist Webcam Driver by Default
  * High-Voltage Threat Audio Alerts
  * Auto-Check for App Updates on Startup
- **App Repository Auto-Updater**: Directly checks GitHub commits, displays remote vs local hash, and synchronizes updates cleanly without breaking user configs or vault keys.

### 11. Emergency "KILL IT ALL" Panic Center
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

### 12. Native Linux Desktop & App Grid Manager
- 1-click controls to register into the system Application Grid (`/usr/share/applications/`), generate trusted Desktop shortcuts across all accounts (`/home/*/Desktop`), or toggle system autostart on boot.

### 13. Live Forensic Terminal & Subprocess Audit Log
- Dedicated `#08090d` dark monospace terminal capturing all subshell commands, stdout, and stderr with millisecond timestamps (`[HH:MM:SS] [LEVEL]`).

---

## 📋 Complete Master Catalog (150+ Features)

| # | Category | Feature Name | Low-Level Subsystem / Implementation |
|---|---|---|---|
| 1 | Network | Real IP Exposure Warning Banner | Instant pulsating alert banner when direct uncloaked IP is revealed |
| 2 | Network | External IP/Geo Resolver | Triple-endpoint query: Proton VPN API, Mullvad, ifconfig.me |
| 3 | Network | Physical City / Region Intel | Identifies municipal location exposed to remote tracking servers |
| 4 | Network | Physical State / Province Sensor | Pinpoints state / province geolocation of outbound connection |
| 5 | Network | Postal Code Resolution | Queries location postal code leaks |
| 6 | Network | ASN & ISP Ownership Resolver | Cross-references active IP against autonomous ASN databases |
| 7 | Network | Proton VPN Connection Auditor | Queries `https://api.protonvpn.ch/vpn/location` |
| 8 | Network | Proton Local Adapter Sensor | Detects `proton0`, `pvpn*`, `wg-proton*` Netlink virtual interfaces |
| 9 | Network | Gateway Route Auditor | Parses `/proc/net/route` & `ip -j route show default` |
| 10 | Network | Gateway Bypass Sentinel | Flags traffic exiting raw physical adapters instead of tunnels |
| 11 | Network | Raw AF_INET6 Socket Probe | Tests raw IPv6 socket creation & audits `/proc/net/if_inet6` |
| 12 | Network | IPv6 Global Address Detector | Scans for routable `2000::/3` scopes bypassing VPN rules |
| 13 | Network | Nonce-Based DNS Leak Test | Dispatches unique UUID DNS queries to detect ISP proxies |
| 14 | Network | DNS Resolver Ownership Check | Inspects `/etc/resolv.conf` nameservers against Zero-Knowledge DNS |
| 15 | Network | Private Tunnel DNS Validator | Verifies `10.2.0.1` / `10.x.x.x` private tunnel resolver isolation |
| 16 | Network | WebRTC STUN Packet Sensor | Scans UDP port 3478 exposure to prevent real-IP leaks |
| 17 | Network | DNS-over-HTTPS/TLS Switcher | Switcher profiles for Proton, Mullvad, Quad9, Cloudflare |
| 18 | Network | DNSSEC Validation Check | Verifies cryptographic RRSIG DNS record signatures |
| 19 | Network | Covert ICMP Tunnel Detector | Monitors abnormal ICMP packet payload sizes via AF_PACKET |
| 20 | Network | Network MTU Normalizer | Normalizes MTU sizes to foil packet-size fingerprinting |
| 21 | Network | 1-Click Instant Leak Sealer | Immediate dispatch of VPN-only killswitch rules |
| 22 | Hardware | MAC Address Randomizer | Automated `ip link down` -> `macchanger -r` -> `ip link up` |
| 23 | Hardware | Vendor OUI Pool Spoofing | Emulates authentic Dell, Intel, or Apple network card pools |
| 24 | Hardware | Wi-Fi Probe MAC Randomizer | Enables `wifi.scan-rand-mac-address = yes` in NetworkManager |
| 25 | Hardware | Dynamic OEM Hostname Spoofer | Rotates system hostname via `hostnamectl` and syncs `/etc/hosts` |
| 26 | Hardware | Corporate Hostname Template | Generates authentic corporate naming conventions |
| 27 | Hardware | Machine-ID Auto-Reseeder | Zeroes and re-generates `/etc/machine-id` with `/dev/urandom` |
| 28 | Hardware | D-Bus Machine-ID Sync | Mirrors machine-id into `/var/lib/dbus/machine-id` |
| 29 | Hardware | DMI / SMBIOS UUID Auditor | Audits `/sys/devices/virtual/dmi/id/*` for tracking serials |
| 30 | Hardware | Motherboard Serial Cloaker | Identifies exposed board serial numbers in sysfs |
| 31 | Hardware | Chassis Type Masker | Shields chassis type indicators from unprivileged probes |
| 32 | Hardware | UTC Timezone Enforcer | Sets timezone to UTC (`timedatectl set-timezone UTC`) |
| 33 | Hardware | RTC Hardware Clock Sync | Syncs hardware CMOS real-time clock to UTC standard |
| 34 | Hardware | BLE Address Rotator | Rotates Bluetooth Low Energy MAC addresses via `btmgmt` |
| 35 | Hardware | Viewport Resolution Shield | Normalizes browser viewports to standard 1080p targets |
| 36 | Tor | Tor Control Port Inspector | Authenticated socket to port 9051 visualizes circuit hops |
| 37 | Tor | 1-Click Identity Rebuilder | Dispatches `SIGNAL NEWNYM` to force circuit reconstruction |
| 38 | Tor | Stream Isolation Manager | Assigns unique SOCKS5 authentication tags per process |
| 39 | Tor | Decoy Cover Traffic Generator | Emits synthetic dummy HTTPS requests to mask packet timing |
| 40 | Tor | Timing Jitter Randomizer | Introduces Poisson packet intervals to defeat traffic analysis |
| 41 | Tor | Decoy Domain Pool Rotator | Rotates dummy traffic across top 100 global domains |
| 42 | Tor | Pluggable Transports Manager | Bridge configurations for obfs4, Snowflake, and Meek |
| 43 | Tor | Bridge Fingerprint Validator | Audits Tor bridges for active connectivity and censor evasion |
| 44 | Tor | Ephemeral .onion File Drop | Spins up temporary v3 hidden service for private transfers |
| 45 | Tor | Onion Service Key Regenerator | Generates fresh ed25519 onion keys on demand |
| 46 | Tor | Secure Time Sync (sdwdate) | HTTP-based anonymous time sync over Tor defeating NTP skew |
| 47 | Tor | Tor Circuit Latency Auditor | Measures round-trip ping time through 3-hop Tor relays |
| 48 | Tor | Exit Relay Country Selector | Filters circuit selection by privacy-friendly jurisdictions |
| 49 | Tor | Strict Node Exclusion Matrix | Excludes Five-Eyes and hostile surveillance relays from circuits |
| 50 | Tor | Tor TransPort Redirection Check | Verifies local port 9040 transparent routing |
| 51 | Firewall | Strict Workstation Profile | Unconditional inbound drop, stateful outbound only |
| 52 | Firewall | Dedicated Proton Killswitch | Restricts traffic strictly to `proton+`, `pvpn+`, `wg+`, `tun+` |
| 53 | Firewall | Universal VPN Killswitch | Drops all traffic not exiting via `tun+`, `wg+`, or `proton+` |
| 54 | Firewall | Tor TransPort Profile | Enforces all system traffic to route exclusively through Tor |
| 55 | Firewall | DNS Hijack Redirector | Forces all port 53 traffic into local encrypted resolvers |
| 56 | Firewall | Dynamic Port Scan Blackhole | Null-routes IPs executing unauthorized port scans |
| 57 | Firewall | RFKILL Wireless Lockdown | Severs Wi-Fi, Bluetooth, and WWAN at kernel radio level |
| 58 | Firewall | IPv6 Null Routing Table | Sets ip6tables INPUT/OUTPUT/FORWARD to unconditional DROP |
| 59 | Firewall | Netfilter Connection Tracking Reset | Flushes conntrack table to disconnect stale TCP sessions |
| 60 | Firewall | Broadcast / Multicast Filter | Drops SSDP, mDNS, and NetBIOS broadcast packet leakage |
| 61 | Firewall | ICMP Echo Request Silencer | Drops inbound ping packets to remain invisible on LAN |
| 62 | Firewall | Bogon IP Range Filter | Blocks RFC-1918 and unallocated Martian IP ranges |
| 63 | Firewall | SYN Flood Limiter | Drops TCP SYN packets exceeding safety thresholds |
| 64 | Firewall | Outbound Quarantine Trap | Captures connection attempts from unapproved processes |
| 65 | Firewall | Native Kicksecure Rule Restorer | Intelligently restores Kicksecure native firewall scripts |
| 66 | Firewall | Whonix-Firewall Compatibility | Preserves Whonix workstation/gateway isolation rules |
| 67 | Firewall | Localhost Loopback Pinning | Strictly allows lo interface while blocking alias routing |
| 68 | Firewall | Anti-Port Knocking Sensor | Detects sequential closed-port probes |
| 69 | Hardware | BadUSB / Rubber Ducky Shield | Sysfs `authorized_default = 0` blocks new USB HID devices |
| 70 | Hardware | USB Port Controller Enumerator | Maps all PCI / root hub controllers in sysfs |
| 71 | Hardware | USBGuard Whitelist Policy | Approves trusted YubiKeys and storage tokens |
| 72 | Hardware | Keystroke Injection Throttler | Rate-limits USB scancodes to foil automated keystroke injection |
| 73 | Hardware | Webcam Hardware Driver Kill | Unloads `uvcvideo` kernel driver, locking `/dev/video*` |
| 74 | Hardware | Camera Device Inode Unlinker | Removes `/dev/video*` character devices while locked |
| 75 | Hardware | Microphone Hardware Mute | Zeroes hardware input capture gain in ALSA / PulseAudio |
| 76 | Hardware | PipeWire Source Node Mutex | Mutes modern PipeWire/WirePlumber audio sources |
| 77 | Hardware | Ultrasonic Beacon Filter | Filters audio frequencies >18kHz used by tracking beacons |
| 78 | Hardware | DMA Attack Shield | Verifies IOMMU bus protection and disables Thunderbolt |
| 79 | Hardware | Thunderbolt Controller Disabler | Powers down PCIe Thunderbolt controllers |
| 80 | Hardware | PCI Hotplug Lockdown | Disables PCI Express hotplug controllers |
| 81 | Hardware | Anti-Extraction Tamper Trigger | Lid close / AC disconnect auto-triggers emergency isolation |
| 82 | Hardware | Optical Drive Interlock | Disables CD/DVD/BluRay automated mounting |
| 83 | Storage | LUKS2 Hardware Vault Encoder | AES-XTS-plain64 512-bit military encryption on USB drives |
| 84 | Storage | Windows Stealth Mode | Makes drive 100% unrecognized and unreadable on Windows |
| 85 | Storage | App Keystore Integration | Stores 512-bit entropy keys safely in `~/.config/cyberbreak/vault_keys/` |
| 86 | Storage | Auto-Generated Random Keyfiles | Cryptographic random 64-byte keyfiles with mode `0600` |
| 87 | Storage | Vault Hardware Registry | Persists vault UUIDs, labels, and mapper mappings |
| 88 | Storage | 1-Click Vault Decoder / Unlock | Opens dm-crypt mapper using stored keys and mounts volume |
| 89 | Storage | 1-Click Vault Lock / Secure | Safely unmounts filesystem and closes cryptographic mapping |
| 90 | Storage | Unprivileged Vault Mounts | Chowns vault mountpoints to user session without root ownership |
| 91 | Storage | Host Boot Drive Safety Guard | Protects `/`, `/boot`, `/etc`, and EFI drives from formatting |
| 92 | Storage | Universal EXT4 Formatter | Fast journaled formatting with custom volume labels |
| 93 | Storage | Btrfs Drive Formatter | Modern copy-on-write filesystem formatter with checksums |
| 94 | Storage | FAT32 (vfat) Formatter | Universal compatibility formatting for legacy media |
| 95 | Storage | ExFAT Drive Formatter | High-capacity flash drive filesystem formatter |
| 96 | Storage | DoD Partition Table Sanitizer | Overwrites MBR/GPT and first 64MB with zero streams |
| 97 | Storage | Live ISO Flasher / Burner | Writes raw OS images directly to block devices |
| 98 | Storage | Unbuffered ISO Streaming | Optimized 4MB block streaming with `conv=fdatasync` |
| 99 | Storage | ISO Flasher Target Safeguard | Rejects system drives to prevent accidental host wiping |
| 100 | Storage | Kicksecure ISO Flasher Profile | Validated burning for Kicksecure and Whonix installer images |
| 101 | Storage | Tails & Arch ISO Flasher Profile | Validated burning for live forensic and minimal distributions |
| 102 | Storage | Flash Drive Geometry Auditor | Parses `lsblk` JSON for sectors, models, and hotplug buses |
| 103 | Storage | Full System Backup to USB | Live snapshot compressed archive creation on USB destination |
| 104 | Storage | User Session Backup Mode | Backs up `/home/$USER` excluding cache and trash |
| 105 | Storage | Essential Configs Backup Mode | Archives `/etc`, `/usr/local/bin`, and user homes |
| 106 | Storage | Timestamped Archive Naming | Automatically timestamps archives (`cyberbreak_backup_*`) |
| 107 | Storage | Supercharged SSD TRIM Engine | Issues `fstrim -av` discards across all mounted flash drives |
| 108 | Storage | Encrypted Volume TRIM Discard | Passes discard operations through active dm-crypt LUKS mappings |
| 109 | Storage | NVMe Namespace Block Reclaim | Reclaims unallocated physical NAND blocks on NVMe drives |
| 110 | Storage | USB Device Removal Detector | Watches block device disconnects in sysfs |
| 111 | Storage | Filesystem Dirty Buffer Flusher | Forces kernel `sync` to eliminate write-cache data loss |
| 112 | Storage | Multi-Mountpoint Scanner | Automatically discovers mounted USB folders in `/media` & `/mnt` |
| 113 | Storage | Volume Label Sanitizer | Replaces dangerous shell characters in volume names |
| 114 | Storage | Storage Armory Audit Terminal | Streams real-time format, mount, and trim progress logs |
| 115 | Storage | Vault Key Backup Export | Secure export of keystore keyfiles for disaster recovery |
| 116 | Kernel | YAMA Ptrace Memory Lock | `kernel.yama.ptrace_scope = 3` stops memory sniffing |
| 117 | Kernel | Unprivileged eBPF Disabler | `kernel.unprivileged_bpf_disabled = 1` kills microcode exploits |
| 118 | Kernel | Kernel Pointer Leak Protection | `kernel.kptr_restrict = 2` zeroes symbols in `/proc/kallsyms` |
| 119 | Kernel | Kernel Ring Buffer Lock | `kernel.dmesg_restrict = 1` restricts `dmesg` logs to root |
| 120 | Kernel | TCP SYN & RFC-1337 Protection | Shields against SYN floods and TIME-WAIT assassination |
| 121 | Kernel | Symlink & FIFO Attack Shield | `fs.protected_fifos = 2` & `fs.protected_regular = 2` |
| 122 | Kernel | Procfs Process Hiding | `hidepid=2` mount option hides processes from other users |
| 123 | Kernel | Core Dump Scrambler | `prctl(PR_SET_DUMPABLE, 0)` stops memory dumps on crash |
| 124 | Kernel | AppArmor Profile Enforcer | Parses `aa-status` and enforces all profiles in `/etc/apparmor.d/` |
| 125 | Kernel | Bubblewrap (bwrap) Sandbox | Runs untrusted binaries in isolated mount namespaces |
| 126 | Kernel | LD_PRELOAD Hijack Scanner | Audits `/etc/ld.so.preload` and dynamic link integrity |
| 127 | Kernel | Process Title Camouflage | `prctl(PR_SET_NAME)` masks processes as `[kworker/u16:2]` |
| 128 | Kernel | Self-Trace Debugger Lock | `ptrace(PTRACE_TRACEME)` prevents debuggers from attaching |
| 129 | Kernel | Kernel Module Loading Lock | `kernel.modules_disabled = 1` locks kernel module tree |
| 130 | Kernel | ASLR Maximum Entropy Enforcer | `kernel.randomize_va_space = 2` for full memory randomization |
| 131 | Shredding | Metadata Stripper (mat2) | In-app drag-and-drop sanitization of PDFs, docs, images |
| 132 | Shredding | Auto-Wiping Clipboard Guard | Zeroes clipboard contents after 15/30/60/120s or on window blur |
| 133 | Shredding | Multi-Pass File Shredder | Overwrites files with random bytes & zeroes (`shred -u -z -n 3`) |
| 134 | Shredding | Kernel RAM Cache Purge | `sync && echo 3 > /proc/sys/vm/drop_caches` |
| 135 | Shredding | Shell History Inoculator | Sets `HISTFILE=/dev/null` and cleans bash/zsh history records |
| 136 | Shredding | Journal Vacuum Sanitizer | Flushes event traces via `journalctl --vacuum-time=1s` |
| 137 | Shredding | File Timestomp Engine | Synchronizes/randomizes access, modify, and change timestamps |
| 138 | Shredding | Inode Deallocation Checker | Verifies zero residual data blocks on unlinked files |
| 139 | Shredding | Temporary Folder Scrubber | Cleanses `/tmp` and `/var/tmp` session files |
| 140 | Shredding | Thumbnail Cache Purger | Clears `~/.cache/thumbnails/` forensic artifact leaks |
| 141 | Shredding | Browser Cache Nuker | Purges cache/cookies across Tor Browser and Firefox |
| 142 | Shredding | Encrypted RAM Disk Creator | Creates ephemeral LUKS-encrypted containers inside volatile RAM |
| 143 | Settings | Control Center Preferences | Persistent configuration in `~/.config/cyberbreak/settings.json` |
| 144 | Settings | Auto-Killswitch on Boot Toggle | Automated firewall enforcement upon desktop login |
| 145 | Settings | Auto-Randomize MAC on Boot | Cycles physical MAC addresses automatically |
| 146 | Settings | Auto-Isolate on Leak Sensor | Drops connectivity if IP or DNS leak occurs |
| 147 | Settings | Strict BadUSB on Idle Switch | Automatic USB port lockdown |
| 148 | Settings | Audio Threat Alert Switch | High-voltage audible warning chimes |
| 149 | Settings | App Repository Auto-Updater | Direct GitHub API commit tracker & in-place update engine |
| 150 | Panic | Sub-50ms Network Blackout | `rfkill block all` + `nmcli off` + iptables DROP-ALL |
| 151 | Panic | Process Neutralizer | `pkill -9` on browsers, VPNs, Tor, SSH, and messengers |
| 152 | Panic | Password-Gated Master Nuke | High-contrast modal requiring authorization passphrase |
| 153 | Panic | LUKS Header Obliteration | `cryptsetup luksErase` + random block write in <100ms |
| 154 | Panic | NVMe / SSD NAND Flash Discard | Controller-level block purge via `blkdiscard -f -z` |
| 155 | Panic | Hard Kernel Crash Panic | `echo 1 > sysrq && echo c > sysrq-trigger` defeats cold-boot |

---

## 📂 Codebase Structure

```
CyberBreak/
├── cyberbreak/
│   ├── __init__.py                 # Root package metadata (Engineered by lilami)
│   ├── main.py                     # Application launcher & High-DPI setup
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py          # Left QListWidget navigation + QStackedWidget
│   │   ├── styles.py               # Complete dark modern neon QSS theme
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── status_card.py      # Metric cards with dynamic status pills
│   │   │   └── nuke_dialog.py      # Password-gated crimson emergency modal
│   │   └── pages/
│   │       ├── __init__.py
│   │       ├── dashboard_page.py   # Security status matrix & real IP leak warning
│   │       ├── leak_page.py        # Real socket IP, city/state, DNS, & IPv6 auditor
│   │       ├── spoofer_page.py     # MAC, hostname, machine-id, timezone spoofer
│   │       ├── tor_cover_page.py   # Tor control port & synthetic cover traffic
│   │       ├── firewall_page.py    # Strict, Proton VPN, & universal killswitches
│   │       ├── usbguard_page.py    # BadUSB defense, webcam & mic hardware kill
│   │       ├── usb_armory_page.py  # LUKS2 USB vault, keystore, ISO flasher, backup
│   │       ├── hardening_page.py   # Sysctl matrix & AppArmor enforcer
│   │       ├── metadata_page.py    # mat2 metadata stripper & file shredder
│   │       ├── settings_page.py    # Control center, automation switches, updater
│   │       ├── panic_page.py       # "ISOLATE NOW" & "NUKE SYSTEM" panic center
│   │       ├── desktop_page.py     # Desktop shortcut & app grid manager
│   │       └── terminal_page.py    # Live full-screen forensic audit terminal
│   ├── core/
│   │   ├── __init__.py
│   │   ├── executor.py             # Asynchronous runner with scoped run_privileged
│   │   ├── helper.py               # Hardened root helper (/usr/local/lib/cyberbreak)
│   │   ├── usb_armory.py           # LUKS2 encoder/decoder, ISO burner, TRIM, backup
│   │   ├── settings_manager.py     # Persistent settings & automation toggles
│   │   ├── updater.py              # GitHub commit tracking & repository updater
│   │   ├── desktop_integrator.py   # .desktop generation & polkit setup
│   │   ├── network_auditor.py      # Socket probes, city/state geo, Proton VPN API
│   │   ├── spoofer_engine.py       # macchanger, hostnamectl, machine-id logic
│   │   ├── tor_controller.py       # Tor stem control port & decoy cover traffic
│   │   ├── firewall_controller.py  # Iptables/nftables & Proton killswitch rules
│   │   ├── hardware_manager.py     # USBGuard sysfs & webcam/mic modprobe
│   │   ├── kernel_hardening.py     # Sysctl parameters & aa-status parser
│   │   ├── metadata_cleaner.py     # mat2 wrapper & secure shredding
│   │   ├── clipboard_guard.py      # Auto-cleaning clipboard timer
│   │   ├── isolation.py            # Fast sub-50ms network blackout
│   │   └── nuke_engine.py          # LUKS erase, blkdiscard, sysrq kernel panic
│   └── assets/
│       ├── cyberbreak.svg          # Scalable vector application icon
│       └── cyberbreak.desktop      # FreeDesktop launcher template
├── polkit/
│   └── org.cyberbreak.security.policy # Scoped helper authorization policy
├── scripts/
│   └── install.sh                  # One-step system-wide installer for sysmaint
├── one line install                # Raw single-line install command
├── one_line_install.sh             # Executable one-line script
├── requirements.txt                # Python package dependencies
├── README.md                       # Master documentation & catalog (By lilami)
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
