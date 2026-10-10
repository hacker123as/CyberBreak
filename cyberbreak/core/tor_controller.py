import os
import glob
import socket
import threading
import time
import random
import urllib.request
from typing import Tuple, List, Dict, Any, Optional
from cyberbreak.core.executor import run_sync, run_privileged, log

class TorController:

    DEFAULT_SOCKETS = ["/run/tor/control", "/var/run/tor/control"]
    DEFAULT_PORTS = [9051, 9151]
    COOKIE_PATHS = [
        "/run/tor/control.authcookie",
        "/var/run/tor/control.authcookie",
        "/var/lib/tor/data/control_auth_cookie",
        os.path.expanduser("~/.tor/control_auth_cookie")
    ]

    @staticmethod
    def is_tor_running() -> bool:
        code, out, _ = run_sync("systemctl is-active tor")
        if code == 0 and "active" in out:
            return True
        code2, out2, _ = run_sync("pgrep -x tor")
        return code2 == 0

    @staticmethod
    def _read_auth_cookie() -> Optional[str]:
        for path in TorController.COOKIE_PATHS:
            if os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        data = f.read()
                        if len(data) == 32:
                            return data.hex()
                except PermissionError:

                    code, out, _ = run_privileged("tor-read-cookie")
                    if code == 0 and len(out.strip()) == 64:
                        return out.strip()
                except Exception:
                    pass

        for path in glob.glob("/run/tor-instances/*/control.authcookie"):
            try:
                with open(path, "rb") as f:
                    data = f.read()
                    if len(data) == 32:
                        return data.hex()
            except Exception:
                pass
        return None

    @staticmethod
    def _open_control_socket() -> Optional[socket.socket]:

        for u_sock in TorController.DEFAULT_SOCKETS:
            if os.path.exists(u_sock):
                try:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.settimeout(4)
                    s.connect(u_sock)
                    return s
                except Exception:
                    try:
                        s.close()
                    except Exception:
                        pass


        for port in TorController.DEFAULT_PORTS:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect(("127.0.0.1", port))
                return s
            except Exception:
                try:
                    s.close()
                except Exception:
                    pass

        return None

    @staticmethod
    def _authenticate(sock: socket.socket, password: str = "") -> bool:
        try:

            cmd = f'AUTHENTICATE "{password}"\r\n' if password else 'AUTHENTICATE ""\r\n'
            sock.sendall(cmd.encode())
            resp = sock.recv(1024).decode()
            if resp.startswith("250"):
                return True


            cookie_hex = TorController._read_auth_cookie()
            if cookie_hex:
                sock.sendall(f"AUTHENTICATE {cookie_hex}\r\n".encode())
                resp = sock.recv(1024).decode()
                if resp.startswith("250"):
                    return True


            sock.sendall(b"PROTOCOLINFO 1\r\n")
            p_info = sock.recv(2048).decode()
            cookie_match = re.search(r'COOKIEFILE="([^"]+)"', p_info)
            if cookie_match:
                c_path = cookie_match.group(1)
                if os.path.exists(c_path):
                    with open(c_path, "rb") as cf:
                        c_hex = cf.read().hex()
                    sock.sendall(f"AUTHENTICATE {c_hex}\r\n".encode())
                    resp = sock.recv(1024).decode()
                    if resp.startswith("250"):
                        return True
        except Exception:
            pass

        return False

    @staticmethod
    def signal_new_identity(password: str = "") -> Tuple[bool, str]:
        log("Sending SIGNAL NEWNYM to Tor control daemon", "TOR")
        sock = TorController._open_control_socket()
        if not sock:
            msg = "Tor Control Socket not reachable (127.0.0.1:9051 or /run/tor/control)"
            log(msg, "WARN")
            return False, msg

        try:
            with sock:
                if not TorController._authenticate(sock, password):
                    msg = "Tor Control authentication rejected"
                    log(msg, "ERR")
                    return False, msg

                sock.sendall(b"SIGNAL NEWNYM\r\n")
                resp = sock.recv(1024).decode()
                if resp.startswith("250"):
                    log("Tor circuit renewal initiated successfully (NEWNYM OK)", "OK")
                    return True, "Identity Renewed (NEWNYM OK)"
                else:
                    return False, resp.strip()
        except Exception as e:
            log(f"Tor control error: {e}", "ERR")
            return False, str(e)

    @staticmethod
    def get_tor_info() -> Dict[str, Any]:
        info = {
            "running": TorController.is_tor_running(),
            "version": "Tor N/A",
            "established": False,
            "circuits_count": 0,
            "circuits": []
        }

        sock = TorController._open_control_socket()
        if not sock:
            return info

        try:
            with sock:
                if not TorController._authenticate(sock):
                    return info


                sock.sendall(b"GETINFO version\r\n")
                v_resp = sock.recv(1024).decode()
                for line in v_resp.split("\n"):
                    if line.startswith("250-version="):
                        info["version"] = line.split("=", 1)[1].strip()


                sock.sendall(b"GETINFO status/circuit-established\r\n")
                est_resp = sock.recv(1024).decode()
                if "status/circuit-established=1" in est_resp:
                    info["established"] = True


                sock.sendall(b"GETINFO circuit-status\r\n")
                c_resp = ""
                while True:
                    chunk = sock.recv(4096).decode()
                    c_resp += chunk
                    if "250 OK" in chunk or not chunk:
                        break

                parsed_circuits = TorController._parse_circuits(c_resp)
                info["circuits"] = parsed_circuits
                info["circuits_count"] = len(parsed_circuits)
        except Exception:
            pass

        return info

    @staticmethod
    def _parse_circuits(raw: str) -> List[Dict[str, str]]:
        circuits = []
        lines = raw.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("250") or line == ".":
                continue

            parts = line.split()
            if len(parts) >= 2:
                circ_id = parts[0]
                status = parts[1]
                path_str = parts[2] if len(parts) > 2 and not parts[2].startswith("PURPOSE=") else ""
                purpose = "GENERAL"
                for p in parts:
                    if p.startswith("PURPOSE="):
                        purpose = p.split("=", 1)[1]


                hops = path_str.split(",") if path_str else []
                guard = TorController._clean_node_name(hops[0]) if len(hops) > 0 else "---"
                middle = TorController._clean_node_name(hops[1]) if len(hops) > 1 else "---"
                exit_node = TorController._clean_node_name(hops[-1]) if len(hops) > 2 else (
                    TorController._clean_node_name(hops[1]) if len(hops) == 2 else "---"
                )

                circuits.append({
                    "id": circ_id,
                    "status": status,
                    "guard": guard,
                    "middle": middle,
                    "exit": exit_node,
                    "hops_count": str(len(hops)),
                    "purpose": purpose
                })

        return circuits

    @staticmethod
    def _clean_node_name(raw: str) -> str:
        if not raw:
            return "---"
        if "~" in raw:
            return raw.split("~", 1)[1]
        if raw.startswith("$"):
            return raw[1:9]
        return raw


