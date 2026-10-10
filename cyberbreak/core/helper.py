#!/usr/bin/env python3

import sys
import os
import re
import glob
import secrets
import subprocess
from typing import List, Tuple

ALLOWED_ACTIONS = [
    "install-webengine",
    "ghost-device",
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
    "usb-luks-dump",
    "usb-luks-backup",
    "usb-mount",
    "usb-umount",
    "usb-format",
    "usb-wipe-zero",
    "usb-flash-iso",
    "system-backup-usb",
    "drive-trim"
]

def run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
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


    run_cmd(["ip", "link", "set", "dev", iface, "down"])

    code, out, err = run_cmd(["macchanger", "-r", iface])
    if code != 0:

        rand_mac = "02:%02x:%02x:%02x:%02x:%02x" % tuple(secrets.token_bytes(5))
        run_cmd(["ip", "link", "set", "dev", iface, "address", rand_mac])

    run_cmd(["ip", "link", "set", "dev", iface, "up"])

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

def action_install_webengine(args: List[str]) -> int:
    if os.path.exists("/usr/bin/apt-get"):
        run_cmd(["apt-get", "update", "-y"])
        code, out, err = run_cmd(["apt-get", "install", "-y", "python3-pyqt6.qtwebengine", "python3-pip", "python3-pyqt6.qtsvg"])
        if code == 0:
            print("OK: python3-pyqt6.qtwebengine installed successfully via apt")
            return 0
    code, out, err = run_cmd(["python3", "-m", "pip", "install", "PyQt6-WebEngine", "PyQt6-QtSvg", "--break-system-packages"])
    if code == 0:
        print("OK: PyQt6-WebEngine installed successfully via pip")
        return 0
    if os.path.exists("/usr/bin/pacman"):
        code, out, err = run_cmd(["pacman", "-Sy", "--noconfirm", "python-pyqt6-webengine"])
        if code == 0:
            print("OK: python-pyqt6-webengine installed via pacman")
            return 0
    if os.path.exists("/usr/bin/dnf"):
        code, out, err = run_cmd(["dnf", "install", "-y", "python3-pyqt6-webengine"])
        if code == 0:
            print("OK: python3-pyqt6-webengine installed via dnf")
            return 0
    print(f"ERROR: Failed installing PyQt6-WebEngine: {err or out}", file=sys.stderr)
    return 1

