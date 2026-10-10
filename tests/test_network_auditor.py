import io
import json
import unittest
from unittest.mock import MagicMock, patch

from cyberbreak.core.network_auditor import NetworkAuditor


MODULE = "cyberbreak.core.network_auditor"


def link(name="proton0", kind="wireguard", state="UNKNOWN", up=True):
    return {
        "ifname": name, "flags": ["UP"] if up else [], "operstate": state,
        "link_type": "none", "linkinfo": {"info_kind": kind},
    }


def command_fixture(links=None, routes=None, unavailable=False):
    links = [link()] if links is None else links
    routes = {} if routes is None else routes

    def run(command, shell):
        if shell or not isinstance(command, list):
            raise AssertionError("Audit commands must be read-only argument lists")
        if unavailable:
            return -1, "", "ip command unavailable"
        if command == ["ip", "-j", "-d", "link", "show"]:
            return 0, json.dumps(links), ""
        if command[:5] in (["ip", "-j", "-4", "route", "get"], ["ip", "-j", "-6", "route", "get"]):
            value = routes.get(command[-1], {"dev": "proton0", "table": 51820})
            if isinstance(value, tuple):
                return value
            return 0, json.dumps([value]), ""
        raise AssertionError(f"Unexpected audit command: {command}")

    return run


def response(value):
    result = MagicMock()
    result.__enter__.return_value = result
    result.read.return_value = json.dumps(value).encode("utf-8")
    return result


class ExternalIdentityTests(unittest.TestCase):
    def fetch(self, values):
        opener = MagicMock()
        opener.open.side_effect = [value if isinstance(value, Exception) else response(value) for value in values]
        with patch(f"{MODULE}.urllib.request.build_opener", return_value=opener):
            identity = NetworkAuditor.get_external_identity()
        return identity, opener

    def test_unavailable_identity_is_unknown_not_leaked_or_protected(self):
        identity, opener = self.fetch([TimeoutError("timed out")] * len(NetworkAuditor.ENDPOINTS))
        self.assertFalse(identity["available"])
        self.assertFalse(identity["exit_verified"])
        self.assertIsNone(identity["is_leak"])
        self.assertIsNone(identity["public_ip_visible"])
        self.assertEqual(len(identity["errors"]), len(NetworkAuditor.ENDPOINTS))
        self.assertTrue(all(call.kwargs["timeout"] == 6 for call in opener.open.call_args_list))

    def test_timeout_falls_back_to_uppercase_ip_key(self):
        identity, opener = self.fetch([TimeoutError(), {"IP": "185.159.157.1", "Country": "CH"}])
        self.assertEqual(identity["ip"], "185.159.157.1")
        self.assertEqual(identity["country"], "CH")
        self.assertEqual(opener.open.call_count, 2)
        self.assertTrue(identity["available"])
        self.assertTrue(identity["public_ip_visible"])
        self.assertIsNone(identity["is_leak"])

    def test_invalid_private_and_non_object_payloads_fall_back(self):
        identity, opener = self.fetch([
            {"ip": "not an address"}, {"ip": "127.0.0.1"}, ["bad schema"], {"ip": "8.8.8.8"},
        ])
        self.assertEqual(identity["ip"], "8.8.8.8")
        self.assertEqual(opener.open.call_count, 4)

    def test_ipv4_and_ipv6_keys_and_versions(self):
        for key, address, version in (
            ("ipv4", "9.9.9.9", 4), ("IPv4", "8.8.4.4", 4),
            ("ipv6", "2606:4700:4700::1111", 6), ("IPv6", "2001:4860:4860::8888", 6),
            ("ip_addr", "1.1.1.1", 4), ("ip_address", "1.0.0.1", 4),
        ):
            with self.subTest(key=key):
                identity, _ = self.fetch([{key: address}])
                self.assertEqual(identity["ip"], address)
                self.assertEqual(identity["ip_version"], version)

    def test_provider_substrings_do_not_verify_exit_or_tor(self):
        identity, _ = self.fetch([{"IP": "185.159.157.1", "ISP": "Proton tor exit network"}])
        self.assertTrue(identity["proton_indicator"])
        self.assertFalse(identity["is_proton"])
        self.assertFalse(identity["is_tor"])
        self.assertFalse(identity["exit_verified"])
        self.assertIsNone(identity["is_leak"])

    def test_mullvad_verification_requires_boolean_from_own_endpoint(self):
        identity, _ = self.fetch([TimeoutError(), {"ip": "185.213.154.1", "mullvad_exit_ip": True}])
        self.assertTrue(identity["is_mullvad"])
        self.assertTrue(identity["exit_verified"])
        self.assertEqual(identity["provider"], "Mullvad")
        for values in (
            [{"ip": "8.8.8.8", "mullvad_exit_ip": True}],
            [TimeoutError(), {"ip": "8.8.8.8", "mullvad_exit_ip": "true"}],
        ):
            identity, _ = self.fetch(values)
            self.assertFalse(identity["exit_verified"])

    def test_configured_proxies_are_not_mixed_with_host_route_evidence(self):
        opener = MagicMock()
        opener.open.return_value = response({"ip": "1.1.1.1"})
        with patch(f"{MODULE}.urllib.request.build_opener", return_value=opener) as builder:
            NetworkAuditor.get_external_identity()
        self.assertEqual(builder.call_args.args[0].proxies, {})


