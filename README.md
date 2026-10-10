# CyberBreak

**A native Linux control center for privacy, network inspection, hardware controls, and encrypted storage.**

Built by **lilami** with Python and PyQt6. CyberBreak brings system tools into one desktop workspace, with a glass-inspired interface, rounded surfaces, clear status cards, and smooth navigation. It is designed around Kicksecure's maintenance and desktop account separation.

[Install](#installation) · [Explore the tools](#inside-the-workspace) · [Develop](#development) · [Troubleshoot](#troubleshooting)

![CyberBreak overview with glass surfaces, network status cards, and quick actions](docs/images/overview.png)

*Interface preview with illustrative audit data.*

## Inside the workspace

| Area | What you can do |
| --- | --- |
| Overview | Inspect public network identity, route information, and system status in one place. |
| Network inspection | Query public IP information, read configured DNS resolvers, inspect the default route, and check local IPv6 addresses. |
| Identity | Randomize interface MAC addresses and the hostname, reseed machine IDs, and switch the system timezone to UTC. |
| Tor | Inspect the local daemon and circuit hops, request a new identity through the control socket, and start or stop background HTTPS requests. |
| Firewall | Apply workstation, VPN, or Proton VPN profiles; inspect active iptables rules; reset the firewall. |
| Hardware and ports | Inspect USB devices and listening ports, change USB authorization, block storage drivers, and control webcam, microphone, and Bluetooth state. |
| USB and storage | Create LUKS2 vaults with app-managed keyfiles, unlock or lock registered vaults, format drives, flash ISO images, archive files to USB, and run filesystem TRIM. |
| Kernel | Audit selected sysctl values, apply their configured hardening values, inspect AppArmor, and enforce available profiles. |
| Files and clipboard | Clean file metadata, overwrite and remove selected files, drop kernel caches, and clear copied text after a timer. |
| Preferences | Save settings, check the repository for updates, and manage desktop shortcuts and autostart. |
| Emergency controls | Disable networking and terminate selected applications; open the separate confirmation dialog for drive destruction and kernel panic. |
| Activity | View timestamped application and command output in the audit terminal. |

The application uses the host's existing VPN and Tor services. It does not install or connect a VPN client. Network labels come from local interfaces, routing information, and public endpoint responses; they are useful diagnostic signals rather than a complete traffic audit. DNS inspection reads `/etc/resolv.conf`.

## Requirements

- A Linux graphical session with Python **3.10+**.
- **PyQt6 6.5+**, **requests 2.28+**, and **stem 1.8+**, as listed in [requirements.txt](requirements.txt).
- Administrator access for system installation and helper configuration.
- The relevant Linux utilities for each system feature.

The installer has package-manager branches for Debian, Ubuntu, Kicksecure, and Arch Linux. Linux operations depend on `/proc`, `/sys`, and distribution services; Windows and macOS are not operational targets.

## Installation

On Debian, Ubuntu, or Kicksecure, open an administrator terminal. Use the `sysmaint` account on Kicksecure.

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/hacker123as/CyberBreak.git
cd CyberBreak
sudo bash scripts/install.sh
```

On Arch Linux, install Git with your package manager, clone the same repository, and run `scripts/install.sh` with administrator privileges. The script chooses its package-manager branch automatically.

After installation, sign out and back in so the desktop session receives its updated group membership. Launch **CyberBreak** from the application menu, the desktop shortcut, or a normal desktop-user terminal:

```bash
cyberbreak
```

The GUI runs as the desktop user. Only supported system actions are dispatched to the privileged helper.

### What the installer configures

| Location | Purpose |
| --- | --- |
| `/opt/cyberbreak` | System-wide application source, owned by root. |
| `/usr/local/bin/cyberbreak` | Launcher for the current user's graphical session. |
| `/usr/local/lib/cyberbreak/cyberbreak-helper` | Root-owned system-action dispatcher. |
| `/usr/libexec/cyberbreak/cyberbreak-helper` | Alternate helper path. |
| `/etc/sudoers.d/cyberbreak` | Passwordless helper invocation for the `cyberbreak` group. |
| `/usr/share/polkit-1/actions/org.cyberbreak.security.policy` | Helper authorization policy. |
| `/etc/polkit-1/rules.d/50-cyberbreak.rules` | Group authorization rule, when the rules directory exists. |
| `/usr/share/applications/cyberbreak.desktop` | Application-menu entry. |
| `/usr/share/icons/hicolor/scalable/apps/cyberbreak.svg` | Application icon. |

The installer creates the `cyberbreak` group and enrolls regular accounts with UIDs from 1000 through 59999. It also places desktop shortcuts in existing `/home/*/Desktop` directories and `/etc/skel/Desktop`. Group membership authorizes the helper's supported actions, including storage changes and emergency operations.

Some package-installation failures are tolerated by the script. If a feature reports a missing command, check that feature's utilities even if the installer printed its completion message.

### Feature-specific utilities

The installer attempts to provide common networking and storage tools, including NetworkManager, iptables, rfkill, macchanger, cryptsetup, and filesystem utilities. Additional tools may be needed:

| Feature | Utilities or service |
| --- | --- |
| Metadata cleanup | `mat2`, with `exiftool` and Pillow as fallbacks. |
| AppArmor inspection and enforcement | AppArmor and `aa-status` / `aa-enforce`. |
| ExFAT formatting | `mkfs.exfat` from `exfatprogs`. |
| Tor circuits and identity renewal | A running Tor service with an accessible, authenticated control socket or port. |
| USBGuard integration | A configured USBGuard service; sysfs authorization is also used. |
| Microphone controls | `pactl` and/or `amixer` for the active audio session. |

For the first three areas on Debian-based systems:

```bash
sudo apt-get install -y mat2 libimage-exiftool-perl python3-pil apparmor apparmor-utils exfatprogs
```

## Using CyberBreak

Start with the overview, then open the relevant workspace from the sidebar. Refresh the device, port, or network information before choosing an action. The activity terminal records command execution and reported errors.

Press **Ctrl+K** to find a tool by name or function. Use the arrow keys and Enter to open a result, or Escape to dismiss the search. The motion control in the top bar reduces interface animation and remembers your choice between sessions.

Firewall profiles replace existing iptables configuration. Storage formatting, ISO flashing, and wiping change the selected device's contents. The emergency isolation action also stops selected processes; the separate destructive action can erase drive metadata and deliberately crash the kernel.

### Encrypted vaults and backups

Vault creation generates a 64-byte keyfile, formats the target with LUKS2, creates an EXT4 filesystem, and records its device and mount information. Registered vaults use those local keyfiles for subsequent unlocks.

| User data | Location |
| --- | --- |
| Preferences | `~/.config/cyberbreak/settings.json` |
| Vault registry | `~/.config/cyberbreak/vault_registry.json` |
| Vault keys | `~/.config/cyberbreak/vault_keys/` |
| Vault mountpoints | `/media/$USER/<vault-label>` |
| USB backup archives | Selected destination under `/media/` or `/mnt/` |

Vault keyfiles are created with mode `0600`. Preserve the keys and registry when moving to a new installation. The registry stores device paths, so a drive that changes its `/dev/` name may require its record to be updated.

USB backups are timestamped `.tar.gz` archives. Home mode archives the user's home while excluding cache and trash; configuration mode archives `/etc`, `/usr/local/bin`, and the user's home. These are file archives, not complete bootable disk images or consistent filesystem snapshots.

### Network requests and preferences

Public identity checks can contact Proton, Mullvad, ipapi, ifconfig.me, and ipify. Update checks use GitHub. The optional decoy generator sends HTTPS requests to a built-in list of public websites using the host's configured network route.

Preferences are persisted locally. Several automation switches are currently stored without an implemented boot, idle, or leak-triggered action. Use the corresponding explicit controls for system changes. The clipboard guard clears copied text after your selected interval while the app is running: 15 seconds, 30 seconds, one minute, or two minutes. Saving a new interval applies it immediately; the default is 30 seconds.

## Development

For an isolated source checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m cyberbreak.main
```

On Debian-based systems, `python3-venv` may be needed to create the environment. A source launch provides the GUI and user-level tools; administrator actions still require the installed helper and authorization configuration.

### Project layout

```text
cyberbreak/
  main.py
  assets/
  ui/
    main_window.py
    styles.py
    widgets/
    pages/
  core/
    executor.py
    helper.py
    network_auditor.py
    usb_armory.py
    settings_manager.py
    ...
scripts/install.sh
polkit/org.cyberbreak.security.policy
requirements.txt
```

The UI pages call focused controllers in `core/`. Worker threads handle longer inspections and commands, Qt signals carry results to the interface, and the shared logger feeds the activity view. `executor.py` dispatches privileged actions through the helper, trying noninteractive sudo before Polkit. `helper.py` maps supported action names to Linux operations.

### Validation

Run syntax checks from the repository root:

```bash
python3 -m compileall -q cyberbreak
bash -n scripts/install.sh
```

For UI changes, launch from source and inspect every page, navigation transition, scroll area, table, and confirmation dialog at normal and compact window sizes. Verify keyboard navigation, disabled and loading states, readable status colors, and command errors. System integrations need a Linux session with the relevant services and devices; syntax checks alone do not validate their behavior. This repository does not currently include an automated test suite.

## Troubleshooting

| Symptom | Check or fix |
| --- | --- |
| `No module named PyQt6` | Install the Python requirements for the interpreter used to launch the app. The installed launcher uses `/usr/bin/python3`. |
| Qt cannot connect to the display | Launch from the active graphical desktop as its normal user. Check `DISPLAY` or `WAYLAND_DISPLAY` in that session. |
| Helper missing or action denied | Re-run installation from the maintenance account, then sign out and back in. Check `id -nG` for `cyberbreak` membership. |
| Polkit prompt does not appear | Confirm `pkexec` is installed and the desktop has a running authentication agent. Read the command error in the activity terminal. |
| Network identity is unknown | Check connectivity, current firewall rules, and access to the public lookup endpoints. |
| VPN status does not match expectations | Compare interface names and routing with the VPN client's own status. Provider and interface detection is heuristic. |
| Tor is running but circuits are unavailable | Check the control socket under `/run/tor/` or `/var/run/tor/`, localhost port 9051 or 9151, and cookie access. |
| Vault unlock cannot find the key or device | Check the registry, local keyfile, and current device path with `lsblk`. |
| Metadata cleanup or formatting fails | Confirm the requested utility is installed and read its reported error. |
| Update button shows maintenance instructions | The system installation is root-owned. Update the source checkout as the maintenance user, rerun the installer, and restart the app. |

To inspect the installed Python dependencies:

```bash
/usr/bin/python3 -c "import PyQt6, requests, stem; print('Python dependencies available')"
```

To refresh a system installation from an existing checkout, run these commands as the maintenance user after saving any local changes:

```bash
git pull --ff-only origin main
sudo bash scripts/install.sh
```
