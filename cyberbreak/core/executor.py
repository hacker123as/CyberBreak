import os
import subprocess
import shlex
import time
from typing import Tuple, List, Optional

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QThread
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    class QObject:
        pass
    class QThread:
        def __init__(self):
            pass
        def start(self):
            self.run()
    def pyqtSignal(*args):
        class DummySignal:
            def emit(self, *a, **k):
                pass
            def connect(self, fn):
                pass
        return DummySignal()

class LogEmitter(QObject):
    log_message = pyqtSignal(str, str)  # (level, message)

GLOBAL_LOGGER = LogEmitter()

def log(message: str, level: str = "INFO"):
    timestamp = time.strftime("%H:%M:%S")
    GLOBAL_LOGGER.log_message.emit(level, f"[{timestamp}] [{level}] {message}")

class CommandWorker(QThread):
    finished_signal = pyqtSignal(int, str, str)  # (exit_code, stdout, stderr)

    def __init__(self, cmd: str, shell: bool = True):
        super().__init__()
        self.cmd = cmd
        self.shell = shell

    def run(self):
        log(f"Executing: {self.cmd}", "EXEC")
        try:
            res = subprocess.run(
                self.cmd,
                shell=self.shell,
                capture_output=True,
                text=True,
                timeout=60
            )
            out = res.stdout.strip()
            err = res.stderr.strip()
            if res.returncode == 0:
                if out:
                    log(f"Output ({res.returncode}): {out[:200]}", "OK")
            else:
                log(f"Exit {res.returncode}: {err or out}", "ERR")
            self.finished_signal.emit(res.returncode, out, err)
        except subprocess.TimeoutExpired:
            log(f"Command timed out: {self.cmd}", "ERR")
            self.finished_signal.emit(-1, "", "Command timed out")
        except Exception as e:
            log(f"Execution failure: {str(e)}", "ERR")
            self.finished_signal.emit(-1, "", str(e))

def run_sync(cmd: str, shell: bool = True) -> Tuple[int, str, str]:
    """Synchronous execution helper for instant queries."""
    try:
        res = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=15
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def get_helper_path() -> Optional[str]:
    """Finds the installed or local privileged helper executable."""
    candidates = [
        "/usr/local/lib/cyberbreak/cyberbreak-helper",
        "/usr/libexec/cyberbreak/cyberbreak-helper",
        "/opt/cyberbreak/cyberbreak/core/helper.py",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "helper.py"))
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def run_privileged(action: str, *args: str) -> Tuple[int, str, str]:
    """
    Executes a narrowly scoped privileged action via the root helper.
    Seamlessly works for restricted Kicksecure 'user' accounts via 
    pre-configured sudoers/polkit helper authorizations.
    """
    helper = get_helper_path()
    cmd_args = [action] + [str(a) for a in args]

    if not helper:
        err_msg = (
            f"Privileged helper not found for '{action}'. "
            "Please run installation from your 'sysmaint' account: "
            "sudo bash /opt/cyberbreak/scripts/install.sh"
        )
        log(err_msg, "ERR")
        return -1, "", err_msg

    # Ensure executable
    if not os.access(helper, os.X_OK):
        try:
            os.chmod(helper, 0o755)
        except Exception:
            pass

    # 1. If current process is already root
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        log(f"Executing privileged action (direct root): {action}", "EXEC")
        try:
            res = subprocess.run([helper] + cmd_args, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                log(f"Privileged OK: {res.stdout.strip()[:200]}", "OK")
            else:
                log(f"Privileged Error ({res.returncode}): {res.stderr.strip() or res.stdout.strip()}", "ERR")
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            return -1, "", str(e)

    # 2. If unprivileged user: attempt passwordless sudo via configured cyberbreak group
    log(f"Dispatching privileged action '{action}' via helper", "EXEC")
    try:
        res = subprocess.run(["sudo", "-n", helper] + cmd_args, capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            if res.stdout.strip():
                log(f"Privileged OK: {res.stdout.strip()[:200]}", "OK")
            return 0, res.stdout.strip(), res.stderr.strip()

        # If sudo -n failed because password required or user not in cyberbreak group, fallback to pkexec
        err_lower = (res.stderr or "").lower()
        if "password" in err_lower or "not in sudoers" in err_lower or res.returncode in (1, 13):
            log("Sudo -n not configured; attempting Polkit pkexec escalation", "WARN")
            pk_res = subprocess.run(["pkexec", helper] + cmd_args, capture_output=True, text=True, timeout=60)
            if pk_res.returncode == 0:
                log(f"Polkit OK: {pk_res.stdout.strip()[:200]}", "OK")
            else:
                log(f"Polkit failed ({pk_res.returncode}): {pk_res.stderr.strip()}", "ERR")
            return pk_res.returncode, pk_res.stdout.strip(), pk_res.stderr.strip()

        return res.returncode, res.stdout.strip(), res.stderr.strip()

    except FileNotFoundError:
        # sudo not installed, attempt pkexec directly
        try:
            pk_res = subprocess.run(["pkexec", helper] + cmd_args, capture_output=True, text=True, timeout=60)
            return pk_res.returncode, pk_res.stdout.strip(), pk_res.stderr.strip()
        except Exception as e2:
            err_msg = (
                f"Privilege escalation failed for '{action}': {e2}. "
                "Ensure CyberBreak was installed from 'sysmaint' via install.sh."
            )
            log(err_msg, "ERR")
            return -1, "", err_msg
    except Exception as e:
        err_msg = f"Privileged helper failed: {e}"
        log(err_msg, "ERR")
        return -1, "", err_msg
