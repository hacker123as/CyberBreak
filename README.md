# CyberBreak

**A native Linux privacy and security workspace with an isolated browser, VPN route inspection, hardware controls and encrypted storage.**

Built by **lilami** with Python and PyQt6. Fourteen workspaces share glass-inspired surfaces, clear status cards, smooth navigation and **Ctrl+K** search. Designed for desktop-user operation, including Kicksecure's maintenance and desktop account separation.

[Install](#installation) · [Browser privacy](#browser-privacy) · [Workspace](#inside-the-workspace) · [Develop](#development) · [Troubleshoot](#troubleshooting)

![CyberBreak overview](docs/images/overview.png)

*Interface preview with illustrative audit data.*

## Browser privacy

Open **Browser privacy** for **Private browser**, **Protection report** and **Firefox profile**.

1. Connect Proton VPN and enable its native kill switch.
2. Choose **Check VPN route**. Browsing starts paused until IPv4 policy routes use an active tunnel and IPv6 is tunnel-routed or has no usable global address. Unknown IPv6 state keeps browsing paused.
3. Choose **Open PixelDefence**, or enter an HTTPS address and select **Go**.
4. Choose **Run browser checks**. **Export report** saves the runtime results and route evidence as JSON.
5. Choose **New session** to discard the browser session and start paused again.

While the built-in session is active, the route is checked every **15 seconds**. Loss of verification pauses browsing, blocks new requests and unloads the page. This browser-level gate has a polling interval. Proton's native kill switch provides system-wide disconnect protection.

Route evidence includes Linux policy routes to `1.1.1.1` and `8.8.8.8`, selected interface state and IPv6 address/route inspection. These are sampled paths, not certification of exit-server ownership, every destination or per-application split tunneling. **Network privacy** exposes the underlying evidence.

The Firewall workspace's Proton preset allows DNS and HTTPS traffic without binding every connection to a tunnel. Use Proton's native kill switch for system-wide protection; that preset is not a verified replacement.

### Strict browser policy

The embedded QtWebEngine browser creates an off-the-record profile with no persistent browsing storage or cache.

| Control | Behavior |
| --- | --- |
| Cookies | Native cookie filter rejects server cookies and script writes. |
| DNT / GPC | Sends `DNT: 1` and `Sec-GPC: 1`, with matching browser preferences. |
| Canvas | Blocks image export and pixel readback; ordinary 2D drawing remains available. |
| Graphics | WebGL disabled; graphics fingerprint APIs restricted. |
| Device APIs | Battery, network information, location, camera, microphone and sensor access restricted. |
| WebRTC / workers | Peer connections, media access and worker creation blocked. |
| Requests | HTTPS navigation and requests to the current page's hostname allowed. Cross-host requests, insecure web requests and unknown schemes blocked. Loopback HTTP is available for local tests. |
| Files / permissions | Downloads, popups, file-picker uploads, filesystem access and browser permission requests denied. |
| New session | Destroys the profile and creates a fresh in-memory session. |

Cross-host CDNs, external logins, embedded media and third-party APIs can stop working under this strict policy. It applies across visited sites and subframes.

**Protection report** attempts ten restrictions in the active page: DNT, GPC, cookie write/read, WebGL, canvas export, canvas pixel readback, battery, network information, WebRTC and workers. Results stay **Not checked** until executed. **Verified** means that restriction was observed in the current session; it is separate from a website's score.

### PixelDefence scoring

The built-in browser scored **100/100 on the live PixelDefence page** during development, with all ten runtime restriction checks passing. The live browser run used Windows QtWebEngine; Linux VPN-route handling is covered by fixture tests rather than a live Proton connection on that host. [Recorded result](docs/pixeldefence-result.json).

![Live PixelDefence result in the protected browser](docs/images/pixeldefence.png)

[PixelDefence's current implementation](https://pixeldefence.com/data-leaking-check/audit.js) subtracts **20 points** when its third-party IP/geolocation request succeeds. That includes a VPN's public exit IP. Blocking the lookup prevents its report, while the visited site still receives the connection's exit IP.

It also subtracts **15 points** for any available canvas hash, without comparing users. Firefox's randomized hash can still be labeled unique; the built-in browser blocks extraction instead.

A checker score follows that checker's rules. It is not proof of anonymity or a complete VPN leak test. Read the runtime report and route evidence alongside the [website audit](https://pixeldefence.com/data-leaking-check/).

### Firefox fallback

The **Firefox profile** tab applies **49 real preferences** for cookie rejection, DNT/GPC, fingerprinting resistance, WebGL/WebRTC restrictions, tracking protection and reduced local persistence, using [Mozilla's privacy controls](https://firefox-source-docs.mozilla.org/toolkit/components/antitracking/anti-tracking/etp-matrix/index.html).

- **Prepare profile** writes only under `~/.config/cyberbreak/browser_profile/`.
- **Launch Firefox** requests a fresh IPv4/IPv6 route check before opening that profile separately.
- **Reset managed settings** removes CyberBreak's `user.js` and persisted managed entries from `prefs.js`, preserving unrelated settings, files and downloads.

Existing Firefox and Tor profiles remain intact. Ownership, redirect and external-edit checks protect other profiles. Close the managed Firefox instance before preparing or resetting it.

Firefox uses its own policy and does not inherit the embedded browser's same-host filter or route-loss pause. Its canvas hash may still be flagged. Use Proton's native kill switch for the external browser.

## Inside the workspace

| Workspace | Tools |
| --- | --- |
| Overview | Network identity, routing, kernel and hardware status. |
| Network privacy | Public exit identity, configured DNS, policy routes and IPv6 inspection. |
| Browser privacy | Strict private browser, runtime checks and isolated Firefox profile. |
| Device identity | MAC address, hostname, machine IDs and timezone. |
| Tor & traffic | Circuits, identity renewal and optional background HTTPS traffic. |
| Firewall | Workstation, VPN and Proton VPN profiles; iptables inspection/reset. |
| Hardware & ports | USB authorization, listening ports, webcam, microphone and Bluetooth. |
| USB & storage | LUKS2 vaults, formatting, ISO flashing, archives and TRIM. |
| Kernel hardening | Selected sysctl settings and AppArmor controls. |
| Metadata & files | Metadata cleaning, selected-file removal and cache controls. |
| Preferences | Local settings, clipboard timer and update checks. |
| Emergency | Isolation/process shutdown and separately confirmed drive/kernel operations. |
| Desktop | Shortcuts and autostart. |
| Audit terminal | Timestamped activity and command output. |

CyberBreak uses existing VPN and Tor services; it does not install or connect a VPN client. A visible public IP is reported as an observation, not an automatic ISP leak. DNS inspection reads `/etc/resolv.conf`.

Use **Ctrl+K**, arrow keys and Enter to open a tool; Escape dismisses search. The top-bar motion control reduces animation and remembers your choice.

## Installation

Requires a Linux graphical session, Python **3.10+**, administrator access for installation, and the dependencies in [requirements.txt](requirements.txt): **PyQt6**, **PyQt6-WebEngine**, **requests** and **stem**.

On Debian, Ubuntu or Kicksecure, use an administrator terminal; use `sysmaint` on Kicksecure:

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/hacker123as/CyberBreak.git
cd CyberBreak
sudo bash scripts/install.sh
```

On Arch Linux, install Git, clone the repository and run the same installer. The script selects its package-manager branch.

Sign out and back in to refresh group membership, then launch from the application menu or a normal desktop-user terminal:

```bash
cyberbreak
```

The GUI runs as the desktop user. Supported system actions use a root-owned helper. The installer creates the `cyberbreak` group, enrolls regular users with UIDs 1000–59999, and installs sudo/Polkit authorization for its supported actions.

| Location | Installed component |
| --- | --- |
| `/opt/cyberbreak` | Root-owned source. |
| `/usr/local/bin/cyberbreak` | Launcher. |
| `/usr/local/lib/cyberbreak/cyberbreak-helper` | Privileged dispatcher; also under `/usr/libexec/cyberbreak/`. |
| `/etc/sudoers.d/cyberbreak` and Polkit policy/rules | Group authorization. |
| `/usr/share/applications/cyberbreak.desktop` | Menu entry. |

WebEngine packages: `python3-pyqt6.qtwebengine` on Debian-based distributions; `python-pyqt6-webengine` on Arch. Missing WebEngine leaves the other workspaces available. Linux system actions are not supported on Windows or macOS.

The installer attempts common networking/storage utilities and tolerates some package failures. Optional features may need `mat2` / `exiftool` / Pillow, AppArmor utilities, `exfatprogs`, a configured USBGuard service, `pactl` / `amixer`, or a Tor daemon with an authenticated control socket.

## Data and system actions

| Local data | Location |
| --- | --- |
| Preferences | `~/.config/cyberbreak/settings.json` |
| Firefox profile | `~/.config/cyberbreak/browser_profile/` |
| Vault registry / keys | `~/.config/cyberbreak/vault_registry.json` / `vault_keys/` |
| Vault mountpoints | `/media/$USER/<vault-label>` |
| USB archives / privacy reports | User-selected destination. |

Vaults use LUKS2/EXT4 and generated 64-byte keyfiles with mode `0600`. Preserve the registry and keys when moving installations; changed drive paths may require registry updates. USB backups are timestamped `.tar.gz` file archives.

Firewall profiles replace iptables configuration. Formatting, flashing and wiping change the selected drive. Emergency isolation stops selected processes; the separate destructive confirmation can erase drive metadata and crash the kernel.

Identity checks can contact Proton, Mullvad, ifconfig.me and ipify; update checks use GitHub. Optional background traffic uses the host's route. The private browser contacts permitted visited sites; exported reports are local.

Several automation settings are stored without implemented boot/idle/leak-triggered actions. Use explicit system controls. The clipboard timer works while CyberBreak is running; its default is 30 seconds.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m cyberbreak.main
```

Debian-based systems may need `python3-venv`. Source launches provide user-level features; privileged actions require the installed helper.

UI pages and shared widgets live under `cyberbreak/ui/`; controllers under `cyberbreak/core/`. `executor.py` dispatches supported privileged actions through `helper.py`. Automated tests are under `tests/`.

Run from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q cyberbreak tests
bash -n scripts/install.sh
```

WebEngine integration tests use a loopback server to attempt API access, cookies, request filtering and session resets. A functioning QtWebEngine runtime is required; missing WebEngine produces explicit skips. Syntax checks and skipped integration tests do not establish browser protection. Linux integrations need their corresponding services/devices.

For UI work, verify keyboard navigation, scrolling, loading/error states and confirmations at normal and compact window sizes.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Private browser unavailable | Install `PyQt6-WebEngine` for the launching interpreter, or the distro package above. |
| Browsing remains paused | Connect Proton VPN and inspect the policy-route evidence. A named/down interface alone is insufficient. |
| Missing images/login/media | Strict cookies, cross-host requests, media and popup restrictions can affect the page. |
| Firefox reset refused | Close the managed instance; inspect the lock, ownership or edited-file error. |
| Display connection fails | Launch as the active desktop user; check `DISPLAY` / `WAYLAND_DISPLAY`. |
| Helper denied | Reinstall from the maintenance account, sign in again, and check `id -nG`. |
| Identity/Tor/vault unavailable | Inspect endpoint access, Tor control authentication, or the registry/key/device path. |
| Update needs maintenance | Update the source as the maintenance user, reinstall and restart. |

Check the installed interpreter:

```bash
/usr/bin/python3 -c "from PyQt6 import QtWidgets, QtWebEngineWidgets; import requests, stem; print('Dependencies available')"
```

Refresh an existing installation after saving local changes:

```bash
git pull --ff-only origin main
sudo bash scripts/install.sh
```
