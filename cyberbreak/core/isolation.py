from typing import Tuple
from cyberbreak.core.executor import run_privileged, run_sync, log

class SystemIsolation:
    """Sub-50ms emergency network blackout and process killswitch."""

    @staticmethod
    def trigger_instant_isolation() -> Tuple[bool, str]:
        """Completely severs all hardware radios, network sockets, and drops firewall via privileged helper."""
        log("EMERGENCY KILLSWITCH TRIGGERED: Initiating Total Network Blackout", "PANIC")
        code, out, err = run_privileged("emergency-isolate")
        if code == 0:
            log("SYSTEM ISOLATED: All network radios severed, firewall dropping all packets", "OK")
            return True, "SYSTEM COMPLETELY ISOLATED"
        else:
            log(f"Emergency isolation failed: {err or out}", "ERR")
            return False, err or out