class RouteTests(unittest.TestCase):
    def audit(self, links=None, routes=None):
        with patch(f"{MODULE}.run_sync", side_effect=command_fixture(links, routes)):
            return NetworkAuditor.check_default_gateway()

    def test_policy_table_route_and_unknown_operstate_wireguard_are_verified(self):
        result = self.audit()
        self.assertTrue(result["available"])
        self.assertTrue(result["route_verified"])
        self.assertTrue(result["policy_routing_checked"])
        self.assertTrue(result["is_proton"])
        self.assertEqual(result["table"], 51820)
        self.assertEqual(result["status"], "tunnel_routed")
        self.assertEqual(len(result["routes"]), 2)

    def test_interface_down_and_route_linkdown_prevent_verification(self):
        for links, routes in (
            ([link(state="DOWN")], {}),
            ([link(up=False)], {}),
            ([link()], {"1.1.1.1": {"dev": "proton0", "flags": ["linkdown"]}}),
        ):
            with self.subTest(links=links, routes=routes):
                result = self.audit(links, routes)
                self.assertFalse(result["route_verified"])
                self.assertEqual(result["status"], "interface_down")
                self.assertIsNone(result["leak_warning"])

    def test_dummy_killswitch_bridge_and_physical_proton_name_are_not_tunnels(self):
        for name, kind in (("pvpnksintrf0", "dummy"), ("virbr0", "bridge"), ("proton0", "ether")):
            with self.subTest(name=name):
                result = self.audit([link(name, kind, "UP")], {
                    target: {"dev": name} for target in NetworkAuditor.ROUTE_TARGETS
                })
                self.assertFalse(result["is_tunnel"])
                self.assertFalse(result["is_proton"])
                self.assertFalse(result["route_verified"])
                self.assertEqual(result["status"], "direct_route")

    def test_wireguard_with_arbitrary_name_is_tunnel_without_proton_attribution(self):
        result = self.audit([link("myvpn")], {target: {"dev": "myvpn"} for target in NetworkAuditor.ROUTE_TARGETS})
        self.assertTrue(result["route_verified"])
        self.assertFalse(result["is_proton"])

    def test_modern_proton_names_are_recognized(self):
        for name in ("proton0", "wg-proton0", "wgproton0", "pvpn0"):
            with self.subTest(name=name):
                result = self.audit([link(name)], {target: {"dev": name} for target in NetworkAuditor.ROUTE_TARGETS})
                self.assertTrue(result["route_verified"])
                self.assertTrue(result["is_proton"])

    def test_partial_split_route_cannot_verify_all_samples(self):
        result = self.audit([link(), link("eth0", "ether", "UP")], {
            "8.8.8.8": {"dev": "eth0", "gateway": "192.168.1.1"},
        })
        self.assertFalse(result["route_verified"])
        self.assertFalse(result["is_tunnel"])
        self.assertTrue(result["leak_warning"])

    def test_unknown_link_state_cannot_verify_route(self):
        result = self.audit([], {})
        self.assertFalse(result["route_verified"])
        self.assertEqual(result["status"], "unverified")
        self.assertIsNone(result["leak_warning"])

    def test_proc_fallback_filters_flags_and_sorts_metrics(self):
        proc = (
            "Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT\n"
            "tun0 00000000 00000000 0000 0 0 1 00000000 0 0 0\n"
            "tun1 00000000 00000000 0201 0 0 2 00000000 0 0 0\n"
            "eth0 00000000 0101A8C0 0003 0 0 500 00000000 0 0 0\n"
            "proton0 00000000 00000000 0001 0 0 50 00000000 0 0 0\n"
        )
        with patch(f"{MODULE}.NetworkAuditor._links", return_value={"proton0": {"up": True, "kind": "wireguard"}}), patch(
            f"{MODULE}.run_sync", return_value=(-1, "", "ip unavailable")
        ), patch("builtins.open", return_value=io.StringIO(proc)):
            result = NetworkAuditor._route("1.1.1.1", {"proton0": {"up": True, "kind": "wireguard"}})
        self.assertEqual(result["interface"], "proton0")
        self.assertEqual(result["metric"], 50)
        self.assertFalse(result["policy_routing_checked"])
        self.assertFalse(result["route_verified"])

    def test_proc_longest_prefix_beats_default_metric(self):
        proc = (
            "Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT\n"
            "eth0 00000000 0101A8C0 0003 0 0 1 00000000 0 0 0\n"
            "proton0 00000000 00000000 0001 0 0 100 00000080 0 0 0\n"
            "proton0 00000080 00000000 0001 0 0 100 00000080 0 0 0\n"
        )
        with patch(f"{MODULE}.run_sync", return_value=(-1, "", "missing")), patch("builtins.open", return_value=io.StringIO(proc)):
            result = NetworkAuditor._route("8.8.8.8", {"proton0": {"up": True, "kind": "wireguard"}})
        self.assertEqual(result["interface"], "proton0")
        self.assertFalse(result["route_verified"])

    def test_unavailable_route_never_reports_safe(self):
        with patch(f"{MODULE}.NetworkAuditor._links", return_value={}), patch(
            f"{MODULE}.run_sync", return_value=(-1, "", "missing")
        ), patch("builtins.open", side_effect=FileNotFoundError()):
            result = NetworkAuditor.check_default_gateway()
        self.assertFalse(result["available"])
        self.assertIsNone(result["leak_warning"])
        self.assertEqual(result["status"], "unavailable")

    def test_sysfs_fallback_requires_admin_up(self):
        values = {"flags": "0x0", "operstate": "unknown", "type": "65534"}

        def read(path, mode):
            return io.StringIO(values[path.rsplit("/", 1)[-1]])

        with patch(f"{MODULE}.run_sync", return_value=(-1, "", "missing")), patch(
            f"{MODULE}.os.listdir", return_value=["proton0"]
        ), patch(f"{MODULE}.os.path.isdir", return_value=False), patch(
            f"{MODULE}.os.path.exists", return_value=False
        ), patch("builtins.open", side_effect=read):
            links = NetworkAuditor._links()
            self.assertFalse(links["proton0"]["up"])
            values["flags"] = "0x1"
            links = NetworkAuditor._links()
            self.assertTrue(links["proton0"]["up"])


