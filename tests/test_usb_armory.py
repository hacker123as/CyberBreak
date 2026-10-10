import os
import json
import secrets
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cyberbreak.core.usb_armory import USBArmory


class USBArmoryCryptoTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.config_dir = os.path.join(self.temp_dir.name, "cyberbreak")
        os.makedirs(self.config_dir, exist_ok=True)

    def test_high_entropy_password_generator(self):
        pw36 = USBArmory.generate_high_entropy_password(36)
        self.assertGreaterEqual(len(pw36), 36)
        # Check character classes
        self.assertTrue(any(c.islower() for c in pw36))
        self.assertTrue(any(c.isupper() for c in pw36))
        self.assertTrue(any(c.isdigit() for c in pw36))
        self.assertTrue(any(c in "!@#$%^&*()-_=+" for c in pw36))

        # Distinct successive keys
        pw_second = USBArmory.generate_high_entropy_password(36)
        self.assertNotEqual(pw36, pw_second)

    def test_keystore_envelope_sealing_and_unsealing(self):
        master_key = secrets.token_bytes(64)
        passcode = "SuperSecret123!@#"
        vault_id = "vault_test99"

        envelope = USBArmory._seal_master_key(master_key, passcode, vault_id)
        self.assertIn("salt", envelope)
        self.assertIn("nonce", envelope)
        self.assertIn("ciphertext", envelope)
        self.assertEqual(envelope["vault_id"], vault_id)

        # Successful unsealing with correct passcode
        ok, unsealed_key, msg = USBArmory._unseal_master_key(envelope, passcode, vault_id)
        self.assertTrue(ok, msg)
        self.assertEqual(unsealed_key, master_key)

        # Failed unsealing with incorrect passcode
        ok_bad, unsealed_bad, msg_bad = USBArmory._unseal_master_key(envelope, "WrongPasscode456!", vault_id)
        self.assertFalse(ok_bad)
        self.assertEqual(unsealed_bad, b"")
        self.assertIn("Incorrect passcode", msg_bad)

    def test_tampered_ciphertext_fails_unsealing(self):
        master_key = secrets.token_bytes(64)
        passcode = "TestPassword123"
        vault_id = "vault_tamper1"

        envelope = USBArmory._seal_master_key(master_key, passcode, vault_id)
        # Tamper with ciphertext
        ct_bytes = bytearray(bytes.fromhex(envelope["ciphertext"]))
        ct_bytes[0] ^= 0xFF
        envelope["ciphertext"] = ct_bytes.hex()

        ok, unsealed, msg = USBArmory._unseal_master_key(envelope, passcode, vault_id)
        self.assertFalse(ok)
        self.assertEqual(unsealed, b"")

    @patch("cyberbreak.core.usb_armory.run_sync")
    def test_system_storage_is_strictly_ignored(self, mock_run):
        lsblk_json = json.dumps({
            "blockdevices": [
                {
                    "name": "nvme0n1",
                    "path": "/dev/nvme0n1",
                    "size": 512110190592,
                    "mountpoint": "/",
                    "fstype": "ext4",
                    "model": "Samsung SSD 980",
                    "tran": "nvme",
                    "rm": False,
                    "children": [
                        {"name": "nvme0n1p1", "path": "/dev/nvme0n1p1", "mountpoint": "/boot/efi", "size": 536870912},
                        {"name": "nvme0n1p2", "path": "/dev/nvme0n1p2", "mountpoint": "/", "size": 511573319680}
                    ]
                },
                {
                    "name": "sda",
                    "path": "/dev/sda",
                    "size": 1000204886016,
                    "mountpoint": "/home",
                    "fstype": "ext4",
                    "model": "Internal HDD",
                    "tran": "sata",
                    "rm": False
                },
                {
                    "name": "sdb",
                    "path": "/dev/sdb",
                    "size": 64000000000,
                    "mountpoint": "",
                    "fstype": "",
                    "model": "SanDisk Ultra",
                    "tran": "usb",
                    "rm": True,
                    "children": [
                        {"name": "sdb1", "path": "/dev/sdb1", "mountpoint": "", "size": 64000000000, "fstype": "vfat", "label": "USB_DRIVE"}
                    ]
                }
            ]
        })
        mock_run.return_value = (0, lsblk_json, "")

        usb_devices = USBArmory.get_usb_devices()
        usb_paths = [d["path"] for d in usb_devices]

        # Verify system drives are completely ignored
        self.assertNotIn("/dev/nvme0n1", usb_paths)
        self.assertNotIn("/dev/nvme0n1p1", usb_paths)
        self.assertNotIn("/dev/nvme0n1p2", usb_paths)
        self.assertNotIn("/dev/sda", usb_paths)

        # Verify only genuine USB devices are accepted
        self.assertIn("/dev/sdb", usb_paths)

    @patch("cyberbreak.core.usb_armory.USBArmory.get_registry_path")
    def test_vault_registry_operations(self, mock_reg_path):
        reg_file = os.path.join(self.config_dir, "vault_registry.json")
        mock_reg_path.return_value = reg_file

        self.assertEqual(USBArmory.load_registry(), [])

        vault_entry = {
            "vault_id": "vault_alpha",
            "label": "ColdStorage",
            "device": "/dev/sdb1",
            "detached_header": True,
            "cipher": "aes-xts-plain64",
            "key_size": 512,
            "pbkdf": "argon2id"
        }
        USBArmory.save_registry([vault_entry])
        loaded = USBArmory.load_registry()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["vault_id"], "vault_alpha")
        self.assertTrue(loaded[0]["detached_header"])


if __name__ == "__main__":
    unittest.main()
