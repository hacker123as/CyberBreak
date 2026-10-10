import os
from typing import Tuple
from cyberbreak.core.executor import run_privileged, log

class NukeEngine:

    MASTER_NUKE_PASSWORDS = ["1234567890", "123457890"]

    @staticmethod
    def verify_password(entered_pass: str) -> bool:
        return entered_pass.strip() in NukeEngine.MASTER_NUKE_PASSWORDS

    @staticmethod
    def execute_panic_nuke(password: str) -> Tuple[bool, str]:
        if not NukeEngine.verify_password(password):
            log("NUKE ABORTED: Passphrase verification failed", "ERR")
            return False, "Invalid passphrase authorization"

        log("CRITICAL: MASTER PANIC NUKE AUTHORIZED. DISPATCHING DESTRUCTION PIPELINE...", "PANIC")
        code, out, err = run_privileged("panic-nuke", password.strip())
        if code == 0:
            return True, "SYSTEM NUKED"
        else:
            log(f"Nuke execution failed: {err or out}", "ERR")
            return False, err or out