class ProtonStatusTests(unittest.TestCase):
    def identity(self, available=True):
        return {
            "available": available, "ip": "185.159.157.1" if available else "Unknown",
            "country": "CH", "city": "Unknown", "isp": "Example hosting",
            "exit_verified": False, "evidence": [], "errors": [],
        }

    def test_existing_stale_interface_does_not_connect(self):
        with patch(f"{MODULE}.run_sync", side_effect=command_fixture([link(state="DOWN"), link("eth0", "ether", "UP")], {
            target: {"dev": "eth0"} for target in NetworkAuditor.ROUTE_TARGETS
        })), patch(f"{MODULE}.NetworkAuditor.get_external_identity", return_value=self.identity()):
            result = NetworkAuditor.check_proton_vpn()
        self.assertTrue(result["detected"])
        self.assertFalse(result["is_connected"])
        self.assertFalse(result["route_verified"])
        self.assertFalse(result["exit_verified"])
        self.assertEqual(result["status"], "detected")

    def test_working_route_is_distinct_from_provider_exit_verification(self):
        with patch(f"{MODULE}.run_sync", side_effect=command_fixture()), patch(
            f"{MODULE}.NetworkAuditor.get_external_identity", return_value=self.identity()
        ):
            result = NetworkAuditor.check_proton_vpn()
        self.assertTrue(result["is_connected"])
        self.assertTrue(result["route_verified"])
        self.assertFalse(result["exit_verified"])
        self.assertEqual(result["server"], "Unverified")
        self.assertEqual(result["status"], "route_observed")

    def test_route_without_reachability_does_not_assert_connected(self):
        with patch(f"{MODULE}.run_sync", side_effect=command_fixture()), patch(
            f"{MODULE}.NetworkAuditor.get_external_identity", return_value=self.identity(False)
        ):
            result = NetworkAuditor.check_proton_vpn()
        self.assertTrue(result["route_verified"])
        self.assertFalse(result["is_connected"])
        self.assertFalse(result["identity_available"])

    def test_audit_accepts_existing_probe_results_without_queries(self):
        gateway = {"available": True, "route_verified": True, "is_proton": True, "interface": "proton0"}
        with patch(f"{MODULE}.NetworkAuditor.get_external_identity") as identity_probe, patch(
            f"{MODULE}.NetworkAuditor.check_default_gateway"
        ) as route_probe:
            audit = NetworkAuditor.audit_vpn_path(self.identity(), gateway)
        identity_probe.assert_not_called()
        route_probe.assert_not_called()
        self.assertTrue(audit["route_verified"])
        self.assertFalse(audit["exit_verified"])


