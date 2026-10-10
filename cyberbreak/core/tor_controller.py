import socket
import threading
import time
import random
import urllib.request
from typing import Tuple, List, Dict
from cyberbreak.core.executor import log

class TorController:
    """Tor control port interface and decoy cover traffic engine."""

    @staticmethod
    def signal_new_identity(control_port: int = 9051, password: str = "") -> Tuple[bool, str]:
        """Sends SIGNAL NEWNYM to Tor Control Port to force circuit renewal."""
        log("Sending SIGNAL NEWNYM to Tor control daemon", "TOR")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(("127.0.0.1", control_port))
                # Authenticate
                auth_cmd = f'AUTHENTICATE "{password}"\r\n' if password else 'AUTHENTICATE ""\r\n'
                s.sendall(auth_cmd.encode())
                auth_resp = s.recv(1024).decode()
                if not auth_resp.startswith("250"):
                    log(f"Tor authentication failed: {auth_resp.strip()}", "ERR")
                    return False, f"Auth failed: {auth_resp.strip()}"

                # Send signal
                s.sendall(b"SIGNAL NEWNYM\r\n")
                sig_resp = s.recv(1024).decode()
                if sig_resp.startswith("250"):
                    log("Tor circuit rebuild triggered (NEWNYM OK)", "OK")
                    return True, "Circuits rebuilt"
                else:
                    log(f"Tor NEWNYM rejected: {sig_resp.strip()}", "WARN")
                    return False, sig_resp.strip()
        except ConnectionRefusedError:
            log("Tor Control Port (9051) connection refused. Is Tor running?", "WARN")
            return False, "Tor daemon port 9051 not reachable"
        except Exception as e:
            log(f"Tor control error: {e}", "ERR")
            return False, str(e)

class DecoyTrafficGenerator(threading.Thread):
    """Generates synthetic background cover traffic to disrupt ISP timing attacks."""

    DECOY_TARGETS = [
        "https://www.wikipedia.org",
        "https://archive.org",
        "https://www.eff.org",
        "https://www.kernel.org",
        "https://www.gnu.org",
        "https://duckduckgo.com"
    ]

    USER_AGENTS = [
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0"
    ]

    def __init__(self, interval_min: float = 4.0, interval_max: float = 12.0):
        super().__init__()
        self.daemon = True
        self.running = False
        self.interval_min = interval_min
        self.interval_max = interval_max

    def start_generator(self):
        self.running = True
        self.start()
        log("Decoy cover traffic generator engaged", "NET")

    def stop_generator(self):
        self.running = False
        log("Decoy cover traffic generator paused", "NET")

    def run(self):
        while self.running:
            target = random.choice(self.DECOY_TARGETS)
            ua = random.choice(self.USER_AGENTS)
            try:
                req = urllib.request.Request(target, headers={"User-Agent": ua})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp.read(1024)  # read partial packet
                log(f"Decoy burst dispatched to {target}", "DECOY")
            except Exception:
                pass
            sleep_duration = random.uniform(self.interval_min, self.interval_max)
            time.sleep(sleep_duration)
