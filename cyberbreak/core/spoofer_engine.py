import os
import glob
import random
import secrets
from typing import List, Dict, Tuple
from cyberbreak.core.executor import run_sync, run_privileged, log

class SpooferEngine:

    @staticmethod
    def get_network_interfaces() -> List[Dict[str, str]]:
        interfaces = []
        net_dir = "/sys/class/net"
        if not os.path.exists(net_dir):
            return interfaces

        for iface in os.listdir(net_dir):

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
        log(f"Initiating MAC randomization sequence on {interface}", "SPOOF")
        code, out, err = run_privileged("mac-randomize", interface)
        if code == 0:
            log(f"MAC randomization completed on {interface}", "OK")
            return True, out or "MAC Randomized"
        else:
            log(f"MAC randomization failed: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def randomize_hostname() -> Tuple[bool, str]:
        prefixes = ["DESKTOP", "THINKPAD", "DEBIAN-WS", "WORKSTATION", "HOST"]
        suffix = secrets.token_hex(3).upper()
        new_name = f"{random.choice(prefixes)}-{suffix}"
        log(f"Rotating hostname to: {new_name}", "SPOOF")

        code, out, err = run_privileged("hostname-randomize", new_name)
        if code == 0:
            log(f"Hostname successfully set to {new_name}", "OK")
            return True, new_name
        else:
            log(f"Failed to set hostname: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def reseed_machine_id() -> Tuple[bool, str]:
        log("Re-seeding /etc/machine-id with random entropy", "SPOOF")
        code, out, err = run_privileged("machine-id-reseed")
        if code == 0:
            log("Machine-ID reseeded successfully", "OK")
            return True, "Reseeded"
        else:
            log(f"Failed to re-seed machine-id: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def set_utc_timezone() -> Tuple[bool, str]:
        log("Enforcing UTC timezone", "SPOOF")
        code, out, err = run_privileged("timezone-utc")
        if code == 0:
            log("Timezone locked to UTC", "OK")
            return True, "UTC"
        else:
            log(f"Failed to set UTC timezone: {err or out}", "ERR")
            return False, err or out