class IPv6Tests(unittest.TestCase):
    def audit(self, table=None, links=None, route=None, socket_error=None):
        socket_mock = MagicMock()
        socket_mock.side_effect = socket_error
        file_mock = patch("builtins.open", side_effect=FileNotFoundError()) if table is None else patch(
            "builtins.open", return_value=io.StringIO(table)
        )
        routes = {} if route is None else {"2606:4700:4700::1111": route}
        with patch(f"{MODULE}.socket.socket", socket_mock), file_mock, patch(
            f"{MODULE}.run_sync", side_effect=command_fixture(links, routes)
        ):
            return NetworkAuditor.check_ipv6_exposure()

    def test_missing_address_probe_is_unavailable_even_when_socket_supported(self):
        result = self.audit()
        self.assertTrue(result["ipv6_supported"])
        self.assertFalse(result["available"])
        self.assertIsNone(result["has_global_ipv6"])
        self.assertIsNone(result["is_leak"])
        self.assertEqual(result["status"], "unavailable")

    def test_socket_failure_is_not_evidence_ipv6_is_safely_disabled(self):
        result = self.audit(socket_error=OSError("permission denied"))
        self.assertIsNone(result["ipv6_supported"])
        self.assertIsNone(result["has_global_ipv6"])
        self.assertFalse(result["route_verified"])

    def test_empty_valid_table_reports_no_global_address(self):
        result = self.audit("")
        self.assertTrue(result["available"])
        self.assertFalse(result["has_global_ipv6"])
        self.assertEqual(result["status"], "no_global_address")

    def test_global_ipv6_on_proton_is_routed_without_claiming_external_leak_pass(self):
        result = self.audit("26064700470000000000000000001111 01 80 00 80 proton0\n")
        self.assertTrue(result["has_global_ipv6"])
        self.assertTrue(result["route_verified"])
        self.assertEqual(result["status"], "tunnel_routed")
        self.assertIsNone(result["is_leak"])
        self.assertEqual(result["addresses"], ["proton0:2606:4700:4700::1111"])

    def test_global_ipv6_direct_route_reports_exposure(self):
        result = self.audit("26064700470000000000000000001111 01 80 00 80 eth0\n", [link("eth0", "ether", "UP")], {"dev": "eth0"})
        self.assertTrue(result["is_leak"])
        self.assertFalse(result["route_verified"])
        self.assertEqual(result["status"], "direct_route")

    def test_ipv6_route_failure_remains_unverified(self):
        result = self.audit("26064700470000000000000000001111 01 80 00 80 proton0\n", route=(-1, "", "Network unreachable"))
        self.assertTrue(result["has_global_ipv6"])
        self.assertIsNone(result["is_leak"])
        self.assertFalse(result["route_verified"])
        self.assertEqual(result["status"], "unverified")

    def test_tentative_failed_and_private_addresses_are_not_global_exposure(self):
        table = (
            "26064700470000000000000000001111 01 80 00 40 proton0\n"
            "26064700470000000000000000001112 01 80 00 08 proton0\n"
            "fd000000000000000000000000000001 01 80 00 80 proton0\n"
            "fe800000000000000000000000000001 01 80 20 80 eth0\n"
        )
        result = self.audit(table)
        self.assertFalse(result["has_global_ipv6"])
        self.assertEqual(result["addresses"], [])


class DnsTests(unittest.TestCase):
    def test_resolver_config_is_validated_and_deduplicated(self):
        table = "nameserver 127.0.0.53\nnameserver garbage\nnameserver 2606:4700:4700::1111\nnameserver 127.0.0.53\n"
        with patch("builtins.open", return_value=io.StringIO(table)):
            self.assertEqual(NetworkAuditor.check_dns_resolvers(), ["127.0.0.53", "2606:4700:4700::1111"])


if __name__ == "__main__":
    unittest.main()
