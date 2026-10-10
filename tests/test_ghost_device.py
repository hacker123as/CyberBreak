import json
import unittest
from unittest.mock import patch, MagicMock

from cyberbreak.core.spoofer_engine import SpooferEngine
from cyberbreak.core.helper import action_ghost_device


class GhostDeviceTests(unittest.TestCase):
    @patch("cyberbreak.core.spoofer_engine.run_privileged")
    @patch("cyberbreak.core.spoofer_engine.SpooferEngine.check_vpn_active")
    def test_ghost_device_blocks_without_vpn(self, mock_vpn, mock_priv):
        mock_vpn.return_value = (False, "No VPN")
        ok, status, details = SpooferEngine.ghost_device(ignore_vpn=False)
        self.assertFalse(ok)
        self.assertEqual(status, "VPN_REQUIRED")
        self.assertIn("reason", details)
        mock_priv.assert_not_called()

    @patch("cyberbreak.core.spoofer_engine.run_privileged")
    @patch("cyberbreak.core.spoofer_engine.SpooferEngine.check_vpn_active")
    def test_ghost_device_proceeds_with_vpn(self, mock_vpn, mock_priv):
        mock_vpn.return_value = (True, "wg0")
        mock_data = {
            "mac_addresses": {"eth0": "02:11:22:33:44:55"},
            "hostname": "DESKTOP-ABC123",
            "machine_id": "0123456789abcdef0123456789abcdef",
            "timezone": "UTC",
            "ram_purged": True,
        }
        mock_priv.return_value = (0, f"OK: GHOST_COMPLETE:{json.dumps(mock_data)}", "")

        ok, status, details = SpooferEngine.ghost_device(ignore_vpn=False)
        self.assertTrue(ok)
        self.assertEqual(status, "GHOST_SUCCESS")
        self.assertEqual(details["hostname"], "DESKTOP-ABC123")
        self.assertEqual(details["timezone"], "UTC")
        mock_priv.assert_called_once_with("ghost-device")

    @patch("cyberbreak.core.spoofer_engine.run_privileged")
    @patch("cyberbreak.core.spoofer_engine.SpooferEngine.check_vpn_active")
    def test_ghost_device_override_proceeds_without_vpn(self, mock_vpn, mock_priv):
        mock_vpn.return_value = (False, "No VPN")
        mock_data = {
            "mac_addresses": {"wlan0": "02:aa:bb:cc:dd:ee"},
            "hostname": "WORKSTATION-999",
            "machine_id": "fedcba9876543210fedcba9876543210",
            "timezone": "UTC",
            "ram_purged": True,
        }
        mock_priv.return_value = (0, f"OK: GHOST_COMPLETE:{json.dumps(mock_data)}", "")

        ok, status, details = SpooferEngine.ghost_device(ignore_vpn=True)
        self.assertTrue(ok)
        self.assertEqual(status, "GHOST_SUCCESS")
        self.assertEqual(details["hostname"], "WORKSTATION-999")
        mock_priv.assert_called_once_with("ghost-device")

    @patch("cyberbreak.core.helper.run_cmd")
    def test_action_ghost_device_helper(self, mock_run_cmd):
        mock_run_cmd.return_value = (0, "OK", "")
        with patch("os.path.exists", return_value=False), \
             patch("builtins.open", create=True):
            code = action_ghost_device([])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
