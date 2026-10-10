import os
import glob
from typing import Tuple
from cyberbreak.core.executor import run_sync, log

class NukeEngine:
    """Anti-forensic drive obliteration and emergency cryptographic shredder."""

    MASTER_NUKE_PASSWORDS = ["1234567890", "123457890"]

    @staticmethod
    def verify_password(entered_pass: str) -> bool:
        """Verifies confirmation passphrase before enabling destruction."""
        if entered_pass in NukeEngine.MASTER_NUKE_PASSWORDS:
            return True
        # Allow system root password if authenticates via sudo
        code, out, err = run_sync(f"echo '{entered_pass}' | sudo -S true")
        return code == 0

    @staticmethod
    def execute_panic_nuke(password: str) -> Tuple[bool, str]:
        """Executes multi-tier irreversible drive wipe and immediate kernel panic."""
        if not NukeEngine.verify_password(password):
            log("NUKE ABORTED: Passphrase verification failed", "ERR")
            return False, "Invalid passphrase authorization"

        log("CRITICAL: MASTER PANIC NUKE AUTHORIZED. EXECUTING DESTRUCTION PIPELINE...", "PANIC")

        # Discover all block storage devices
        block_devices = glob.glob("/dev/sd[a-z]") + glob.glob("/dev/nvme[0-9]n[0-9]") + glob.glob("/dev/vd[a-z]")
        partitions = glob.glob("/dev/sd[a-z][0-9]*") + glob.glob("/dev/nvme[0-9]n[0-9]p[0-9]*")

        # Tier 1: LUKS Header Erase
        for part in partitions:
            log(f"Wiping LUKS cryptographic keyslots on {part}", "NUKE")
            run_sync(f"cryptsetup luksErase --batch-mode {part}")
            # Overwrite first 16MB of partition with urandom
            run_sync(f"dd if=/dev/urandom of={part} bs=1M count=16 status=none conv=fsync")

        # Tier 2: NVMe/SSD Hardware Block Discard
        for dev in block_devices:
            log(f"Executing blkdiscard hardware wipe on {dev}", "NUKE")
            run_sync(f"blkdiscard -f -z {dev}")
            # Zap partition tables
            run_sync(f"sgdisk --zap-all {dev}")

        # Tier 3: Memory Sync and Instant Kernel Crash Panic
        log("Triggering anti-cold-boot intentional kernel crash panic", "NUKE")
        run_sync("sync")
        run_sync("echo 1 > /proc/sys/kernel/sysrq")
        # sysrq c crashes the kernel immediately, preventing DRAM decay forensic dumps
        run_sync("echo c > /proc/sysrq-trigger")

        return True, "SYSTEM NUKED"
