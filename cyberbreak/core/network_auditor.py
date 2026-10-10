import ipaddress
import json
import os
import socket
import urllib.request
from typing import Dict, Any, List

from cyberbreak.core.executor import log, run_sync


class NetworkAuditor:
    ENDPOINTS = [
        "https://api.protonvpn.ch/vpn/location",
        "https://am.i.mullvad.net/json",
        "https://ifconfig.me/all.json",
        "https://api.ipify.org?format=json",
    ]
    ROUTE_TARGETS = ("1.1.1.1", "8.8.8.8")

    @staticmethod
    def _public_ip(parsed: Dict[str, Any]):
        for key in ("ip", "IP", "ip_addr", "ip_address", "ipv4", "IPv4", "ipv6", "IPv6"):
            value = parsed.get(key)
            if not isinstance(value, str):
                continue
            try:
                address = ipaddress.ip_address(value.strip())
                if address.is_global:
                    return str(address)
            except ValueError:
                pass
        return None

    @staticmethod
    def _text(parsed: Dict[str, Any], *keys: str):
        for key in keys:
            value = parsed.get(key)
            if isinstance(value, (str, int)) and not isinstance(value, bool) and str(value).strip():
                return str(value).strip()
        return "Unknown"

    @staticmethod
    def get_external_identity() -> Dict[str, Any]:
        data = {
            "ip": "Unknown", "isp": "Unknown", "country": "Unknown",
            "region": "Unknown", "city": "Unknown", "postal": "Unknown",
            "asn": "Unknown", "timezone": "Unknown", "is_mullvad": False,
            "is_proton": False, "is_tor": False, "is_leak": None,
            "raw": {}, "available": False, "status": "unavailable",
            "endpoint": None, "ip_version": None, "exit_verified": False,
            "provider": "Unknown", "proton_indicator": False,
            "public_ip_visible": None, "evidence": [], "errors": [],
        }
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for url in NetworkAuditor.ENDPOINTS:
            try:
                log(f"Querying external identity endpoint: {url}", "NET")
                request = urllib.request.Request(url, headers={"User-Agent": "CyberBreak/1.0", "Accept": "application/json"})
                with opener.open(request, timeout=6) as response:
                    parsed = json.loads(response.read(1048576).decode("utf-8"))
                if not isinstance(parsed, dict):
                    raise ValueError("Identity response is not an object")
                ip = NetworkAuditor._public_ip(parsed)
                if not ip:
                    raise ValueError("Identity response has no valid public IP address")
                data.update({
                    "ip": ip,
                    "isp": NetworkAuditor._text(parsed, "org", "organization", "Organization", "isp", "ISP"),
                    "country": NetworkAuditor._text(parsed, "country_name", "country", "Country"),
                    "region": NetworkAuditor._text(parsed, "region", "region_name", "state", "State"),
                    "city": NetworkAuditor._text(parsed, "city", "City"),
                    "postal": NetworkAuditor._text(parsed, "postal", "zip"),
                    "asn": NetworkAuditor._text(parsed, "asn", "asn_organization"),
                    "timezone": NetworkAuditor._text(parsed, "timezone"),
                    "raw": parsed, "available": True, "status": "observed",
                    "endpoint": url, "ip_version": ipaddress.ip_address(ip).version,
                    "public_ip_visible": True,
                })
                data["proton_indicator"] = "proton" in data["isp"].casefold()
                if url == "https://am.i.mullvad.net/json" and parsed.get("mullvad_exit_ip") is True:
                    data.update({"is_mullvad": True, "provider": "Mullvad", "exit_verified": True})
                    data["evidence"].append("Mullvad's HTTPS endpoint confirms this request used a Mullvad exit IP.")
                data["evidence"].append(f"{url} observed this process's direct HTTPS exit as IPv{data['ip_version']} {ip}.")
                data["evidence"].append("A visible public exit IP alone cannot establish an ISP leak or verify Proton VPN.")
                return data
            except Exception as error:
                data["errors"].append(f"{url}: {error}")
                log(f"Identity endpoint unavailable: {url}: {error}", "WARN")
        return data

    @staticmethod
    def _proton_interface(name: str) -> bool:
        name = name.casefold()
        return name.startswith(("proton", "pvpn", "wg-proton", "wgproton")) and not any(
            token in name for token in ("kill", "ksintr", "leak")
        )

    @staticmethod
    def _is_tunnel(name: str, kind: str = "") -> bool:
        if kind in ("dummy", "bridge", "veth", "bond", "vlan", "vrf"):
            return False
        return kind in ("wireguard", "tun", "tap", "ppp") or (
            kind in ("", "none") and (NetworkAuditor._proton_interface(name) or name.casefold().startswith(("tun", "tap", "wg", "ppp")))
        )

    @staticmethod
    def _links() -> Dict[str, Dict[str, Any]]:
        result = {}
        code, output, _ = run_sync(["ip", "-j", "-d", "link", "show"], shell=False)
        if code == 0:
            try:
                parsed = json.loads(output)
                if not isinstance(parsed, list):
                    raise ValueError("Link response is not a list")
                for item in parsed:
                    if not isinstance(item, dict) or not isinstance(item.get("ifname"), str):
                        continue
                    info = item.get("linkinfo") or {}
                    state = str(item.get("operstate", "UNKNOWN")).casefold()
                    result[item["ifname"]] = {
                        "up": "UP" in item.get("flags", []) and state not in ("down", "lowerlayerdown", "notpresent"),
                        "state": state, "kind": info.get("info_kind", item.get("link_type", "")), "source": "ip link",
                    }
                return result
            except (ValueError, TypeError, AttributeError):
                pass
        try:
            for name in os.listdir("/sys/class/net"):
                path = f"/sys/class/net/{name}"
                try:
                    with open(f"{path}/flags", "r") as handle:
                        flags = int(handle.read().strip(), 16)
                    with open(f"{path}/operstate", "r") as handle:
                        state = handle.read().strip().casefold()
                    if os.path.isdir(f"{path}/bridge"):
                        kind = "bridge"
                    elif os.path.exists(f"{path}/tun_flags"):
                        kind = "tun"
                    else:
                        try:
                            with open(f"{path}/type", "r") as handle:
                                kind = "" if int(handle.read().strip()) == 65534 else "other"
                        except (OSError, ValueError):
                            kind = "other"
                    result[name] = {
                        "up": bool(flags & 1) and state not in ("down", "lowerlayerdown", "notpresent"),
                        "state": state, "kind": kind, "source": "sysfs",
                    }
                except (OSError, ValueError):
                    result[name] = {"up": None, "state": "unknown", "kind": "", "source": "sysfs"}
        except OSError:
            pass
        return result

    @staticmethod
    def _route(target: str, links: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        version = ipaddress.ip_address(target).version
        result = {
            "destination": target, "interface": "Unknown", "gateway_ip": "Unknown",
            "available": False, "policy_routing_checked": False, "route_verified": False,
            "is_tunnel": False, "is_proton": False, "interface_up": None,
            "interface_kind": "", "source": None, "errors": [],
        }
        code, output, error = run_sync(["ip", "-j", f"-{version}", "route", "get", target], shell=False)
        if code == 0:
            try:
                routes = json.loads(output)
                if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
                    raise ValueError("Route lookup returned no usable result")
                route = routes[0]
                name = route.get("dev")
                if not isinstance(name, str) or route.get("type", "unicast") != "unicast":
                    raise ValueError("No usable unicast route")
                link = links.get(name, {})
                tunnel = NetworkAuditor._is_tunnel(name, link.get("kind", ""))
                up = link.get("up")
                if "linkdown" in route.get("flags", []):
                    up = False
                result.update({
                    "interface": name, "gateway_ip": route.get("gateway", "None"),
                    "available": True, "policy_routing_checked": True,
                    "route_verified": tunnel and up is True, "interface_up": up,
                    "interface_kind": link.get("kind", ""), "source": "ip route get",
                    "is_tunnel": tunnel, "is_proton": tunnel and NetworkAuditor._proton_interface(name),
                    "table": route.get("table", "main"),
                })
                return result
            except (ValueError, TypeError, AttributeError) as parse_error:
                result["errors"].append(str(parse_error))
        else:
            result["errors"].append(error or "Policy route lookup unavailable")
        if version == 6:
            return result
        try:
            candidates = []
            destination = ipaddress.ip_address(target)
            with open("/proc/net/route", "r") as handle:
                lines = handle.readlines()
            for line in lines[1:]:
                fields = line.split()
                if len(fields) < 8:
                    continue
                try:
                    flags = int(fields[3], 16)
                    if not flags & 1 or flags & 0x200:
                        continue
                    network_ip = socket.inet_ntoa(bytes.fromhex(fields[1])[::-1])
                    mask = socket.inet_ntoa(bytes.fromhex(fields[7])[::-1])
                    network = ipaddress.IPv4Network(f"{network_ip}/{mask}", strict=False)
                    if destination not in network or links.get(fields[0], {}).get("up") is False:
                        continue
                    gateway = socket.inet_ntoa(bytes.fromhex(fields[2])[::-1])
                    candidates.append((-network.prefixlen, int(fields[6]), fields[0], gateway))
                except (ValueError, OSError):
                    continue
            if candidates:
                _, metric, name, gateway = min(candidates)
                link = links.get(name, {})
                tunnel = NetworkAuditor._is_tunnel(name, link.get("kind", ""))
                result.update({
                    "interface": name, "gateway_ip": gateway, "available": True,
                    "interface_up": link.get("up"), "interface_kind": link.get("kind", ""),
                    "is_tunnel": tunnel, "is_proton": tunnel and NetworkAuditor._proton_interface(name),
                    "source": "/proc/net/route", "metric": metric,
                })
        except OSError as route_error:
            result["errors"].append(str(route_error))
        return result

    @staticmethod
    def check_default_gateway() -> Dict[str, Any]:
        links = NetworkAuditor._links()
        routes = [NetworkAuditor._route(target, links) for target in NetworkAuditor.ROUTE_TARGETS]
        result = dict(routes[0])
        result["routes"] = routes
        result["interfaces"] = links
        result["available"] = all(route["available"] for route in routes)
        result["route_verified"] = all(route["route_verified"] for route in routes)
        result["policy_routing_checked"] = all(route["policy_routing_checked"] for route in routes)
        result["is_tunnel"] = all(route["is_tunnel"] for route in routes)
        result["is_proton"] = all(route["is_proton"] for route in routes)
        result["leak_warning"] = None
        result["evidence"] = [
            f"{route['destination']} resolves via {route['interface']} using {route['source'] or 'an unavailable lookup'}."
            for route in routes
        ]
        result["errors"] = [error for route in routes for error in route["errors"]]
        if not result["available"]:
            result["status"] = "unavailable"
        elif not result["policy_routing_checked"]:
            result["status"] = "unverified"
            result["evidence"].append("The proc route table does not account for policy routing.")
        elif result["route_verified"]:
            result["status"] = "tunnel_routed"
            result["leak_warning"] = False
        elif any(route["interface_up"] is False for route in routes):
            result["status"] = "interface_down"
        elif any(route["interface_up"] is None for route in routes):
            result["status"] = "unverified"
        else:
            result["status"] = "direct_route"
            result["leak_warning"] = True
        result["evidence"].append("Sampled routes describe this host process; browser proxies and split tunneling can use a different path.")
        return result

    @staticmethod
    def audit_vpn_path(identity=None, gateway=None) -> Dict[str, Any]:
        identity = NetworkAuditor.get_external_identity() if identity is None else identity
        gateway = NetworkAuditor.check_default_gateway() if gateway is None else gateway
        routed = gateway.get("route_verified") is True
        reachable = identity.get("available") is True
        proton = gateway.get("is_proton") is True
        return {
            "available": gateway.get("available") is True,
            "detected": gateway.get("is_tunnel") is True, "route_verified": routed,
            "exit_verified": identity.get("exit_verified") is True,
            "is_connected": routed and reachable,
            "proton_detected": proton, "identity_available": reachable,
            "status": "tunnel_observed" if routed and reachable else (
                "tunnel_routed" if routed else gateway.get("status", "unavailable")
            ),
            "ip": identity.get("ip", "Unknown"), "interface": gateway.get("interface", "Unknown"),
            "identity": identity, "gateway": gateway,
            "evidence": list(gateway.get("evidence", [])) + list(identity.get("evidence", [])),
            "errors": list(gateway.get("errors", [])) + list(identity.get("errors", [])),
        }

    @staticmethod
    def check_proton_vpn(identity=None, gateway=None) -> Dict[str, Any]:
        audit = NetworkAuditor.audit_vpn_path(identity, gateway)
        identity = audit["identity"]
        links = audit["gateway"].get("interfaces")
        if not isinstance(links, dict):
            links = NetworkAuditor._links()
        detected = [name for name, link in links.items() if NetworkAuditor._proton_interface(name) and NetworkAuditor._is_tunnel(name, link.get("kind", ""))]
        proton_routed = audit["proton_detected"] and audit["route_verified"]
        connected = proton_routed and audit["identity_available"]
        interface = audit["interface"] if audit["proton_detected"] else (detected[0] if detected else "None")
        return {
            "is_connected": connected, "server": "Unverified",
            "ip": identity["ip"], "country": identity["country"],
            "city": identity["city"], "isp": identity["isp"], "interface": interface,
            "available": audit["available"], "detected": bool(detected) or audit["proton_detected"],
            "route_verified": proton_routed, "exit_verified": False,
            "identity_available": audit["identity_available"],
            "status": "route_observed" if connected else (
                "route_verified" if proton_routed else ("detected" if detected else "unavailable" if not audit["available"] else "not_detected")
            ),
            "evidence": audit["evidence"] + ["Proton interface names are local indicators; the Proton exit server identity has not been independently verified."],
            "errors": audit["errors"],
        }

    @staticmethod
    def check_dns_resolvers() -> List[str]:
        resolvers = []
        try:
            with open("/etc/resolv.conf", "r") as handle:
                for line in handle:
                    parts = line.split()
                    if len(parts) > 1 and parts[0] == "nameserver":
                        try:
                            resolver = str(ipaddress.ip_address(parts[1]))
                        except ValueError:
                            continue
                        if resolver not in resolvers:
                            resolvers.append(resolver)
            log(f"Active DNS resolver configuration: {resolvers}", "NET")
        except OSError as error:
            log(f"DNS resolver configuration unavailable: {error}", "WARN")
        return resolvers

    @staticmethod
    def check_ipv6_exposure() -> Dict[str, Any]:
        status = {
            "ipv6_supported": None, "has_global_ipv6": None, "addresses": [],
            "available": False, "status": "unavailable", "route_verified": False,
            "is_leak": None, "route": None, "evidence": [], "errors": [],
        }
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM):
                status["ipv6_supported"] = True
        except OSError as error:
            status["errors"].append(f"IPv6 socket probe: {error}")
        try:
            with open("/proc/net/if_inet6", "r") as handle:
                lines = handle.readlines()
            status["available"] = True
            status["has_global_ipv6"] = False
            for line in lines:
                fields = line.split()
                if len(fields) < 6:
                    continue
                try:
                    address = ipaddress.IPv6Address(int(fields[0], 16))
                    scope = int(fields[3], 16)
                    flags = int(fields[4], 16)
                    if scope == 0 and address.is_global and fields[5] != "lo" and not flags & (0x08 | 0x40):
                        status["has_global_ipv6"] = True
                        status["addresses"].append(f"{fields[5]}:{address}")
                except ValueError:
                    continue
            if status["has_global_ipv6"]:
                route = NetworkAuditor._route("2606:4700:4700::1111", NetworkAuditor._links())
                status["route"] = route
                status["route_verified"] = route["route_verified"]
                status["status"] = "tunnel_routed" if route["route_verified"] else (
                    "direct_route" if route["available"] and route["interface_up"] is True and not route["is_tunnel"] else "unverified"
                )
                if status["status"] == "direct_route":
                    status["is_leak"] = True
                status["errors"].extend(route["errors"])
                status["evidence"].append("A global IPv6 address is configured; sampled IPv6 routing requires separate verification.")
            else:
                status["status"] = "no_global_address"
                status["evidence"].append("No currently usable global IPv6 address was found in the Linux address table.")
        except OSError as error:
            status["errors"].append(f"IPv6 address table unavailable: {error}")
        return status