def action_ghost_device(args: List[str]) -> int:
    import json
    results = {}

    # 1. Randomize MAC addresses across all physical/virtual network adapters
    mac_results = {}
    net_dir = "/sys/class/net"
    if os.path.exists(net_dir):
        for iface in os.listdir(net_dir):
            if iface in ("lo",) or iface.startswith(("veth", "docker", "virbr", "br-")):
                continue
            run_cmd(["ip", "link", "set", "dev", iface, "down"])
            code, out, _ = run_cmd(["macchanger", "-r", iface])
            if code != 0:
                rand_mac = "02:%02x:%02x:%02x:%02x:%02x" % tuple(secrets.token_bytes(5))
                run_cmd(["ip", "link", "set", "dev", iface, "address", rand_mac])
            run_cmd(["ip", "link", "set", "dev", iface, "up"])
            run_cmd(["nmcli", "device", "reapply", iface])

            addr_file = os.path.join(net_dir, iface, "address")
            if os.path.exists(addr_file):
                try:
                    with open(addr_file, "r") as f:
                        mac_results[iface] = f.read().strip()
                except Exception:
                    mac_results[iface] = "Randomized"
            else:
                mac_results[iface] = "Randomized"
    results["mac_addresses"] = mac_results

    # 2. Hostname randomization
    prefixes = ["DESKTOP", "THINKPAD", "DEBIAN-WS", "WORKSTATION", "HOST", "KICKSECURE"]
    suffix = secrets.token_hex(3).upper()
    new_host = f"{secrets.choice(prefixes)}-{suffix}"
    code, _, _ = run_cmd(["hostnamectl", "set-hostname", new_host])
    if code != 0:
        try:
            with open("/etc/hostname", "w") as f:
                f.write(new_host + "\n")
        except Exception:
            pass
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
    results["hostname"] = new_host

    # 3. Machine-ID and D-Bus ID reseed
    new_id = secrets.token_hex(16)
    try:
        with open("/etc/machine-id", "w") as f:
            f.write(new_id + "\n")
        if os.path.exists("/var/lib/dbus/machine-id"):
            with open("/var/lib/dbus/machine-id", "w") as f:
                f.write(new_id + "\n")
        results["machine_id"] = new_id
    except Exception:
        run_cmd(["systemd-machine-id-setup"])
        results["machine_id"] = "Reseeded via systemd"

    # 4. UTC timezone lock
    code, _, _ = run_cmd(["timedatectl", "set-timezone", "UTC"])
    if code != 0:
        try:
            if os.path.exists("/etc/localtime"):
                os.remove("/etc/localtime")
            os.symlink("/usr/share/zoneinfo/UTC", "/etc/localtime")
        except Exception:
            pass
    results["timezone"] = "UTC"

    # 5. Flush ARP / neighbor table
    run_cmd(["ip", "neigh", "flush", "all"])

    # 6. Flush DNS caches
    run_cmd(["resolvectl", "flush-caches"])
    run_cmd(["systemd-resolve", "--flush-caches"])
    run_cmd(["nscd", "-i", "hosts"])

    # 7. Drop RAM caches and memory buffers
    try:
        with open("/proc/sys/vm/drop_caches", "w") as f:
            f.write("3\n")
        results["ram_purged"] = True
    except Exception:
        results["ram_purged"] = False

    print(f"OK: GHOST_COMPLETE:{json.dumps(results)}")
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

def is_hid_or_critical_device(dev_path: str) -> bool:
    dev_name = os.path.basename(dev_path)
    if dev_name.startswith("usb"):
        return True

    dev_class_file = os.path.join(dev_path, "bDeviceClass")
    if os.path.exists(dev_class_file):
        try:
            with open(dev_class_file, "r") as f:
                cls = f.read().strip()
                if cls in ("03", "09"):
                    return True
        except Exception:
            pass

    for prop in ("product", "manufacturer"):
        prop_file = os.path.join(dev_path, prop)
        if os.path.exists(prop_file):
            try:
                with open(prop_file, "r") as f:
                    txt = f.read().lower()
                    if any(w in txt for w in ("mouse", "pointer", "trackball", "touchpad", "keyboard", "hid", "hub", "receiver", "dongle")):
                        return True
            except Exception:
                pass

    if os.path.exists(os.path.join(dev_path, "input")) or glob.glob(os.path.join(dev_path, "input*")):
        return True

    for iface in glob.glob(os.path.join(dev_path, "*:*")):
        class_file = os.path.join(iface, "bInterfaceClass")
        if os.path.exists(class_file):
            try:
                with open(class_file, "r") as f:
                    if f.read().strip() == "03":
                        return True
            except Exception:
                pass
        if os.path.exists(os.path.join(iface, "input")):
            return True

    return False

def action_usb_lockdown(args: List[str]) -> int:
    if args and args[0] == "0":
        return action_usb_unlock(args)

    controllers = glob.glob("/sys/bus/usb/devices/usb*")
    for ctrl in controllers:
        auth_file = os.path.join(ctrl, "authorized")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "w") as f:
                    f.write("1")
            except Exception:
                pass

    devices = glob.glob("/sys/bus/usb/devices/[0-9]*")
    deauth_count = 0
    protected_count = 0
    for dev in devices:
        if ":" in os.path.basename(dev):
            continue
        auth_file = os.path.join(dev, "authorized")
        if not os.path.exists(auth_file):
            continue

        if is_hid_or_critical_device(dev):
            try:
                with open(auth_file, "w") as f:
                    f.write("1")
                protected_count += 1
            except Exception:
                pass
        else:
            try:
                with open(auth_file, "w") as f:
                    f.write("0")
                deauth_count += 1
            except Exception:
                pass

    print(f"OK: USB lockdown active ({deauth_count} non-input devices blocked, {protected_count} mouse/keyboard/hub devices protected)")
    return 0

