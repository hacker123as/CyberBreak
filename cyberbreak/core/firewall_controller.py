from typing import Tuple
from cyberbreak.core.executor import run_privileged, run_sync, log

class FirewallController:
    """Linux Netfilter/iptables profile management and leak blocking."""

    @staticmethod
    def apply_strict_profile() -> Tuple[bool, str]:
        """Applies strict stateful firewall profile: drops all inbound, allows outbound."""
        log("Applying Strict Workstation firewall profile", "FW")
        code, out, err = run_privileged("firewall-strict")
        if code == 0:
            log("Strict Workstation profile active", "OK")
            return True, "Strict Workstation Active"
        else:
            log(f"Firewall profile failed: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def apply_vpn_killswitch() -> Tuple[bool, str]:
        """Locks down all non-VPN network traffic: only allows tun/wg/proton interfaces."""
        log("Applying VPN Killswitch profile (Zero Raw Leakage)", "FW")
        code, out, err = run_privileged("firewall-vpn")
        if code == 0:
            log("VPN Killswitch Active: Non-tunneled traffic blocked", "OK")
            return True, "VPN Killswitch Active"
        else:
            log(f"VPN Killswitch failed: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def apply_protonvpn_killswitch() -> Tuple[bool, str]:
        """Strictly locks all network traffic to Proton VPN tunnel interfaces and WireGuard/OpenVPN ports."""
        log("Applying Proton VPN Dedicated Killswitch", "FW")
        code, out, err = run_privileged("firewall-proton")
        if code == 0:
            log("Proton VPN Dedicated Killswitch Active", "OK")
            return True, "Proton VPN Killswitch Active"
        else:
            log(f"Proton Killswitch failed: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def reset_firewall() -> Tuple[bool, str]:
        """Flushes firewall and restores default or native Kicksecure policies."""
        log("Restoring default/native firewall policies", "FW")
        code, out, err = run_privileged("firewall-reset")
        if code == 0:
            log("Firewall policy restored", "OK")
            return True, "Firewall Reset"
        else:
            log(f"Firewall reset failed: {err or out}", "ERR")
            return False, err or out
