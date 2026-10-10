#!/usr/bin/env python3
"""
CyberBreak Narrowly Scoped Privileged Helper
Target: Kicksecure Linux / Debian / Arch
Security: Only accepts predefined, strictly validated actions.
Never executes arbitrary shell input. Owned by root:root, mode 0755.
"""

import sys
import os
import re
import glob
import secrets
import subprocess
from typing import List, Tuple

ALLOWED_ACTIONS = [
    "mac-randomize",
    "hostname-randomize",
    "machine-id-reseed",
    "timezone-utc",
    "firewall-strict",
    "firewall-vpn",
    "firewall-proton",
    "firewall-reset",
    "usb-lockdown",
    "webcam-toggle",
    "sysctl-harden",
    "apparmor-status",
    "apparmor-enforce",
    "purge-ram",
    "emergency-isolate",
    "panic-nuke"
]

def run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    """Executes a command safely without shell=True."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def action_mac_randomize(args: List[str]) -> int:
    if len(args) < 1:
        print("ERROR: Interface required", file=sys.stderr)
        return 2
    iface = args[0]
    if not re.match(r"^[a-zA-Z0-9_\-\.]{1,32}$", iface) or iface == "lo":
        print(f"ERROR: Invalid interface name '{iface}'", file=sys.stderr)
        return 3
    if not os.path.exists(f"/sys/class/net/{iface}"):
        print(f"ERROR: Interface '{iface}' does not exist", file=sys.stderr)
        return 4

    # Down
    run_cmd(["ip", "link", "set", "dev", iface, "down"])
    # Randomize
    code, out, err = run_cmd(["macchanger", "-r", iface])
    if code != 0:
        # Fallback to manual locally-administered unicast MAC
        rand_mac = "02:%02x:%02x:%02x:%02x:%02x" % tuple(secrets.token_bytes(5))
        run_cmd(["ip", "link", "set", "dev", iface, "address", rand_mac])
    # Up
    run_cmd(["ip", "link", "set", "dev", iface, "up"])
    # NM reapply
    run_cmd(["nmcli", "device", "reapply", iface])
    print(f"OK: MAC randomized for {iface}")
    return 0

def action_hostname_randomize(args: List[str]) -> int:
    if len(args) < 1:
        print("ERROR: Hostname required", file=sys.stderr)
        return 2
    new_host = args[0]
    if not re.match(r"^[a-zA-Z0-9\-]{1,63}$", new_host):
        print(f"ERROR: Invalid hostname '{new_host}'", file=sys.stderr)
        return 3

    code, out, err = run_cmd(["hostnamectl", "set-hostname", new_host])
    if code != 0:
        try:
            with open("/etc/hostname", "w") as f:
                f.write(new_host + "\n")
        except Exception as e:
            print(f"ERROR: Failed writing /etc/hostname: {e}", file=sys.stderr)
            return 4

    # Sync /etc/hosts 127.0.1.1
    try:
        if os.path.exists("/etc/hosts"):
            with open("/etc/hosts", "r") as f:
                lines = f.readlines()
            new_lines = []
            found = False
            for line in lines:
                if line.startswith("127.0.1.1"):
                    new_lines.append(f"127.0.1.1\t{new_host}\n")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"127.0.1.1\t{new_host}\n")
            with open("/etc/hosts", "w") as f:
                f.writelines(new_lines)
    except Exception:
        pass

    print(f"OK: Hostname set to {new_host}")
    return 0

def action_machine_id_reseed(args: List[str]) -> int:
    new_id = secrets.token_hex(16)
    try:
        with open("/etc/machine-id", "w") as f:
            f.write(new_id + "\n")
        if os.path.exists("/var/lib/dbus/machine-id"):
            with open("/var/lib/dbus/machine-id", "w") as f:
                f.write(new_id + "\n")
        print(f"OK: Machine-ID reseeded to {new_id}")
        return 0
    except Exception as e:
        code, out, err = run_cmd(["systemd-machine-id-setup"])
        if code == 0:
            print("OK: Machine-ID reseeded via systemd-machine-id-setup")
            return 0
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

def action_timezone_utc(args: List[str]) -> int:
    code, out, err = run_cmd(["timedatectl", "set-timezone", "UTC"])
    if code != 0:
        try:
            if os.path.exists("/etc/localtime"):
                os.remove("/etc/localtime")
            os.symlink("/usr/share/zoneinfo/UTC", "/etc/localtime")
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
    print("OK: Timezone locked to UTC")
    return 0

def action_firewall_strict(args: List[str]) -> int:
    cmds = [
        ["iptables", "-F"],
        ["iptables", "-X"],
        ["iptables", "-P", "INPUT", "DROP"],
        ["iptables", "-P", "FORWARD", "DROP"],
        ["iptables", "-P", "OUTPUT", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ["ip6tables", "-F"],
        ["ip6tables", "-P", "INPUT", "DROP"],
        ["ip6tables", "-P", "FORWARD", "DROP"],
        ["ip6tables", "-P", "OUTPUT", "DROP"]
    ]
    for c in cmds:
        run_cmd(c)
    print("OK: Strict firewall profile applied")
    return 0

def action_firewall_vpn(args: List[str]) -> int:
    cmds = [
        ["iptables", "-F"],
        ["iptables", "-X"],
        ["iptables", "-P", "INPUT", "DROP"],
        ["iptables", "-P", "FORWARD", "DROP"],
        ["iptables", "-P", "OUTPUT", "DROP"],
        ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "tun+", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "tun+", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "wg+", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "wg+", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "proton+", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "proton+", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "pvpn+", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "pvpn+", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ["ip6tables", "-F"],
        ["ip6tables", "-P", "INPUT", "DROP"],
        ["ip6tables", "-P", "FORWARD", "DROP"],
        ["ip6tables", "-P", "OUTPUT", "DROP"]
    ]
    for c in cmds:
        run_cmd(c)
    print("OK: VPN tunnel killswitch applied")
    return 0

def action_firewall_proton(args: List[str]) -> int:
    cmds = [
        ["iptables", "-F"],
        ["iptables", "-X"],
        ["iptables", "-P", "INPUT", "DROP"],
        ["iptables", "-P", "FORWARD", "DROP"],
        ["iptables", "-P", "OUTPUT", "DROP"],
        ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "proton+", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "proton+", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "pvpn+", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "pvpn+", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "wg+", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "wg+", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "tun+", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "tun+", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        # WireGuard & OpenVPN ports
        ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "51820", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "1194", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "1194", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "8443", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "ACCEPT"],
        ["ip6tables", "-F"],
        ["ip6tables", "-P", "INPUT", "DROP"],
        ["ip6tables", "-P", "FORWARD", "DROP"],
        ["ip6tables", "-P", "OUTPUT", "DROP"]
    ]
    for c in cmds:
        run_cmd(c)
    print("OK: Proton VPN dedicated killswitch applied")
    return 0

def action_firewall_reset(args: List[str]) -> int:
    # If Kicksecure or Whonix native firewall exists, restart it cleanly
    code, _, _ = run_cmd(["systemctl", "is-active", "kicksecure-firewall"])
    if code == 0:
        run_cmd(["systemctl", "restart", "kicksecure-firewall"])
        print("OK: Restored native Kicksecure firewall")
        return 0

    code, _, _ = run_cmd(["systemctl", "is-active", "whonix-firewall"])
    if code == 0:
        run_cmd(["systemctl", "restart", "whonix-firewall"])
        print("OK: Restored native Whonix firewall")
        return 0

    cmds = [
        ["iptables", "-F"],
        ["iptables", "-X"],
        ["iptables", "-t", "nat", "-F"],
        ["iptables", "-t", "nat", "-X"],
        ["iptables", "-P", "INPUT", "ACCEPT"],
        ["iptables", "-P", "FORWARD", "ACCEPT"],
        ["iptables", "-P", "OUTPUT", "ACCEPT"],
        ["ip6tables", "-F"],
        ["ip6tables", "-P", "INPUT", "ACCEPT"],
        ["ip6tables", "-P", "FORWARD", "ACCEPT"],
        ["ip6tables", "-P", "OUTPUT", "ACCEPT"]
    ]
    for c in cmds:
        run_cmd(c)
    print("OK: Standard firewall default policy restored")
    return 0

def action_usb_lockdown(args: List[str]) -> int:
    enable = args[0] == "1" if args else True
    val = "0" if enable else "1"
    controllers = glob.glob("/sys/bus/usb/devices/usb*")
    count = 0
    for ctrl in controllers:
        auth_file = os.path.join(ctrl, "authorized_default")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "w") as f:
                    f.write(val)
                count += 1
            except Exception:
                pass
    if enable:
        run_cmd(["usbguard", "set-parameter", "InsertedDevicePolicy", "block"])
    else:
        run_cmd(["usbguard", "set-parameter", "InsertedDevicePolicy", "apply-policy"])
    print(f"OK: USB lockdown {'enabled' if enable else 'disabled'} ({count} controllers)")
    return 0

def action_webcam_toggle(args: List[str]) -> int:
    disable = args[0] == "1" if args else True
    if disable:
        code, out, err = run_cmd(["modprobe", "-r", "uvcvideo"])
        if code == 0:
            print("OK: Webcam driver unloaded")
            return 0
        print(f"WARN: Failed unloading uvcvideo: {err}", file=sys.stderr)
        return 1
    else:
        code, out, err = run_cmd(["modprobe", "uvcvideo"])
        if code == 0:
            print("OK: Webcam driver restored")
            return 0
        print(f"WARN: Failed loading uvcvideo: {err}", file=sys.stderr)
        return 1

def action_sysctl_harden(args: List[str]) -> int:
    params = {
        "kernel.yama.ptrace_scope": "3",
        "kernel.unprivileged_bpf_disabled": "1",
        "kernel.kptr_restrict": "2",
        "kernel.dmesg_restrict": "1",
        "fs.protected_fifos": "2",
        "fs.protected_regular": "2",
        "net.ipv4.tcp_syncookies": "1",
        "net.ipv4.tcp_rfc1337": "1"
    }
    applied = 0
    for k, v in params.items():
        code, _, _ = run_cmd(["sysctl", "-w", f"{k}={v}"])
        if code == 0:
            applied += 1
    print(f"OK: Applied {applied}/{len(params)} hardened kernel sysctl parameters")
    return 0

def action_apparmor_status(args: List[str]) -> int:
    code, out, err = run_cmd(["aa-status", "--json"])
    if code == 0 and out:
        print(out)
        return 0
    code2, out2, err2 = run_cmd(["aa-status"])
    if code2 == 0:
        print(out2)
        return 0
    print("AppArmor status unavailable or unconfined")
    return 0

def action_apparmor_enforce(args: List[str]) -> int:
    profiles = glob.glob("/etc/apparmor.d/*")
    if profiles:
        code, out, err = run_cmd(["aa-enforce"] + profiles)
        if code == 0:
            print("OK: AppArmor profiles enforced")
            return 0
        print(f"WARN: aa-enforce returned {code}: {err}", file=sys.stderr)
        return code
    print("OK: No AppArmor profiles to enforce")
    return 0

def action_purge_ram(args: List[str]) -> int:
    run_cmd(["sync"])
    try:
        with open("/proc/sys/vm/drop_caches", "w") as f:
            f.write("3\n")
        print("OK: Kernel RAM caches dropped")
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

def action_emergency_isolate(args: List[str]) -> int:
    # 1. Hardware radio kill
    run_cmd(["rfkill", "block", "all"])
    # 2. NetworkManager disable
    run_cmd(["nmcli", "networking", "off"])
    # 3. Bring down network interfaces
    for iface in glob.glob("/sys/class/net/*"):
        name = os.path.basename(iface)
        if name != "lo":
            run_cmd(["ip", "link", "set", "dev", name, "down"])
    # 4. Nuclear DROP firewall
    cmds = [
        ["iptables", "-F"],
        ["iptables", "-X"],
        ["iptables", "-t", "nat", "-F"],
        ["iptables", "-t", "nat", "-X"],
        ["iptables", "-P", "INPUT", "DROP"],
        ["iptables", "-P", "FORWARD", "DROP"],
        ["iptables", "-P", "OUTPUT", "DROP"],
        ["ip6tables", "-F"],
        ["ip6tables", "-X"],
        ["ip6tables", "-P", "INPUT", "DROP"],
        ["ip6tables", "-P", "FORWARD", "DROP"],
        ["ip6tables", "-P", "OUTPUT", "DROP"]
    ]
    for c in cmds:
        run_cmd(c)
    # 5. Terminate sensitive processes
    sensitive = ["firefox", "chromium", "brave", "tor", "openvpn", "wireguard", "telegram-desktop", "signal-desktop"]
    for p in sensitive:
        run_cmd(["pkill", "-9", "-f", p])
    print("OK: System completely isolated from all networks")
    return 0

def action_panic_nuke(args: List[str]) -> int:
    if len(args) < 1 or args[0] not in ["1234567890", "123457890"]:
        print("ERROR: Authorization failed", file=sys.stderr)
        return 1

    print("ALERT: EXECUTING DESTRUCTIVE PANIC NUKE PIPELINE")
    partitions = glob.glob("/dev/sd[a-z][0-9]*") + glob.glob("/dev/nvme[0-9]n[0-9]p[0-9]*")
    block_devices = glob.glob("/dev/sd[a-z]") + glob.glob("/dev/nvme[0-9]n[0-9]")

    # Tier 1: LUKS headers
    for p in partitions:
        run_cmd(["cryptsetup", "luksErase", "--batch-mode", p])
        run_cmd(["dd", "if=/dev/urandom", f"of={p}", "bs=1M", "count=16", "status=none", "conv=fsync"])

    # Tier 2: blkdiscard
    for b in block_devices:
        run_cmd(["blkdiscard", "-f", "-z", b])
        run_cmd(["sgdisk", "--zap-all", b])

    # Tier 3: Memory crash panic
    run_cmd(["sync"])
    try:
        with open("/proc/sys/kernel/sysrq", "w") as f:
            f.write("1\n")
        with open("/proc/sysrq-trigger", "w") as f:
            f.write("c\n")
    except Exception:
        pass
    return 0

def main():
    if os.geteuid() != 0:
        print("ERROR: cyberbreak-helper must be executed with root privileges via polkit or sudo.", file=sys.stderr)
        return 13

    if len(sys.argv) < 2:
        print(f"Usage: cyberbreak-helper <action> [args...]\nAllowed actions:\n  " + "\n  ".join(ALLOWED_ACTIONS))
        return 1

    action = sys.argv[1]
    args = sys.argv[2:]

    action_map = {
        "mac-randomize": action_mac_randomize,
        "hostname-randomize": action_hostname_randomize,
        "machine-id-reseed": action_machine_id_reseed,
        "timezone-utc": action_timezone_utc,
        "firewall-strict": action_firewall_strict,
        "firewall-vpn": action_firewall_vpn,
        "firewall-proton": action_firewall_proton,
        "firewall-reset": action_firewall_reset,
        "usb-lockdown": action_usb_lockdown,
        "webcam-toggle": action_webcam_toggle,
        "sysctl-harden": action_sysctl_harden,
        "apparmor-status": action_apparmor_status,
        "apparmor-enforce": action_apparmor_enforce,
        "purge-ram": action_purge_ram,
        "emergency-isolate": action_emergency_isolate,
        "panic-nuke": action_panic_nuke,
    }

    handler = action_map.get(action)
    if not handler:
        print(f"ERROR: Unrecognized action '{action}'", file=sys.stderr)
        return 1

    return handler(args)

if __name__ == "__main__":
    sys.exit(main())