def action_usb_unlock(args: List[str]) -> int:
    controllers = glob.glob("/sys/bus/usb/devices/usb*")
    for ctrl in controllers:
        for fname in ("authorized_default", "authorized"):
            auth_file = os.path.join(ctrl, fname)
            if os.path.exists(auth_file):
                try:
                    with open(auth_file, "w") as f:
                        f.write("1")
                except Exception:
                    pass

    devices = glob.glob("/sys/bus/usb/devices/[0-9]*")
    auth_count = 0
    for dev in devices:
        if ":" in os.path.basename(dev):
            continue
        auth_file = os.path.join(dev, "authorized")
        if os.path.exists(auth_file):
            try:
                with open(auth_file, "w") as f:
                    f.write("1")
                auth_count += 1
            except Exception:
                pass

    conf_path = "/etc/modprobe.d/cyberbreak-usb-lock.conf"
    if os.path.exists(conf_path):
        try:
            os.remove(conf_path)
        except Exception:
            pass

    run_cmd(["modprobe", "-a", "usb-storage", "uas"])
    run_cmd(["usbguard", "set-parameter", "InsertedDevicePolicy", "apply-policy"])
    code, out, _ = run_cmd(["usbguard", "list-devices", "-b"])
    if code == 0 and out:
        for line in out.strip().split("\n"):
            parts = line.split(":", 1)
            if parts and parts[0].strip().isdigit():
                run_cmd(["usbguard", "allow-device", parts[0].strip()])

    for pci_rescan in glob.glob("/sys/bus/pci/rescan"):
        try:
            with open(pci_rescan, "w") as f:
                f.write("1\n")
        except Exception:
            pass

    print(f"OK: USB ports and devices restored ({len(controllers)} controllers, {auth_count} devices authorized)")
    return 0

def action_usb_device_auth(args: List[str]) -> int:
    if len(args) < 2:
        print("ERROR: Device ID and auth state (1/0) required", file=sys.stderr)
        return 2
    dev_id, val = args[0], args[1]
    if not re.match(r"^[a-zA-Z0-9_\-\.:]+$", dev_id):
        print(f"ERROR: Invalid device ID: '{dev_id}'", file=sys.stderr)
        return 3

    if ":" in dev_id:
        dev_id = dev_id.split(":")[0]

    target_dir = f"/sys/bus/usb/devices/{dev_id}"
    auth_path = f"{target_dir}/authorized"
    if not os.path.exists(auth_path):
        print(f"ERROR: Device sysfs node does not exist: {auth_path}", file=sys.stderr)
        return 4

    if val == "1":
        bus_match = re.match(r"^([0-9]+)-", dev_id)
        if bus_match:
            ctrl_auth = f"/sys/bus/usb/devices/usb{bus_match.group(1)}/authorized"
            if os.path.exists(ctrl_auth):
                try:
                    with open(ctrl_auth, "w") as f:
                        f.write("1")
                except Exception:
                    pass

        if "." in dev_id:
            parent_id = dev_id.rsplit(".", 1)[0]
            while parent_id:
                p_auth = f"/sys/bus/usb/devices/{parent_id}/authorized"
                if os.path.exists(p_auth):
                    try:
                        with open(p_auth, "w") as f:
                            f.write("1")
                    except Exception:
                        pass
                if "." in parent_id:
                    parent_id = parent_id.rsplit(".", 1)[0]
                else:
                    break

    try:
        with open(auth_path, "w") as f:
            f.write("1" if val == "1" else "0")
    except Exception as e:
        print(f"ERROR: Failed writing authorized node: {e}", file=sys.stderr)
        return 5

    if val == "1":
        code, out, _ = run_cmd(["usbguard", "list-devices"])
        if code == 0 and out:
            for line in out.strip().split("\n"):
                if f"at {dev_id}" in line or dev_id in line:
                    parts = line.split(":", 1)
                    if parts and parts[0].strip().isdigit():
                        run_cmd(["usbguard", "allow-device", parts[0].strip()])

    print(f"OK: USB device {dev_id} authorized={val}")
    return 0

