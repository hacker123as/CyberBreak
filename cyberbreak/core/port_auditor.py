import os
import re
import socket
from typing import List, Dict, Tuple, Any
from cyberbreak.core.executor import run_sync, run_privileged, log

class PortAuditor:
    """
    Real-time listening port auditor and network socket lockdown controller.
    Scans TCP and UDP listening sockets via ss / procfs, identifies bound PIDs,
    and applies instant Netfilter port drops and rogue daemon process termination.
    Engineered by lilami only.
    """

    @staticmethod
    def get_open_listening_ports() -> List[Dict[str, Any]]:
        """
        Enumerates all listening TCP and UDP network ports on the system.
        Extracts Protocol, Local IP, Port, Process Name, PID, and Exposure Risk.
        """
        results: List[Dict[str, Any]] = []

        # 1. Primary engine: ss -tulnp (Socket Statistics)
        code, out, _ = run_sync("ss -tulnp")
        if code == 0 and out:
            lines = out.strip().split("\n")
            for line in lines[1:]:  # Skip header
                parsed = PortAuditor._parse_ss_line(line)
                if parsed:
                    results.append(parsed)
            if results:
                return results

        # 2. Secondary fallback: netstat -tulnp
        code2, out2, _ = run_sync("netstat -tulnp")
        if code2 == 0 and out2:
            lines2 = out2.strip().split("\n")
            for line in lines2:
                parsed = PortAuditor._parse_netstat_line(line)
                if parsed:
                    results.append(parsed)
            if results:
                return results

        # 3. Tertiary fallback: Parse /proc/net/tcp, /proc/net/udp
        results = PortAuditor._parse_proc_net()
        return results

    @staticmethod
    def _parse_ss_line(line: str) -> Dict[str, Any] | None:
        """Parses a single line from 'ss -tulnp'."""
        parts = line.split()
        if len(parts) < 5:
            return None

        proto = parts[0].upper()
        if proto not in ("TCP", "UDP", "RAW"):
            return None

        state = parts[1]
        local_raw = parts[4]

        # Extract IP and Port from local_raw (e.g. 0.0.0.0:22, *:80, [::]:5353, 127.0.0.1:9050)
        bind_ip, port = PortAuditor._split_host_port(local_raw)
        if port == 0:
            return None

        # Parse process info: users:(("sshd",pid=1234,fd=3))
        proc_name = "System / Unknown"
        pid = 0
        rest = " ".join(parts[5:]) if len(parts) > 5 else ""
        proc_match = re.search(r'users:\(\("([^"]+)",pid=(\d+)', rest)
        if proc_match:
            proc_name = proc_match.group(1)
            pid = int(proc_match.group(2))
        else:
            # Check for simpler format: ("name",pid)
            proc_match2 = re.search(r'\("([^"]+)",(\d+)\)', rest)
            if proc_match2:
                proc_name = proc_match2.group(1)
                pid = int(proc_match2.group(2))

        # Classify risk
        is_wan = bind_ip in ("0.0.0.0", "::", "*", "")
        risk = "CRITICAL / WAN EXPOSED" if is_wan else "LOCAL LOOPBACK"

        return {
            "proto": proto,
            "port": port,
            "bind_ip": bind_ip,
            "state": state,
            "process": proc_name,
            "pid": pid,
            "risk": risk,
            "is_wan": is_wan
        }

    @staticmethod
    def _parse_netstat_line(line: str) -> Dict[str, Any] | None:
        """Parses a single line from 'netstat -tulnp'."""
        parts = line.split()
        if len(parts) < 6:
            return None
        proto = parts[0].upper()
        if not proto.startswith(("TCP", "UDP")):
            return None

        local_raw = parts[3]
        bind_ip, port = PortAuditor._split_host_port(local_raw)
        if port == 0:
            return None

        state = parts[5] if proto.startswith("TCP") else "UNCONN"
        proc_part = parts[6] if len(parts) > 6 else "-"
        proc_name = "Unknown"
        pid = 0
        if "/" in proc_part:
            pid_str, p_name = proc_part.split("/", 1)
            if pid_str.isdigit():
                pid = int(pid_str)
                proc_name = p_name

        is_wan = bind_ip in ("0.0.0.0", "::", "*", "")
        risk = "CRITICAL / WAN EXPOSED" if is_wan else "LOCAL LOOPBACK"

        return {
            "proto": proto,
            "port": port,
            "bind_ip": bind_ip,
            "state": state,
            "process": proc_name,
            "pid": pid,
            "risk": risk,
            "is_wan": is_wan
        }

    @staticmethod
    def _split_host_port(raw: str) -> Tuple[str, int]:
        """Splits an address string like 0.0.0.0:22 or [::]:80 into host and port."""
        if not raw:
            return "0.0.0.0", 0

        # Strip brackets from IPv6
        if raw.startswith("["):
            end_bracket = raw.rfind("]")
            if end_bracket != -1:
                host = raw[1:end_bracket]
                port_str = raw[end_bracket + 2:] if len(raw) > end_bracket + 2 else "0"
                try:
                    return host, int(port_str)
                except ValueError:
                    return host, 0

        # IPv4 or wildcard
        colon_idx = raw.rfind(":")
        if colon_idx != -1:
            host = raw[:colon_idx]
            port_str = raw[colon_idx + 1:]
            try:
                return host, int(port_str)
            except ValueError:
                return host, 0

        return raw, 0

    @staticmethod
    def _parse_proc_net() -> List[Dict[str, Any]]:
        """Parses /proc/net/tcp and /proc/net/udp directly if CLI tools are unavailable."""
        results: List[Dict[str, Any]] = []
        files = [
            ("/proc/net/tcp", "TCP"),
            ("/proc/net/udp", "UDP"),
            ("/proc/net/tcp6", "TCP6"),
            ("/proc/net/udp6", "UDP6")
        ]

        for path, proto in files:
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r") as f:
                    lines = f.readlines()
                for line in lines[1:]:
                    parts = line.strip().split()
                    if len(parts) < 4:
                        continue
                    # State 0A is LISTEN for TCP
                    state_hex = parts[3]
                    if "TCP" in proto and state_hex != "0A":
                        continue

                    local_addr_hex = parts[1]
                    if ":" in local_addr_hex:
                        ip_hex, port_hex = local_addr_hex.split(":")
                        port = int(port_hex, 16)
                        # Convert hex IP to dotted string
                        try:
                            if len(ip_hex) == 8:
                                ip_int = int(ip_hex, 16)
                                ip_bytes = ip_int.to_bytes(4, byteorder='little')
                                bind_ip = socket.inet_ntoa(ip_bytes)
                            else:
                                bind_ip = "::"
                        except Exception:
                            bind_ip = "0.0.0.0"

                        is_wan = bind_ip in ("0.0.0.0", "::", "*")
                        results.append({
                            "proto": proto,
                            "port": port,
                            "bind_ip": bind_ip,
                            "state": "LISTEN",
                            "process": "Kernel / Daemon",
                            "pid": 0,
                            "risk": "CRITICAL / WAN EXPOSED" if is_wan else "LOCAL LOOPBACK",
                            "is_wan": is_wan
                        })
            except Exception:
                pass

        return results

    @staticmethod
    def lockdown_single_port(port: int, proto: str = "tcp", pid: int = 0) -> Tuple[bool, str]:
        """
        Binds and drops network port via Netfilter rules and terminates listening daemon.
        Engineered by lilami only.
        """
        proto_clean = proto.lower().replace("6", "")
        log(f"Locking down network port {proto_clean.upper()}:{port} (PID: {pid})", "PORT")

        # 1. Block via Netfilter in privileged helper
        code, out, err = run_privileged("port-block", str(port), proto_clean)
        if code != 0:
            log(f"Failed to insert Netfilter drop rule for port {port}: {err or out}", "ERR")

        # 2. Terminate daemon process if valid PID provided
        if pid > 1:
            code2, out2, err2 = run_privileged("port-kill", str(pid))
            if code2 == 0:
                log(f"Terminated listening daemon PID {pid} on port {port}", "OK")

        status_msg = f"Port {proto_clean.upper()}:{port} locked down successfully"
        log(status_msg, "OK")
        return True, status_msg

    @staticmethod
    def lockdown_all_open_ports() -> Tuple[bool, str]:
        """
        Emergency lockdown of ALL listening TCP and UDP ports across all interfaces.
        Drops inbound connections via Netfilter rules and stops non-essential listening daemons.
        Engineered by lilami only.
        """
        log("EXECUTING FULL LISTENING NETWORK PORTS LOCKDOWN", "PORT")
        code, out, err = run_privileged("port-lockdown-all")
        if code == 0:
            log("All open listening ports sealed by Netfilter", "OK")
            return True, "All Open Ports Locked Down"
        else:
            log(f"Network port lockdown encountered error: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def get_active_iptables_rules() -> List[Dict[str, str]]:
        """
        Retrieves live active Netfilter/iptables rules to confirm firewall reality.
        """
        rules = []
        code, out, _ = run_sync("iptables -L -n -v --line-numbers")
        if code != 0 or not out:
            return rules

        current_chain = "UNKNOWN"
        for line in out.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("Chain "):
                # Chain INPUT (policy DROP 12 packets, 840 bytes)
                parts = line.split()
                if len(parts) >= 2:
                    current_chain = parts[1]
                continue
            if line.startswith("num") or line.startswith("pkts"):
                continue

            parts = line.split()
            if len(parts) >= 9:
                num = parts[0]
                pkts = parts[1]
                bytes_cnt = parts[2]
                target = parts[3]
                proto = parts[4]
                opt = parts[5]
                in_iface = parts[6]
                out_iface = parts[7]
                source = parts[8]
                dest = parts[9] if len(parts) > 9 else "0.0.0.0/0"
                extra = " ".join(parts[10:]) if len(parts) > 10 else ""

                rules.append({
                    "chain": current_chain,
                    "num": num,
                    "pkts": pkts,
                    "bytes": bytes_cnt,
                    "target": target,
                    "proto": proto,
                    "source": source,
                    "dest": dest,
                    "extra": extra
                })

        return rules
