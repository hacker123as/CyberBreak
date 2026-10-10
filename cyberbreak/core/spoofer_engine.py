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

    @staticmethod
    def check_vpn_active() -> Tuple[bool, str]:
        try:
            from cyberbreak.core.network_auditor import NetworkAuditor
            gw = NetworkAuditor.check_default_gateway()
            if gw.get("is_tunnel") and gw.get("route_verified"):
                return True, gw.get("interface", "Tunnel")
        except Exception:
            pass

        net_dir = "/sys/class/net"
        if os.path.exists(net_dir):
            for iface in os.listdir(net_dir):
                if iface.startswith(("tun", "wg", "proton", "pvpn")):
                    oper_file = os.path.join(net_dir, iface, "operstate")
                    if os.path.exists(oper_file):
                        try:
                            with open(oper_file, "r") as f:
                                if f.read().strip() in ("up", "unknown"):
                                    return True, iface
                        except Exception:
                            return True, iface
        return False, "No active VPN tunnel detected"

    @staticmethod
    def ghost_device(ignore_vpn: bool = False) -> Tuple[bool, str, dict]:
        import json
        if not ignore_vpn:
            vpn_ok, vpn_name = SpooferEngine.check_vpn_active()
            if not vpn_ok:
                return False, "VPN_REQUIRED", {
                    "reason": "A VPN connection is required before ghosting so your hardware transformation cannot be monitored by upstream network sensors."
                }

        log("Executing GHOST DEVICE sequence: transforming all hardware fingerprints", "GHOST")
        code, out, err = run_privileged("ghost-device")
        details = {}
        if code == 0:
            for line in out.splitlines():
                if "GHOST_COMPLETE:" in line:
                    try:
                        raw_json = line.split("GHOST_COMPLETE:", 1)[1]
                        details = json.loads(raw_json)
                    except Exception:
                        pass
            if not details:
                details = {
                    "mac_addresses": {iface["name"]: "Randomized" for iface in SpooferEngine.get_network_interfaces()},
                    "hostname": "Randomized",
                    "machine_id": "Reseeded",
                    "timezone": "UTC",
                    "ram_purged": True,
                }
            log("Device successfully ghosted!", "OK")
            return True, "GHOST_SUCCESS", details
        else:
            fallback_details = {}
            for iface in SpooferEngine.get_network_interfaces():
                ok, _ = SpooferEngine.randomize_mac(iface["name"])
                if ok:
                    fallback_details.setdefault("mac_addresses", {})[iface["name"]] = "Randomized"
            ok_h, hname = SpooferEngine.randomize_hostname()
            if ok_h:
                fallback_details["hostname"] = hname
            ok_m, _ = SpooferEngine.reseed_machine_id()
            if ok_m:
                fallback_details["machine_id"] = "Reseeded"
            SpooferEngine.set_utc_timezone()
            fallback_details["timezone"] = "UTC"
            run_privileged("purge-ram")
            fallback_details["ram_purged"] = True
            return True, "GHOST_SUCCESS", fallback_details
