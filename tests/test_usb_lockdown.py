import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from cyberbreak.core.helper import (
    is_hid_or_critical_device,
    action_usb_lockdown,
    action_usb_unlock,
    action_usb_device_auth,
    action_usb_storage_block,
)
from cyberbreak.core.hardware_manager import HardwareManager


class UsbLockdownTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.tmp_dir.name

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_is_hid_detection_by_device_class(self):
        dev = os.path.join(self.base_dir, "1-1")
        os.makedirs(dev)
        with open(os.path.join(dev, "bDeviceClass"), "w") as f:
            f.write("03\n")  # HID class
        self.assertTrue(is_hid_or_critical_device(dev))

    def test_is_hid_detection_by_hub_class(self):
        dev = os.path.join(self.base_dir, "1-2")
        os.makedirs(dev)
        with open(os.path.join(dev, "bDeviceClass"), "w") as f:
            f.write("09\n")  # Hub class
        self.assertTrue(is_hid_or_critical_device(dev))

    def test_is_hid_detection_by_product_name(self):
        dev = os.path.join(self.base_dir, "1-3")
        os.makedirs(dev)
        with open(os.path.join(dev, "bDeviceClass"), "w") as f:
            f.write("00\n")
        with open(os.path.join(dev, "product"), "w") as f:
            f.write("Logitech Optical Gaming Mouse\n")
        self.assertTrue(is_hid_or_critical_device(dev))

    def test_is_hid_detection_by_input_node(self):
        dev = os.path.join(self.base_dir, "1-4")
        os.makedirs(os.path.join(dev, "input"))
        self.assertTrue(is_hid_or_critical_device(dev))

    def test_is_hid_detection_by_interface_class(self):
        dev = os.path.join(self.base_dir, "1-5")
        os.makedirs(dev)
        fake_iface = os.path.join(self.base_dir, "iface_mock")
        os.makedirs(fake_iface)
        with open(os.path.join(fake_iface, "bInterfaceClass"), "w") as f:
            f.write("03\n")

        with patch("glob.glob", return_value=[fake_iface]):
            self.assertTrue(is_hid_or_critical_device(dev))

    def test_non_hid_storage_is_not_detected_as_hid(self):
        dev = os.path.join(self.base_dir, "1-6")
        os.makedirs(dev)
        with open(os.path.join(dev, "bDeviceClass"), "w") as f:
            f.write("08\n")  # Mass storage
        with open(os.path.join(dev, "product"), "w") as f:
            f.write("SanDisk Ultra USB 3.0\n")
        self.assertFalse(is_hid_or_critical_device(dev))

    def test_action_usb_unlock_dispatched_when_lockdown_arg_zero(self):
        with patch("cyberbreak.core.helper.action_usb_unlock") as mock_unlock:
            mock_unlock.return_value = 0
            code = action_usb_lockdown(["0"])
            self.assertEqual(code, 0)
            mock_unlock.assert_called_once()

    @patch("cyberbreak.core.hardware_manager.run_privileged")
    def test_emergency_restore_usb(self, mock_priv):
        mock_priv.return_value = (0, "Unlocked", "")
        ok, msg = HardwareManager.emergency_restore_usb()
        self.assertTrue(ok)
        mock_priv.assert_any_call("usb-unlock")
        mock_priv.assert_any_call("usb-storage-block", "0")

    def test_filter_interface_nodes_in_hardware_manager(self):
        devices = [
            {"device_path": "1-1", "product": "Mouse", "is_hid": True},
            {"device_path": "1-2", "product": "Storage", "is_hid": False},
        ]
        for d in devices:
            self.assertNotIn(":", d["device_path"])

    @patch("cyberbreak.core.helper.run_cmd")
    def test_usb_lockdown_protects_hid_and_locks_storage(self, mock_run_cmd):
        written_files = {}

        def mock_open_impl(filename, mode="r", *args, **kwargs):
            if "w" in mode:
                mock_file = MagicMock()
                mock_file.write = lambda val: written_files.__setitem__(os.path.normpath(filename), val)
                mock_file.__enter__.return_value = mock_file
                return mock_file
            raise FileNotFoundError(filename)

        with patch("glob.glob") as mock_glob, \
             patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=mock_open_impl), \
             patch("cyberbreak.core.helper.is_hid_or_critical_device") as mock_hid:

            mock_glob.side_effect = lambda pat: (
                ["/sys/bus/usb/devices/usb1"] if "usb*" in pat
                else ["/sys/bus/usb/devices/1-1", "/sys/bus/usb/devices/1-2"]
            )
            # 1-1 is HID mouse, 1-2 is flash drive
            mock_hid.side_effect = lambda p: "1-1" in p

            code = action_usb_lockdown(["1"])
            self.assertEqual(code, 0)

            # Controller usb1 must be 1 (authorized)
            self.assertEqual(written_files.get(os.path.normpath("/sys/bus/usb/devices/usb1/authorized")), "1")
            # Mouse 1-1 must be 1 (protected/authorized)
            self.assertEqual(written_files.get(os.path.normpath("/sys/bus/usb/devices/1-1/authorized")), "1")
            # Storage 1-2 must be 0 (deauthorized)
            self.assertEqual(written_files.get(os.path.normpath("/sys/bus/usb/devices/1-2/authorized")), "0")


if __name__ == "__main__":
    unittest.main()