def action_usb_storage_block(args: List[str]) -> int:
    block = args[0] == "1" if args else True
    conf_path = "/etc/modprobe.d/cyberbreak-usb-lock.conf"
    if block:
        try:
            os.makedirs("/etc/modprobe.d", exist_ok=True)
            with open(conf_path, "w") as f:
                f.write("# CyberBreak USB Storage Block\nblacklist usb_storage\nblacklist uas\ninstall usb-storage /bin/true\ninstall uas /bin/true\n")
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
        run_cmd(["modprobe", "-a", "usb-storage", "uas"])
        print("OK: USB mass storage drivers unblocked and loaded")
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

    run_cmd(["rfkill", "block", "all"])

    run_cmd(["nmcli", "networking", "off"])

    for iface in glob.glob("/sys/class/net/*"):
        name = os.path.basename(iface)
        if name != "lo":
            run_cmd(["ip", "link", "set", "dev", name, "down"])

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


    for p in partitions:
        run_cmd(["cryptsetup", "luksErase", "--batch-mode", p])
        run_cmd(["dd", "if=/dev/urandom", f"of={p}", "bs=1M", "count=16", "status=none", "conv=fsync"])


    for b in block_devices:
        run_cmd(["blkdiscard", "-f", "-z", b])
        run_cmd(["sgdisk", "--zap-all", b])


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
    if not re.match(r"^/dev/(sd[a-z][0-9]*|nvme[0-9]n[0-9](p[0-9]+)?|loop[0-9]+|vd[a-z][0-9]*|mapper/[a-zA-Z0-9_\-]+)$", dev):
        return False
    if not os.path.exists(dev):
        return False
    try:
        # Check against active mountpoints
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    mounted_dev, mountpoint = parts[0], parts[1]
                    # Block root, boot, home, var, usr, etc.
                    if mountpoint in ("/", "/boot", "/boot/efi", "/etc", "/home", "/var", "/usr", "/tmp") and (mounted_dev == dev or dev.startswith(mounted_dev) or mounted_dev.startswith(dev)):
                        return False
    except Exception:
        pass
    return True

