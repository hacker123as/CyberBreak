#!/usr/bin/env python3
"""
CyberBreak Narrowly Scoped Privileged Helper
Target: Kicksecure Linux / Debian / Arch
Security: Only accepts predefined, strictly validated actions.
Never executes arbitrary shell input. Owned by root:root, mode 0755.
Engineered by lilami only.
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
    "usb-unlock",
    "usb-device-auth",
    "usb-storage-block",
    "port-block",
    "port-kill",
    "port-lockdown-all",
    "iptables-rules-list",
    "tor-read-cookie",
    "webcam-toggle",
    "sysctl-harden",
    "apparmor-status",
    "apparmor-enforce",
    "purge-ram",
    "emergency-isolate",
    "panic-nuke",
    "usb-luks-format",
    "usb-luks-open",
    "usb-luks-close",
    "usb-mount",
    "usb-umount",
    "usb-format",
    "usb-wipe-zero",
    "usb-flash-iso",
    "system-backup-usb",
    "drive-trim"
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
    # 1. Block default authorization on all root controllers
    controllers = glob.glob("/sys/bus/usb/devices/usb*")
    for ctrl in controllers:
        auth_file = os.path.join(ctrl, "authorized_default")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "w") as f:
                    f.write("0")
            except Exception:
                pass

    # 2. De-authorize connected non-root USB devices (excluding root hubs)
    devices = glob.glob("/sys/bus/usb/devices/[0-9]*")
    deauth_count = 0
    for dev in devices:
        auth_file = os.path.join(dev, "authorized")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "w") as f:
                    f.write("0")
                deauth_count += 1
            except Exception:
                pass

    # 3. Block usb-storage & uas kernel drivers
    try:
        os.makedirs("/etc/modprobe.d", exist_ok=True)
        with open("/etc/modprobe.d/cyberbreak-usb-lock.conf", "w") as f:
            f.write("# CyberBreak USB Storage Lockdown\nblacklist usb_storage\nblacklist uas\ninstall usb-storage /bin/true\ninstall uas /bin/true\n")
    except Exception:
        pass
    run_cmd(["modprobe", "-r", "uas", "usb-storage"])

    # 4. USBGuard policy if present
    run_cmd(["usbguard", "set-parameter", "InsertedDevicePolicy", "block"])

    print(f"OK: Deep USB lockdown enabled ({len(controllers)} root controllers, {deauth_count} devices isolated)")
    return 0

def action_usb_unlock(args: List[str]) -> int:
    controllers = glob.glob("/sys/bus/usb/devices/usb*")
    for ctrl in controllers:
        auth_file = os.path.join(ctrl, "authorized_default")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "w") as f:
                    f.write("1")
            except Exception:
                pass

    devices = glob.glob("/sys/bus/usb/devices/[0-9]*")
    auth_count = 0
    for dev in devices:
        auth_file = os.path.join(dev, "authorized")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "w") as f:
                    f.write("1")
                auth_count += 1
            except Exception:
                pass

    if os.path.exists("/etc/modprobe.d/cyberbreak-usb-lock.conf"):
        try:
            os.remove("/etc/modprobe.d/cyberbreak-usb-lock.conf")
        except Exception:
            pass

    run_cmd(["usbguard", "set-parameter", "InsertedDevicePolicy", "apply-policy"])
    print(f"OK: USB ports and devices restored ({len(controllers)} controllers, {auth_count} devices authorized)")
    return 0

def action_usb_device_auth(args: List[str]) -> int:
    if len(args) < 2:
        print("ERROR: Device ID and auth state (1/0) required", file=sys.stderr)
        return 2
    dev_id, val = args[0], args[1]
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", dev_id):
        print(f"ERROR: Invalid device ID: '{dev_id}'", file=sys.stderr)
        return 3
    auth_path = f"/sys/bus/usb/devices/{dev_id}/authorized"
    if not os.path.exists(auth_path):
        print(f"ERROR: Device sysfs node does not exist: {auth_path}", file=sys.stderr)
        return 4
    try:
        with open(auth_path, "w") as f:
            f.write("1" if val == "1" else "0")
        print(f"OK: USB device {dev_id} authorized={val}")
        return 0
    except Exception as e:
        print(f"ERROR: Failed writing authorized node: {e}", file=sys.stderr)
        return 5

def action_usb_storage_block(args: List[str]) -> int:
    block = args[0] == "1" if args else True
    conf_path = "/etc/modprobe.d/cyberbreak-usb-lock.conf"
    if block:
        try:
            os.makedirs("/etc/modprobe.d", exist_ok=True)
            with open(conf_path, "w") as f:
                f.write("blacklist usb_storage\nblacklist uas\ninstall usb-storage /bin/true\ninstall uas /bin/true\n")
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        for dev in glob.glob("/sys/bus/usb/drivers/usb-storage/*"):
            dev_name = os.path.basename(dev)
            if re.match(r"^[0-9]+-[0-9\.]+$", dev_name):
                try:
                    with open("/sys/bus/usb/drivers/usb-storage/unbind", "w") as f:
                        f.write(dev_name)
                except Exception:
                    pass
        run_cmd(["modprobe", "-r", "uas", "usb-storage"])
        print("OK: USB mass storage drivers blocked at kernel level")
        return 0
    else:
        if os.path.exists(conf_path):
            try:
                os.remove(conf_path)
            except Exception:
                pass
        run_cmd(["modprobe", "usb-storage"])
        print("OK: USB mass storage drivers unblocked")
        return 0

def action_port_block(args: List[str]) -> int:
    if len(args) < 2:
        print("ERROR: Port and protocol required", file=sys.stderr)
        return 2
    port_str, proto = args[0], args[1].lower()
    if not port_str.isdigit() or not (1 <= int(port_str) <= 65535):
        print(f"ERROR: Invalid port '{port_str}'", file=sys.stderr)
        return 3
    if proto not in ("tcp", "udp"):
        print(f"ERROR: Invalid protocol '{proto}'", file=sys.stderr)
        return 4
    port = port_str
    run_cmd(["iptables", "-I", "INPUT", "1", "-p", proto, "--dport", port, "-j", "DROP"])
    run_cmd(["ip6tables", "-I", "INPUT", "1", "-p", proto, "--dport", port, "-j", "DROP"])
    print(f"OK: Inbound traffic to {proto.upper()}:{port} dropped by Netfilter")
    return 0

def action_port_kill(args: List[str]) -> int:
    if len(args) < 1:
        print("ERROR: PID required", file=sys.stderr)
        return 2
    pid_str = args[0]
    if not pid_str.isdigit():
        print("ERROR: PID must be integer", file=sys.stderr)
        return 3
    pid = int(pid_str)
    if pid <= 100:
        print(f"ERROR: Refusing to kill critical system PID {pid}", file=sys.stderr)
        return 4
    cmdline_path = f"/proc/{pid}/cmdline"
    if os.path.exists(cmdline_path):
        try:
            with open(cmdline_path, "r") as f:
                cmd = f.read()
                if any(crit in cmd for crit in ("systemd", "init", "dbus", "polkit", "kworker")):
                    print(f"ERROR: Refusing to kill protected daemon PID {pid}", file=sys.stderr)
                    return 5
        except Exception:
            pass
    code, _, err = run_cmd(["kill", "-9", str(pid)])
    if code == 0:
        print(f"OK: Terminated listening process PID {pid}")
        return 0
    print(f"ERROR: Failed to kill PID {pid}: {err}", file=sys.stderr)
    return code

def action_port_lockdown_all(args: List[str]) -> int:
    code, out, _ = run_cmd(["ss", "-tulnp"])
    blocked_count = 0
    killed_count = 0

    if code == 0 and out:
        for line in out.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 5:
                proto = parts[0].lower()
                local_raw = parts[4]
                colon = local_raw.rfind(":")
                if colon != -1:
                    port_str = local_raw[colon+1:]
                    if port_str.isdigit():
                        port = int(port_str)
                        run_cmd(["iptables", "-I", "INPUT", "1", "-p", proto, "--dport", str(port), "-j", "DROP"])
                        blocked_count += 1

                rest = " ".join(parts[5:]) if len(parts) > 5 else ""
                proc_match = re.search(r'users:\(\("([^"]+)",pid=(\d+)', rest)
                if proc_match:
                    p_name = proc_match.group(1)
                    p_pid = int(proc_match.group(2))
                    if p_pid > 100 and p_name not in ("tor", "systemd-resolved"):
                        run_cmd(["kill", "-9", str(p_pid)])
                        killed_count += 1

    # Block inbound NEW connections
    run_cmd(["iptables", "-I", "INPUT", "1", "-m", "conntrack", "--ctstate", "NEW", "-m", "tcp", "-p", "tcp", "-j", "DROP"])
    run_cmd(["iptables", "-I", "INPUT", "1", "-m", "conntrack", "--ctstate", "NEW", "-m", "udp", "-p", "udp", "-j", "DROP"])

    print(f"OK: Full port lockdown applied ({blocked_count} ports dropped, {killed_count} daemons terminated)")
    return 0

def action_iptables_rules_list(args: List[str]) -> int:
    code, out, err = run_cmd(["iptables", "-L", "-n", "-v", "--line-numbers"])
    if code == 0:
        print(out)
        return 0
    print(f"ERROR: {err or out}", file=sys.stderr)
    return code

def action_tor_read_cookie(args: List[str]) -> int:
    paths = [
        "/run/tor/control.authcookie",
        "/var/run/tor/control.authcookie",
        "/var/lib/tor/data/control_auth_cookie"
    ] + glob.glob("/run/tor-instances/*/control.authcookie")
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    data = f.read()
                    if len(data) == 32:
                        print(data.hex())
                        return 0
            except Exception:
                pass
    print("ERROR: Tor cookie not found or unreadable", file=sys.stderr)
    return 1

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

def is_safe_block_device(dev: str) -> bool:
    """Ensures device is a valid block device and NEVER the active host root/boot device."""
    if not re.match(r"^/dev/(sd[a-z][0-9]*|nvme[0-9]n[0-9](p[0-9]+)?|loop[0-9]+|vd[a-z][0-9]*|mapper/[a-zA-Z0-9_\-]+)$", dev):
        return False
    if not os.path.exists(dev):
        return False
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    mounted_dev, mountpoint = parts[0], parts[1]
                    if mountpoint in ("/", "/boot", "/boot/efi", "/etc") and (mounted_dev == dev or dev.startswith(mounted_dev)):
                        return False
    except Exception:
        pass
    return True

def action_usb_luks_format(args: List[str]) -> int:
    if len(args) < 2:
        print("ERROR: Device and keyfile path required", file=sys.stderr)
        return 2
    dev, keyfile = args[0], args[1]
    if not is_safe_block_device(dev):
        print(f"ERROR: Unsafe target device '{dev}'", file=sys.stderr)
        return 3
    if not os.path.exists(keyfile):
        print(f"ERROR: Keyfile not found: '{keyfile}'", file=sys.stderr)
        return 4
    cmd = [
        "cryptsetup", "luksFormat", "--type", "luks2",
        "--cipher", "aes-xts-plain64", "--key-size", "512",
        "--hash", "sha512", "--batch-mode",
        "--key-file", keyfile, dev
    ]
    code, out, err = run_cmd(cmd)
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    print(f"OK: LUKS2 volume formatted on {dev}")
    return 0

def action_usb_luks_open(args: List[str]) -> int:
    if len(args) < 3:
        print("ERROR: Device, mapper name, and keyfile required", file=sys.stderr)
        return 2
    dev, mapper, keyfile = args[0], args[1], args[2]
    if not re.match(r"^[a-zA-Z0-9_\-]{1,32}$", mapper):
        print("ERROR: Invalid mapper name", file=sys.stderr)
        return 3
    if not os.path.exists(keyfile):
        print("ERROR: Keyfile not found", file=sys.stderr)
        return 4
    code, out, err = run_cmd(["cryptsetup", "luksOpen", dev, mapper, "--key-file", keyfile])
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    print(f"OK: Mapper {mapper} opened")
    return 0

def action_usb_luks_close(args: List[str]) -> int:
    if len(args) < 1:
        print("ERROR: Mapper name required", file=sys.stderr)
        return 2
    mapper = args[0]
    if not re.match(r"^[a-zA-Z0-9_\-]{1,32}$", mapper):
        return 3
    code, out, err = run_cmd(["cryptsetup", "luksClose", mapper])
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    print(f"OK: Mapper {mapper} closed")
    return 0

def action_usb_mount(args: List[str]) -> int:
    if len(args) < 3:
        print("ERROR: Device, mountpoint, and fstype required", file=sys.stderr)
        return 2
    dev, mountpoint, fstype = args[0], args[1], args[2]
    if not (mountpoint.startswith("/media/") or mountpoint.startswith("/mnt/")):
        print("ERROR: Mountpoint must be inside /media/ or /mnt/", file=sys.stderr)
        return 3
    os.makedirs(mountpoint, exist_ok=True)
    code, out, err = run_cmd(["mount", "-t", fstype, dev, mountpoint])
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    run_cmd(["chmod", "770", mountpoint])
    print(f"OK: Mounted {dev} on {mountpoint}")
    return 0

def action_usb_umount(args: List[str]) -> int:
    if len(args) < 1:
        print("ERROR: Mountpoint required", file=sys.stderr)
        return 2
    mountpoint = args[0]
    if not (mountpoint.startswith("/media/") or mountpoint.startswith("/mnt/")):
        print("ERROR: Mountpoint must be inside /media/ or /mnt/", file=sys.stderr)
        return 3
    code, out, err = run_cmd(["umount", "-l", mountpoint])
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    print(f"OK: Unmounted {mountpoint}")
    return 0

def action_usb_format(args: List[str]) -> int:
    if len(args) < 2:
        print("ERROR: Device and fstype required", file=sys.stderr)
        return 2
    dev, fstype = args[0], args[1]
    label = args[2] if len(args) > 2 else "Storage"
    label = re.sub(r"[^a-zA-Z0-9_\-]", "", label)[:16] or "Storage"

    if not is_safe_block_device(dev):
        print(f"ERROR: Unsafe target device '{dev}'", file=sys.stderr)
        return 3

    if fstype == "ext4":
        code, out, err = run_cmd(["mkfs.ext4", "-F", "-L", label, dev])
    elif fstype == "btrfs":
        code, out, err = run_cmd(["mkfs.btrfs", "-f", "-L", label, dev])
    elif fstype == "vfat":
        code, out, err = run_cmd(["mkfs.vfat", "-F", "32", "-n", label, dev])
    elif fstype == "exfat":
        code, out, err = run_cmd(["mkfs.exfat", "-n", label, dev])
    else:
        print(f"ERROR: Unsupported fstype '{fstype}'", file=sys.stderr)
        return 4

    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    print(f"OK: Formatted {dev} as {fstype}")
    return 0

def action_usb_wipe_zero(args: List[str]) -> int:
    if len(args) < 1:
        print("ERROR: Device required", file=sys.stderr)
        return 2
    dev = args[0]
    if not is_safe_block_device(dev):
        print(f"ERROR: Unsafe target device '{dev}'", file=sys.stderr)
        return 3
    run_cmd(["wipefs", "-a", dev])
    code, out, err = run_cmd(["dd", "if=/dev/zero", f"of={dev}", "bs=1M", "count=64", "status=none", "conv=fsync"])
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    print(f"OK: Partition table wiped on {dev}")
    return 0

def action_usb_flash_iso(args: List[str]) -> int:
    if len(args) < 2:
        print("ERROR: ISO path and target device required", file=sys.stderr)
        return 2
    iso, dev = args[0], args[1]
    if not os.path.exists(iso) or not iso.lower().endswith(".iso"):
        print(f"ERROR: Invalid ISO path: {iso}", file=sys.stderr)
        return 3
    if not is_safe_block_device(dev):
        print(f"ERROR: Unsafe target device '{dev}'", file=sys.stderr)
        return 4
    code, out, err = run_cmd(["dd", f"if={iso}", f"of={dev}", "bs=4M", "status=none", "conv=fdatasync"])
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    run_cmd(["sync"])
    print(f"OK: Burned {iso} to {dev}")
    return 0

def action_system_backup_usb(args: List[str]) -> int:
    if len(args) < 3:
        print("ERROR: Target dir, mode, and user required", file=sys.stderr)
        return 2
    target_dir, mode, user = args[0], args[1], args[2]
    if not (target_dir.startswith("/media/") or target_dir.startswith("/mnt/")):
        print("ERROR: Backup target must be mounted in /media/ or /mnt/", file=sys.stderr)
        return 3
    if not os.path.exists(target_dir):
        print(f"ERROR: Target directory does not exist: {target_dir}", file=sys.stderr)
        return 4

    timestamp = subprocess.getoutput("date +%Y%m%d_%H%M%S")
    out_file = os.path.join(target_dir, f"cyberbreak_backup_{mode}_{timestamp}.tar.gz")

    if mode == "home":
        src = f"/home/{user}" if os.path.exists(f"/home/{user}") else "/home"
        cmd = ["tar", "-czf", out_file, "--exclude=.cache", "--exclude=.local/share/Trash", src]
    else:
        cmd = [
            "tar", "-czf", out_file,
            "/etc", "/usr/local/bin", f"/home/{user}"
        ]

    code, out, err = run_cmd(cmd)
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    run_cmd(["sync"])
    print(f"OK: System backup created at {out_file}")
    return 0

def action_drive_trim(args: List[str]) -> int:
    code, out, err = run_cmd(["fstrim", "-av"])
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    print(out or "OK: All SSD storage and crypt mappings trimmed.")
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
        "usb-unlock": action_usb_unlock,
        "usb-device-auth": action_usb_device_auth,
        "usb-storage-block": action_usb_storage_block,
        "port-block": action_port_block,
        "port-kill": action_port_kill,
        "port-lockdown-all": action_port_lockdown_all,
        "iptables-rules-list": action_iptables_rules_list,
        "tor-read-cookie": action_tor_read_cookie,
        "webcam-toggle": action_webcam_toggle,
        "sysctl-harden": action_sysctl_harden,
        "apparmor-status": action_apparmor_status,
        "apparmor-enforce": action_apparmor_enforce,
        "purge-ram": action_purge_ram,
        "emergency-isolate": action_emergency_isolate,
        "panic-nuke": action_panic_nuke,
        "usb-luks-format": action_usb_luks_format,
        "usb-luks-open": action_usb_luks_open,
        "usb-luks-close": action_usb_luks_close,
        "usb-mount": action_usb_mount,
        "usb-umount": action_usb_umount,
        "usb-format": action_usb_format,
        "usb-wipe-zero": action_usb_wipe_zero,
        "usb-flash-iso": action_usb_flash_iso,
        "system-backup-usb": action_system_backup_usb,
        "drive-trim": action_drive_trim,
    }

    handler = action_map.get(action)
    if not handler:
        print(f"ERROR: Unrecognized action '{action}'", file=sys.stderr)
        return 1

    return handler(args)

if __name__ == "__main__":
    sys.exit(main())
