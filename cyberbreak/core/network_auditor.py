import json
import socket
import urllib.request
import re
from typing import Dict, Any, List
from cyberbreak.core.executor import log

class NetworkAuditor:
    """Real socket and network probing engine with zero mock data."""

    ENDPOINTS = [
        "https://api.protonvpn.ch/vpn/location",
        "https://am.i.mullvad.net/json",
        "https://ifconfig.me/all.json",
        "https://api.ipify.org?format=json"
    ]

    @staticmethod
    def check_proton_vpn() -> Dict[str, Any]:
        """Probes Proton VPN official location API and local interface state."""
        proton_status = {
            "is_connected": False,
            "server": "None",
            "ip": "Unknown",
            "country": "Unknown",
            "city": "Unknown",
            "isp": "Unknown",
            "interface": "None"
        }

        # 1. Query Proton VPN official API
        proton_apis = [
            "https://api.protonvpn.ch/vpn/location",
            "https://api.protonmail.ch/vpn/location"
        ]
        for api_url in proton_apis:
            try:
                log(f"Auditing Proton VPN status via {api_url}", "NET")
                req = urllib.request.Request(
                    api_url,
                    headers={"User-Agent": "ProtonVPN/3.0.0"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    raw_data = resp.read().decode("utf-8")
                    parsed = json.loads(raw_data)
                    ip = parsed.get("IP", parsed.get("ip", "Unknown"))
                    isp = parsed.get("ISP", parsed.get("isp", ""))
                    country = parsed.get("Country", parsed.get("country", ""))
                    city = parsed.get("City", parsed.get("city", ""))

                    proton_status["ip"] = ip
                    proton_status["isp"] = isp
                    proton_status["country"] = country
                    proton_status["city"] = city

                    # If ISP contains Proton or if API returns successfully from Proton network
                    if "proton" in isp.lower() or "proton" in parsed.get("Organization", "").lower():
                        proton_status["is_connected"] = True
                        proton_status["server"] = f"ProtonVPN ({country})"
                    break
            except Exception as e:
                log(f"Proton API query {api_url} check: {e}", "WARN")

        # 2. Check local network interfaces for Proton adapters (proton0, pvpn*, wg-proton*)
        try:
            import os
            net_path = "/sys/class/net"
            if os.path.exists(net_path):
                for iface in os.listdir(net_path):
                    if iface.startswith(("proton", "pvpn", "wg-proton")):
                        proton_status["interface"] = iface
                        proton_status["is_connected"] = True
                        log(f"Local Proton VPN interface detected: {iface}", "OK")
                        break
        except Exception:
            pass

        return proton_status

    @staticmethod
    def get_external_identity() -> Dict[str, Any]:
        """Queries external endpoints to discover public IP, ISP, city, state, and leak status."""
        data = {
            "ip": "Unknown",
            "isp": "Unknown",
            "country": "Unknown",
            "region": "Unknown",
            "city": "Unknown",
            "postal": "Unknown",
            "asn": "Unknown",
            "timezone": "Unknown",
            "is_mullvad": False,
            "is_proton": False,
            "is_tor": False,
            "is_leak": True,
            "raw": {}
        }
        endpoints = [
            "https://api.protonvpn.ch/vpn/location",
            "https://am.i.mullvad.net/json",
            "https://ipapi.co/json/",
            "https://ifconfig.me/all.json",
            "https://api.ipify.org?format=json"
        ]
        for url in endpoints:
            try:
                log(f"Querying external identity endpoint: {url}", "NET")
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "curl/7.88.1"}
                )
                with urllib.request.urlopen(req, timeout=6) as response:
                    raw_text = response.read().decode("utf-8")
                    parsed = json.loads(raw_text)
                    ip_val = parsed.get("ip", parsed.get("IP", "Unknown"))
                    if ip_val != "Unknown":
                        data["ip"] = ip_val
                        data["isp"] = (
                            parsed.get("org") or parsed.get("organization") or
                            parsed.get("isp") or parsed.get("ISP") or "Unknown"
                        )
                        data["country"] = (
                            parsed.get("country_name") or parsed.get("country") or
                            parsed.get("Country") or "Unknown"
                        )
                        data["region"] = (
                            parsed.get("region") or parsed.get("region_name") or
                            parsed.get("state") or parsed.get("State") or "Unknown"
                        )
                        data["city"] = parsed.get("city") or parsed.get("City") or "Unknown"
                        data["postal"] = parsed.get("postal") or parsed.get("zip") or "Unknown"
                        data["asn"] = str(parsed.get("asn") or parsed.get("asn_organization") or "Unknown")
                        data["timezone"] = parsed.get("timezone") or "Unknown"

                        data["is_mullvad"] = bool(parsed.get("mullvad_exit_ip", False))
                        isp_lower = data["isp"].lower()
                        if "proton" in isp_lower or "proton" in parsed.get("Organization", "").lower():
                            data["is_proton"] = True
                        if "tor" in isp_lower or "exit" in isp_lower:
                            data["is_tor"] = True

                        if data["is_proton"] or data["is_mullvad"] or data["is_tor"]:
                            data["is_leak"] = False
                        else:
                            data["is_leak"] = True

                        data["raw"] = parsed
                        log(
                            f"Identity resolved: IP={data['ip']} Location={data['city']}, {data['region']}, {data['country']} "
                            f"ISP={data['isp']} LeakRevealed={data['is_leak']}", "OK"
                        )
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
            "is_proton": False,
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
                    if iface.startswith(("proton", "pvpn", "wg-proton")):
                        result["is_tunnel"] = True
                        result["is_proton"] = True
                        result["leak_warning"] = False
                    elif iface.startswith(("tun", "wg", "tap", "ppp", "virbr")):
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
