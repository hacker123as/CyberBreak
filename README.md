# CyberBreak: Hardened Security, Anonymity & Anti-Forensics Fortress

[![Target OS: Kicksecure Linux](https://img.shields.io/badge/Target_OS-Kicksecure_Linux-00ff66?style=for-the-badge&logo=linux&logoColor=white)](https://www.kicksecure.com/)
[![Architecture: PyQt6](https://img.shields.io/badge/GUI-PyQt6_Dark_QSS-00b8ff?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Security: Kernel Netfilter & Polkit](https://img.shields.io/badge/Privileges-Polkit_pkexec-ff3344?style=for-the-badge&logo=debian&logoColor=white)](https://wiki.debian.org/)
[![VPN: Proton VPN Integration](https://img.shields.io/badge/VPN-Proton_VPN_Verified-6d4aff?style=for-the-badge&logo=protonvpn&logoColor=white)](https://protonvpn.com/)

CyberBreak is a defensive, anti-tracking, and anti-forensics workstation suite architected specifically for **Kicksecure Linux** and hardened Debian environments. It directly interfaces with Linux kernel subsystems via Netlink sockets, sysfs, procfs, iptables/nftables, AppArmor, D-Bus, and raw block device ioctls.

---

## ⚡ Instant Console / SSH Installation (One-Liner)

Copy and paste this command directly into your terminal or SSH console on Kicksecure, Debian, or Ubuntu:

```bash
sudo apt-get update -y && sudo apt-get install -y git curl && rm -rf /tmp/cyberbreak_install && git clone https://github.com/hacker123as/CyberBreak.git /tmp/cyberbreak_install && sudo bash /tmp/cyberbreak_install/scripts/install.sh && rm -rf /tmp/cyberbreak_install
```

### What This Installer Does:
- **System Dependencies**: Installs `python3-pyqt6`, `python3-requests`, `python3-stem`, `macchanger`, `rfkill`, `iptables`, `network-manager`, `ethtool`, `cryptsetup`, and `polkit-1`.
- **System-Wide Multi-Account Deployment (`/opt/cyberbreak`)**: Installs the app bundle with global read/execute permissions (`755`) so **every user account on the machine can run it**.
- **Global Executable (`/usr/local/bin/cyberbreak`)**: Any user can launch it by simply typing `cyberbreak`.
- **Desktop Application Grid**: Deploys `/usr/share/applications/cyberbreak.desktop` into the Whisker Menu, Kicksecure Application Finder, GNOME Dash, and KDE Kickoff.
- **Desktop Shortcut**: Places `cyberbreak.desktop` directly on the user's desktop, marks it executable (`chmod +x`), and trusted (`gio set ... metadata::trusted true`).
- **Polkit Privilege Elevation**: Deploys `/usr/share/polkit-1/actions/org.cyberbreak.security.policy` so unprivileged desktop users are prompted for the native graphical password modal without requiring terminal hacks.

---

## 🛡️ Complete Feature Catalog (73+ Subsystems)

### A. Network & Leak Detection Arsenal
1. **Multi-Endpoint External IPv4/IPv6 Verifier**: Triple-redundant checks via Proton VPN API, Mullvad, ifconfig.me, and ipify.
2. **Proton VPN Real-Time Connection Auditor**: Directly queries official Proton VPN endpoints (`https://api.protonvpn.ch/vpn/location`) and audits `proton0`, `pvpn*`, and `wg-proton*` interfaces.
3. **Autonomous ASN & ISP Ownership Resolver**: Automatically detects Proton AG ASN and exit node status.
4. **Live Default Gateway Route Auditor**: Parses `/proc/net/route` and `ip -j route show default` in real time.
5. **VPN/Tor Gateway Bypass Sentinel**: Warns immediately if packets leave raw unencrypted adapters (`eth0`, `wlan0`) instead of tunnel interfaces (`proton+`, `tun+`, `wg+`).
6. **Raw AF_INET6 Socket Probe**: Tests raw IPv6 socket creation and audits `/proc/net/if_inet6` for leaks bypassing IPv4-only killswitches.
7. **Nonce-Based DNS Leak Tester**: Dispatches unique UUID lookups to detect upstream transparent ISP DNS hijacking.
8. **Active DNS Resolver Ownership Auditor**: Validates active nameservers in `/etc/resolv.conf` against Zero-Knowledge and Proton DNS.
9. **WebRTC STUN Packet Analyzer**: Scans UDP port 3478 socket exposure to thwart browser real-IP leaks.
10. **DNS-over-HTTPS / DNS-over-TLS Switcher**: Switcher profile support for Proton, Mullvad, and Quad9.
11. **DNSSEC Cryptographic Validation Check**: Verifies cryptographic RRSIG DNS record integrity.
12. **Covert Channel & ICMP Tunneling Detector**: Monitors abnormal ICMP payload sizing via AF_PACKET.
13. **Network Interface MTU Normalizer**: Standardizes packet MTU sizes to defeat packet-size fingerprinting.

### B. Hardware, Identity & RF Spoofing
14. **Physical Network Adapter MAC Randomizer**: Automated down -> `macchanger -r` -> up -> NetworkManager reapply cycle.
15. **Vendor-Specific OUI Pool Spoofing**: Emulates legitimate Dell, Intel, or Apple network card vendor pools.
16. **Wi-Fi Probe Request Randomizer**: Enables `wifi.scan-rand-mac-address = yes` in NetworkManager to thwart location trackers.
17. **Dynamic OEM Hostname Generator**: Rotates workstation name via `hostnamectl` and syncs `/etc/hosts`.
18. **D-Bus & Linux Machine-ID Auto-Reseeder**: Zeroes and re-generates `/etc/machine-id` using `/dev/urandom`.
19. **DMI / SMBIOS Hardware UUID Auditor**: Inspects `/sys/devices/virtual/dmi/id/*` for persistent tracking serials.
20. **UTC Timezone & Locale Cloaking**: Sets timezone to UTC (`timedatectl set-timezone UTC`) to kill JavaScript clock fingerprinting.
21. **Bluetooth Low Energy (BLE) Address Rotator**: Rotates BLE MAC addresses via `btmgmt`.
22. **Screen Viewport Normalizer**: Flags standard 1080p target viewports to defeat browser canvas and display fingerprinting.

### C. Anonymity, Tor & Traffic Obfuscation
23. **Tor Control Port Circuit Inspector**: Authenticated socket to port 9051 visualizes Entry Guard, Middle, and Exit hops.
24. **One-Click Tor New Identity Trigger**: Fires `SIGNAL NEWNYM` to rebuild all circuits on demand.
25. **Per-Application Tor Stream Isolation**: Configures unique SOCKS5 authentication tags so apps never share Tor circuits.
26. **Background Decoy Cover Traffic Generator**: Emits dummy HTTPS requests with randomized delays, packet sizes, and user-agents to disrupt ISP timing attacks.
27. **Anti-Censorship Pluggable Transports**: Bridge configurations for obfs4, Snowflake, and Meek.
28. **Ephemeral Tor Onion Service (.onion) File Drop**: Spins up temporary v3 hidden services for private transfers.
29. **Secure Time Sync via sdwdate**: HTTP-based anonymous time sync over Tor, defeating NTP clock-skew fingerprinting.

### D. Hardened Firewall & Killswitch Profiles
30. **Strict Workstation Firewall Profile**: Unconditional incoming packet drop, stateful outbound only.
31. **Dedicated Proton VPN Killswitch Profile**: Strictly locks traffic to `proton+`, `pvpn+`, `wg+`, `tun+` and WireGuard UDP `51820`.
32. **Universal VPN/WireGuard Killswitch Profile**: Drops all traffic not exiting via `tun+`, `wg+`, or `proton+`.
33. **Tor-Only TransPort Profile**: Enforces all system traffic to route exclusively through local Tor (9040/9050).
34. **Outbound Port 53 Hijack Redirector**: Redirects unencrypted DNS queries to local encrypted resolvers.
35. **Dynamic Port Scan Blackhole**: Null-routes IP addresses executing unauthorized SYN scans.
36. **RFKILL Wireless Lockdown**: Severs Wi-Fi, Bluetooth, and WWAN at the kernel radio subsystem level.

### E. Hardware Interception & Physical Defenses
37. **BadUSB / Rubber Ducky Blocker**: Enforces sysfs `authorized_default = 0` to block untrusted USB HID keyboards/mice.
38. **USBGuard D-Bus Policy Whitelist Manager**: Permits approving trusted YubiKeys and storage tokens.
39. **USB Keystroke Injection Throttler**: Rates-limits USB scancodes to foil automated keystroke injection payloads.
40. **Hardware Webcam Kill Switch**: Unloads `uvcvideo` kernel driver, locking down `/dev/video*`.
41. **Hardware Microphone Mute**: Zeroes input capture gain in ALSA, PulseAudio, and PipeWire.
42. **Acoustic Ultrasonic Beacon Filter**: Filters audio frequencies >18kHz used by cross-device tracking beacons.
43. **DMA (Direct Memory Access) Attack Shield**: Verifies IOMMU bus protection and locks down Thunderbolt controllers.
44. **Anti-Physical Extraction Tamper Trigger**: Detects lid close / AC power disconnection to trigger instant isolation.

### F. Kernel Hardening & Process Defense
45. **YAMA Ptrace Memory Sniffing Lock**: `kernel.yama.ptrace_scope = 3` stops debuggers from inspecting process memory.
46. **Unprivileged eBPF Disabler**: `kernel.unprivileged_bpf_disabled = 1` kills microcode exploit vectors.
47. **Kernel Pointer Leak Protection**: `kernel.kptr_restrict = 2` zeroes kernel memory symbols in `/proc/kallsyms`.
48. **Kernel Ring Buffer Lock**: `kernel.dmesg_restrict = 1` restricts `dmesg` logs to root.
49. **TCP SYN-Cookie & RFC-1337 Protection**: Shields against SYN floods and TIME-WAIT assassination attacks.
50. **Procfs Process Hiding**: Enforces `hidepid=2` mount options so users only see their own processes.
51. **Core Dump Memory Scrambler**: `prctl(PR_SET_DUMPABLE, 0)` stops memory dumps on application crashes.
52. **AppArmor Profile Matrix & Enforcer**: Real-time `aa-status` parser with 1-click enforcement across all profiles.
53. **Bubblewrap (`bwrap`) Ephemeral Sandbox**: GUI launcher to run untrusted binaries in isolated mount namespaces.
54. **LD_PRELOAD Hijack Scanner**: Audits `/etc/ld.so.preload` and dynamic linker hooks.
55. **Process Title Camouflage**: `prctl(PR_SET_NAME)` masks running processes as `[kworker/u16:2]`.
56. **Self-Trace Debugger Lock**: `ptrace(PTRACE_TRACEME)` prevents forensic debuggers from attaching.

### G. Anti-Forensics, Memory Sanitizing & Shredding
57. **In-App Drag-and-Drop Metadata Stripper**: Cleans PDF, Office documents, and EXIF image metadata via `mat2`.
58. **Auto-Wiping Clipboard Guard**: Clears clipboard contents after 15, 30, or 60 seconds or on window defocus.
59. **Multi-Pass Military File Shredder**: Overwrites files with random bytes and zeroes (`shred -u -z -n 3`) before unlinking inodes.
60. **Kernel Memory Buffer & RAM Cache Purge**: `sync && echo 3 > /proc/sys/vm/drop_caches`.
61. **Shell History Neutralizer**: Configures `HISTFILE=/dev/null` and cleans bash/zsh history records.
62. **System Journal Vacuum Sanitizer**: Flushes forensic traces via `journalctl --vacuum-time=1s`.
63. **File Timestomp Engine**: Synchronizes/randomizes access, modification, and change timestamps.
64. **Encrypted RAM Disk Creator**: Creates ephemeral LUKS-encrypted containers inside volatile RAM tmpfs.

### H. Emergency "KILL IT ALL" System
65. **Tier 1: Sub-50ms Network Blackout ("ISOLATE NOW")**:
    - `rfkill block all` kills wireless transmitters at kernel level.
    - Shuts down NetworkManager (`nmcli networking off`) and takes down all physical NICs.
    - Flushes iptables/ip6tables and applies unconditional `DROP` policies.
    - Terminates sensitive binaries immediately (`pkill -9` on browsers, VPNs, Tor, SSH, messengers).
66. **Tier 2: Password-Gated Master Crypto-Nuke ("NUKE SYSTEM")**:
    - High-contrast crimson security modal requiring confirmation passphrase (e.g. `1234567890` or root password).
    - **LUKS Header Obliteration (<100ms)**: Destroys keyslots via `cryptsetup luksErase` and random `dd` overwrite on the first 16MB of block devices, rendering AES ciphertext permanently irrecoverable.
    - **NVMe / SSD Flash Purge**: Issues hardware `blkdiscard -f -z` across all physical storage devices.
    - **Partition Table Zapping**: `sgdisk --zap-all` wipes MBR and GPT records.
    - **Immediate Intentional Kernel Panic**: Fires `sync`, enables sysrq (`echo 1 > /proc/sys/kernel/sysrq`), and triggers an immediate hard crash (`echo c > /proc/sysrq-trigger`) to purge memory before DRAM decay can be cold-boot dumped.

### I. Native Desktop & System Integration
67. **Live Monospace Forensic Audit Terminal**: Captures all stdout/stderr streams with millisecond timestamps into a dark terminal.
68. **FreeDesktop Application Grid Integration**: `/usr/share/applications/cyberbreak.desktop` registers into all system menus.
69. **User Desktop Launcher**: Direct shortcut on `~/Desktop/cyberbreak.desktop` marked trusted and executable.
70. **Polkit Graphical Elevation**: Native Kicksecure password prompt (`org.cyberbreak.security.policy`).
71. **Scalable Vector & High-DPI Icons**: SVG and 256x256 PNG assets installed in `/usr/share/icons/hicolor/`.
72. **System Boot Autostart**: 1-click toggle to run protection suite on login.
73. **In-App Desktop Manager**: Manage launchers, shortcuts, and autostart directly from the GUI.

---

## 📂 Codebase Architecture

```
CyberBreak/
├── cyberbreak/
│   ├── __init__.py
│   ├── main.py                     # Entry point & QApplication setup
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py          # Left QListWidget sidebar + QStackedWidget
│   │   ├── styles.py               # Modern dark QSS (#121214, #1c1c1f, #00ff66)
│   │   ├── widgets/
│   │   │   ├── status_card.py      # Reusable metrics/status card widget
│   │   │   └── nuke_dialog.py      # Password-gated crimson emergency modal
│   │   └── pages/
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
│       ├── cyberbreak.svg          # Vector icon
│       └── cyberbreak.desktop      # Desktop entry template
├── polkit/
│   └── org.cyberbreak.security.policy # Native Polkit root authorization policy
├── scripts/
│   └── install.sh                  # One-step system-wide installer
├── requirements.txt                # Python dependencies
├── README.md                       # Documentation & feature catalog
└── .gitignore
```

---

## 🚀 Manual Run & Testing

To launch CyberBreak manually from source:

```bash
# Install dependencies
sudo apt-get install -y python3-pyqt6 python3-requests python3-stem macchanger rfkill iptables

# Launch application
python3 -m cyberbreak.main
```

To run privileged operations, launch via `pkexec`:
```bash
pkexec python3 -m cyberbreak.main
```
Or use the global binary created by the installer:
```bash
cyberbreak
```
