from typing import Tuple
from cyberbreak.core.executor import run_sync, log

class SystemIsolation:
    """Sub-50ms emergency network blackout and process killswitch."""

    @staticmethod
    def trigger_instant_isolation() -> Tuple[bool, str]:
        """Completely severs all hardware radios, network sockets, and drops firewall."""
        log("EMERGENCY KILLSWITCH TRIGGERED: Initiating Total Network Blackout", "PANIC")
        
        # 1. Hardware RF kill
        run_sync("rfkill block all")
        
        # 2. NetworkManager disable
        run_sync("nmcli networking off")
        
        # 3. Bring down all physical interfaces
        run_sync("for iface in $(ls /sys/class/net); do [ \"$iface\" != \"lo\" ] && ip link set $iface down; done")
        
        # 4. Nuclear DROP firewall
        cmds = [
            "iptables -F",
            "iptables -X",
            "iptables -t nat -F",
            "iptables -t nat -X",
            "iptables -P INPUT DROP",
            "iptables -P FORWARD DROP",
            "iptables -P OUTPUT DROP",
            "ip6tables -F",
            "ip6tables -X",
            "ip6tables -P INPUT DROP",
            "ip6tables -P FORWARD DROP",
            "ip6tables -P OUTPUT DROP"
        ]
        for c in cmds:
            run_sync(c)

        # 5. Terminate sensitive network processes
        sensitive_procs = ["firefox", "chromium", "brave", "tor", "openvpn", "wireguard", "telegram-desktop", "signal-desktop"]
        for proc in sensitive_procs:
            run_sync(f"pkill -9 -f {proc}")

        log("SYSTEM ISOLATED: All network radios severed, firewall dropping all packets", "OK")
        return True, "SYSTEM COMPLETELY ISOLATED"
