from typing import Tuple
from cyberbreak.core.executor import run_sync, log

class FirewallController:
    """Linux Netfilter/iptables profile management and leak blocking."""

    @staticmethod
    def apply_strict_profile() -> Tuple[bool, str]:
        """Applies strict stateful firewall profile: drops all inbound, allows outbound."""
        log("Applying Strict Workstation firewall profile", "FW")
        cmds = [
            "iptables -F",
            "iptables -X",
            "iptables -P INPUT DROP",
            "iptables -P FORWARD DROP",
            "iptables -P OUTPUT ACCEPT",
            "iptables -A INPUT -i lo -j ACCEPT",
            "iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
            "ip6tables -P INPUT DROP",
            "ip6tables -P FORWARD DROP",
            "ip6tables -P OUTPUT DROP"
        ]
        for c in cmds:
            code, out, err = run_sync(c)
            if code != 0:
                log(f"Firewall command failed: {c} -> {err}", "ERR")
                return False, err
        log("Strict Workstation profile active", "OK")
        return True, "Strict Workstation Active"

    @staticmethod
    def apply_vpn_killswitch() -> Tuple[bool, str]:
        """Locks down all non-VPN network traffic: only allows tun/wg interfaces."""
        log("Applying VPN Killswitch profile (Zero Raw Leakage)", "FW")
        cmds = [
            "iptables -F",
            "iptables -X",
            "iptables -P INPUT DROP",
            "iptables -P FORWARD DROP",
            "iptables -P OUTPUT DROP",
            "iptables -A INPUT -i lo -j ACCEPT",
            "iptables -A OUTPUT -o lo -j ACCEPT",
            # Allow tunnel interfaces
            "iptables -A OUTPUT -o tun+ -j ACCEPT",
            "iptables -A INPUT -i tun+ -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
            "iptables -A OUTPUT -o wg+ -j ACCEPT",
            "iptables -A INPUT -i wg+ -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
            # Block all IPv6
            "ip6tables -F",
            "ip6tables -P INPUT DROP",
            "ip6tables -P FORWARD DROP",
            "ip6tables -P OUTPUT DROP"
        ]
        for c in cmds:
            code, out, err = run_sync(c)
            if code != 0:
                log(f"VPN Killswitch command failed: {c} -> {err}", "ERR")
                return False, err
        log("VPN Killswitch Active: Non-tunneled traffic blocked", "OK")
        return True, "VPN Killswitch Active"

    @staticmethod
    def reset_firewall() -> Tuple[bool, str]:
        """Flushes firewall and restores default ACCEPT policies."""
        log("Resetting firewall to standard default ACCEPT", "FW")
        cmds = [
            "iptables -F",
            "iptables -X",
            "iptables -t nat -F",
            "iptables -t nat -X",
            "iptables -P INPUT ACCEPT",
            "iptables -P FORWARD ACCEPT",
            "iptables -P OUTPUT ACCEPT",
            "ip6tables -F",
            "ip6tables -P INPUT ACCEPT",
            "ip6tables -P FORWARD ACCEPT",
            "ip6tables -P OUTPUT ACCEPT"
        ]
        for c in cmds:
            run_sync(c)
        log("Firewall reset complete", "OK")
        return True, "Firewall Reset"
