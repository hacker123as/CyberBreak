import json
import socket
import urllib.request
import re
from typing import Dict, Any, List
from cyberbreak.core.executor import log

class NetworkAuditor:
    """Real socket and network probing engine with zero mock data."""

    ENDPOINTS = [
        "https://am.i.mullvad.net/json",
        "https://ifconfig.me/all.json",
        "https://api.ipify.org?format=json"
    ]

    @staticmethod
    def get_external_identity() -> Dict[str, Any]:
        """Queries external endpoints to discover public IP, ISP, and location."""
        data = {
            "ip": "Unknown",
            "isp": "Unknown",
            "country": "Unknown",
            "city": "Unknown",
            "is_mullvad": False,
            "raw": {}
        }
        for url in NetworkAuditor.ENDPOINTS:
            try:
                log(f"Querying external identity endpoint: {url}", "NET")
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "curl/7.88.1"}
                )
                with urllib.request.urlopen(req, timeout=6) as response:
                    raw_text = response.read().decode("utf-8")
                    parsed = json.loads(raw_text)
                    if "ip" in parsed:
                        data["ip"] = parsed.get("ip", "Unknown")
                        data["isp"] = parsed.get("organization", parsed.get("isp", "Unknown"))
                        data["country"] = parsed.get("country", parsed.get("country_name", "Unknown"))
                        data["city"] = parsed.get("city", "Unknown")
                        data["is_mullvad"] = parsed.get("mullvad_exit_ip", False)
                        data["raw"] = parsed
                        log(f"Identity resolved: IP={data['ip']} ISP={data['isp']}", "OK")
                        return data
            except Exception as e:
                log(f"Endpoint {url} failed: {e}", "WARN")
                continue
        return data

    @staticmethod
    def check_default_gateway() -> Dict[str, Any]:
        """Audits /proc/net/route and default gateway interface."""
        result = {
            "interface": "Unknown",
            "gateway_ip": "Unknown",
            "is_tunnel": False,
            "leak_warning": False
        }
        try:
            with open("/proc/net/route", "r") as f:
                lines = f.readlines()
            for line in lines[1:]:
                fields = line.strip().split()
                if len(fields) >= 3 and fields[1] == "00000000":  # Default route
                    iface = fields[0]
                    result["interface"] = iface
                    # Convert hex IP to quad-dotted
                    hex_gw = fields[2]
                    gw_parts = [str(int(hex_gw[i:i+2], 16)) for i in (6, 4, 2, 0)]
                    result["gateway_ip"] = ".".join(gw_parts)
                    if iface.startswith(("tun", "wg", "tap", "ppp", "virbr")):
                        result["is_tunnel"] = True
                        result["leak_warning"] = False
                    else:
                        result["is_tunnel"] = False
                        result["leak_warning"] = True
                    break
            log(f"Route check: default via {result['interface']} ({result['gateway_ip']}) Tunnel={result['is_tunnel']}", "NET")
        except Exception as e:
            log(f"Error parsing /proc/net/route: {e}", "ERR")
        return result

    @staticmethod
    def check_dns_resolvers() -> List[str]:
        """Parses active nameservers from /etc/resolv.conf."""
        resolvers = []
        try:
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("nameserver"):
                        parts = line.split()
                        if len(parts) > 1:
                            resolvers.append(parts[1])
            log(f"Active DNS resolvers detected: {resolvers}", "NET")
        except Exception as e:
            log(f"Error reading /etc/resolv.conf: {e}", "ERR")
        return resolvers

    @staticmethod
    def check_ipv6_exposure() -> Dict[str, Any]:
        """Audits IPv6 socket bindability and global addresses in /proc/net/if_inet6."""
        status = {
            "ipv6_supported": False,
            "has_global_ipv6": False,
            "addresses": []
        }
        # Check socket creation
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            s.close()
            status["ipv6_supported"] = True
        except Exception:
            status["ipv6_supported"] = False

        # Read /proc/net/if_inet6
        try:
            with open("/proc/net/if_inet6", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        raw_ip = parts[0]
                        scope = int(parts[3], 16)  # Scope 0x00 is Global
                        iface = parts[5]
                        if scope == 0x00 and iface != "lo":
                            status["has_global_ipv6"] = True
                            status["addresses"].append(f"{iface}:{raw_ip}")
            log(f"IPv6 check: Supported={status['ipv6_supported']}, GlobalLeak={status['has_global_ipv6']}", "NET")
        except FileNotFoundError:
            # IPv6 disabled in kernel
            status["has_global_ipv6"] = False
        except Exception as e:
            log(f"Error inspecting IPv6: {e}", "WARN")
        return status
