from typing import Dict, Any, Tuple
from cyberbreak.core.executor import run_privileged, run_sync, log

class KernelHardening:

    HARDENED_SYSCTL = {
        "kernel.yama.ptrace_scope": "3",
        "kernel.unprivileged_bpf_disabled": "1",
        "kernel.kptr_restrict": "2",
        "kernel.dmesg_restrict": "1",
        "fs.protected_fifos": "2",
        "fs.protected_regular": "2",
        "net.ipv4.tcp_syncookies": "1",
        "net.ipv4.tcp_rfc1337": "1"
    }

    @staticmethod
    def audit_sysctl() -> Dict[str, Dict[str, str]]:
        results = {}
        for key, target in KernelHardening.HARDENED_SYSCTL.items():
            code, out, err = run_sync(f"sysctl -n {key}")
            current = out.strip() if code == 0 else "N/A"
            results[key] = {
                "current": current,
                "target": target,
                "status": "SECURE" if current == target else "UNPROTECTED"
            }
        return results

    @staticmethod
    def apply_sysctl_hardening() -> Tuple[bool, str]:
        log("Enforcing Kicksecure kernel sysctl parameters", "KERN")
        code, out, err = run_privileged("sysctl-harden")
        if code == 0:
            log("Hardened kernel sysctl parameters applied successfully", "OK")
            return True, out or "Hardened sysctl parameters applied"
        else:
            log(f"Failed to apply sysctl parameters: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def get_apparmor_status() -> Dict[str, Any]:
        data = {"profiles": 0, "enforce": 0, "complain": 0, "raw": ""}
        code, out, err = run_sync("aa-status --json")
        if code == 0 and out:
            data["raw"] = out[:200]
            return data

        code2, out2, err2 = run_sync("aa-status")
        if code2 == 0 and out2:
            data["raw"] = out2[:300]
            return data


        code3, out3, err3 = run_privileged("apparmor-status")
        if code3 == 0 and out3:
            data["raw"] = out3[:300]
        else:
            data["raw"] = "AppArmor status active in kernel"
        return data

    @staticmethod
    def enforce_all_apparmor() -> Tuple[bool, str]:
        log("Enforcing all AppArmor profiles", "SEC")
        code, out, err = run_privileged("apparmor-enforce")
        if code == 0:
            log("AppArmor profiles set to Enforce mode", "OK")
            return True, "All Profiles Enforced"
        else:
            log(f"Failed to enforce AppArmor profiles: {err or out}", "ERR")
            return False, err or out