def action_usb_luks_format(args: List[str]) -> int:
    if len(args) < 2:
        print("ERROR: Device and keyfile path required", file=sys.stderr)
        return 2
    dev, keyfile = args[0], args[1]
    header_file = args[2] if len(args) > 2 and args[2] not in ("none", "") else None
    if not is_safe_block_device(dev):
        print(f"ERROR: Unsafe target device '{dev}'", file=sys.stderr)
        return 3
    if not os.path.exists(keyfile):
        print(f"ERROR: Keyfile not found: '{keyfile}'", file=sys.stderr)
        return 4

    # Calibrate Argon2id memory to system capacity (min 128MB, up to 1GB, default 512MB)
    pbkdf_mem_kb = 524288
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    tot_kb = int(line.split()[1])
                    pbkdf_mem_kb = max(131072, min(1048576, tot_kb // 4))
                    break
    except Exception:
        pass

    # Initialize empty detached header if requested
    if header_file:
        try:
            h_dir = os.path.dirname(header_file)
            if h_dir:
                os.makedirs(h_dir, exist_ok=True)
            if not os.path.exists(header_file):
                with open(header_file, "wb") as f:
                    f.write(b"\x00" * (16 * 1024 * 1024))
                os.chmod(header_file, 0o600)
        except Exception as e:
            print(f"ERROR: Failed creating detached header file: {e}", file=sys.stderr)
            return 5

    # 1. AES-256-XTS (aes-xts-plain64, 512-bit combined key)
    # 2. Argon2id PBKDF with hardware-calibrated memory & work factor
    cmd = [
        "cryptsetup", "luksFormat", "--type", "luks2",
        "--cipher", "aes-xts-plain64", "--key-size", "512",
        "--hash", "sha512",
        "--pbkdf", "argon2id",
        "--pbkdf-memory", str(pbkdf_mem_kb),
        "--pbkdf-parallelism", "4",
        "--iter-time", "3000",
        "--batch-mode",
        "--key-file", keyfile
    ]
    if header_file:
        cmd.extend(["--header", header_file])
    cmd.append(dev)

    code, out, err = run_cmd(cmd)
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    print(f"OK: Hardened LUKS2 (AES-256-XTS / Argon2id) volume formatted on {dev}")
    return 0

def action_usb_luks_open(args: List[str]) -> int:
    if len(args) < 3:
        print("ERROR: Device, mapper name, and keyfile required", file=sys.stderr)
        return 2
    dev, mapper, keyfile = args[0], args[1], args[2]
    header_file = args[3] if len(args) > 3 and args[3] not in ("none", "") else None
    if not re.match(r"^[a-zA-Z0-9_\-]{1,32}$", mapper):
        print("ERROR: Invalid mapper name", file=sys.stderr)
        return 3
    if not os.path.exists(keyfile):
        print("ERROR: Keyfile not found", file=sys.stderr)
        return 4
    cmd = ["cryptsetup", "luksOpen", dev, mapper, "--key-file", keyfile]
    if header_file and os.path.exists(header_file):
        cmd.extend(["--header", header_file])
    code, out, err = run_cmd(cmd)
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

def action_usb_luks_dump(args: List[str]) -> int:
    if len(args) < 1:
        print("ERROR: Device or header required", file=sys.stderr)
        return 2
    dev = args[0]
    header_file = args[1] if len(args) > 1 and args[1] not in ("none", "") else None
    cmd = ["cryptsetup", "luksDump"]
    if header_file and os.path.exists(header_file):
        cmd.extend(["--header", header_file])
    cmd.append(dev)
    code, out, err = run_cmd(cmd)
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    print(out)
    return 0

def action_usb_luks_backup(args: List[str]) -> int:
    if len(args) < 2:
        print("ERROR: Device and backup destination required", file=sys.stderr)
        return 2
    dev, backup_path = args[0], args[1]
    header_file = args[2] if len(args) > 2 and args[2] not in ("none", "") else None
    if header_file and os.path.exists(header_file):
        try:
            import shutil
            b_dir = os.path.dirname(backup_path)
            if b_dir:
                os.makedirs(b_dir, exist_ok=True)
            shutil.copy2(header_file, backup_path)
            os.chmod(backup_path, 0o600)
            print(f"OK: Detached header backup saved to {backup_path}")
            return 0
        except Exception as e:
            print(f"ERROR: Failed copying header: {e}", file=sys.stderr)
            return 4
    cmd = ["cryptsetup", "luksHeaderBackup", dev, "--header-backup-file", backup_path, "--batch-mode"]
    code, out, err = run_cmd(cmd)
    if code != 0:
        print(f"ERROR: {err or out}", file=sys.stderr)
        return code
    try:
        os.chmod(backup_path, 0o600)
    except Exception:
        pass
    print(f"OK: Header backup created at {backup_path}")
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
        "install-webengine": action_install_webengine,
        "ghost-device": action_ghost_device,
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
        "usb-luks-dump": action_usb_luks_dump,
        "usb-luks-backup": action_usb_luks_backup,
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
