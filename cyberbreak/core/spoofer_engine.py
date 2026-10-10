import os
import glob
import random
import secrets
from typing import List, Dict, Tuple
from cyberbreak.core.executor import run_sync, log

class SpooferEngine:
    """Hardware, MAC, Hostname, and Identity Spoofing Engine."""

    @staticmethod
    def get_network_interfaces() -> List[Dict[str, str]]:
        """Enumerates active physical and wireless network adapters from sysfs."""
        interfaces = []
        net_dir = "/sys/class/net"
        if not os.path.exists(net_dir):
            return interfaces

        for iface in os.listdir(net_dir):
            # Skip loopback and virtual virtualization interfaces
            if iface in ("lo",) or iface.startswith(("veth", "docker", "virbr", "br-")):
                continue

            addr_path = os.path.join(net_dir, iface, "address")
            oper_path = os.path.join(net_dir, iface, "operstate")

            mac = "Unknown"
            state = "unknown"

            if os.path.exists(addr_path):
                try:
                    with open(addr_path, "r") as f:
                        mac = f.read().strip()
                except Exception:
                    pass

            if os.path.exists(oper_path):
                try:
                    with open(oper_path, "r") as f:
                        state = f.read().strip()
                except Exception:
                    pass

            interfaces.append({
                "name": iface,
                "mac": mac,
                "state": state
            })
        return interfaces

    @staticmethod
    def randomize_mac(interface: str) -> Tuple[bool, str]:
        """Brings interface down, randomizes MAC with macchanger or ip link, and brings it up."""
        log(f"Initiating MAC randomization sequence on {interface}", "SPOOF")
        # Step 1: Interface down
        code, out, err = run_sync(f"ip link set dev {interface} down")
        if code != 0:
            log(f"Failed to bring {interface} down: {err}", "ERR")
            return False, f"Interface down failed: {err}"

        # Step 2: macchanger or manual random MAC
        code, out, err = run_sync(f"macchanger -r {interface}")
        if code != 0:
            # Fallback to pure ip link with locally administered unicast MAC
            rand_mac = "02:%02x:%02x:%02x:%02x:%02x" % tuple(secrets.token_bytes(5))
            log(f"macchanger failed, applying fallback MAC: {rand_mac}", "WARN")
            code, out, err = run_sync(f"ip link set dev {interface} address {rand_mac}")

        # Step 3: Interface up
        run_sync(f"ip link set dev {interface} up")
        # Step 4: NetworkManager reapply if available
        run_sync(f"nmcli device reapply {interface}")

        log(f"MAC randomization completed on {interface}", "OK")
        return True, out

    @staticmethod
    def randomize_hostname() -> Tuple[bool, str]:
        """Generates realistic OEM workstation hostname and applies via hostnamectl."""
        prefixes = ["DESKTOP", "THINKPAD", "DEBIAN-WS", "WORKSTATION", "HOST"]
        suffix = secrets.token_hex(3).upper()
        new_name = f"{random.choice(prefixes)}-{suffix}"
        log(f"Rotating hostname to: {new_name}", "SPOOF")

        code, out, err = run_sync(f"hostnamectl set-hostname {new_name}")
        if code == 0:
            log(f"Hostname successfully set to {new_name}", "OK")
            return True, new_name
        else:
            log(f"Failed to set hostname: {err}", "ERR")
            return False, err

    @staticmethod
    def reseed_machine_id() -> Tuple[bool, str]:
        """Re-seeds /etc/machine-id to prevent cross-session correlation."""
        new_id = secrets.token_hex(16)
        log("Re-seeding /etc/machine-id with random entropy", "SPOOF")
        try:
            with open("/etc/machine-id", "w") as f:
                f.write(new_id + "\n")
            if os.path.exists("/var/lib/dbus/machine-id"):
                with open("/var/lib/dbus/machine-id", "w") as f:
                    f.write(new_id + "\n")
            log(f"Machine-ID updated: {new_id[:8]}...", "OK")
            return True, new_id
        except Exception as e:
            # Try via systemd tool if permission error
            code, out, err = run_sync("systemd-machine-id-setup")
            if code == 0:
                log("Machine-ID refreshed via systemd-machine-id-setup", "OK")
                return True, "systemd reset"
            log(f"Failed to re-seed machine-id: {e}", "ERR")
            return False, str(e)

    @staticmethod
    def set_utc_timezone() -> Tuple[bool, str]:
        """Sets timezone to UTC to defeat browser javascript clock fingerprinting."""
        log("Enforcing UTC timezone", "SPOOF")
        code, out, err = run_sync("timedatectl set-timezone UTC")
        if code == 0:
            log("Timezone locked to UTC", "OK")
            return True, "UTC"
        return False, err
