import subprocess
import shlex
import time
from typing import Tuple, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread

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