class DecoyTrafficGenerator(threading.Thread):

    DECOY_TARGETS = [
        "https://www.wikipedia.org",
        "https://archive.org",
        "https://www.eff.org",
        "https://www.kernel.org",
        "https://www.gnu.org",
        "https://duckduckgo.com",
        "https://www.torproject.org",
        "https://www.debian.org",
        "https://www.kicksecure.com"
    ]

    USER_AGENTS = [
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0"
    ]

    def __init__(self, interval_min: float = 3.0, interval_max: float = 9.0, log_callback=None):
        super().__init__()
        self.daemon = True
        self.running = False
        self.interval_min = interval_min
        self.interval_max = interval_max
        self.log_callback = log_callback
        self.packets_sent = 0
        self.bytes_sent = 0

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
            start_t = time.time()
            try:
                req = urllib.request.Request(target, headers={"User-Agent": ua})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    chunk = resp.read(2048)
                    size = len(chunk)
                    elapsed = round((time.time() - start_t) * 1000, 1)
                    self.packets_sent += 1
                    self.bytes_sent += size

                    msg = f"Decoy burst dispatched to {target} ({size} bytes, {elapsed}ms)"
                    log(msg, "DECOY")
                    if self.log_callback:
                        self.log_callback(target, size, elapsed, "200 OK")
            except Exception as e:
                if self.log_callback:
                    self.log_callback(target, 0, 0, f"ERR: {e}")

            sleep_duration = random.uniform(self.interval_min, self.interval_max)
            time.sleep(sleep_duration)
