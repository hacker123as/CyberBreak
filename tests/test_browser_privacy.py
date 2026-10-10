import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cyberbreak.core.browser_privacy import BrowserPrivacyManager, CHECK_URL, FIREFOX_PREFERENCES


class BrowserPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.config_dir = self.directory / "cyberbreak"
        self.manager = BrowserPrivacyManager(config_dir=self.config_dir)

    def prepare(self):
        success, message = self.manager.prepare_profile()
        self.assertTrue(success, message)

    def create_symlink(self, link, target, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks are unavailable: {exc}")

    def test_inspection_never_creates_profile(self):
        with patch.object(self.manager, "_find_browser", return_value=None):
            result = self.manager.inspect()
        self.assertFalse(self.config_dir.exists())
        self.assertFalse(result["configured"])
        self.assertFalse(result["available"])
        self.assertTrue(result["safe"])
        self.assertEqual(result["status"], "not_created")

    def test_real_preferences_cover_requested_browser_exposures(self):
        expected = {
            "privacy.donottrackheader.enabled": True,
            "privacy.globalprivacycontrol.enabled": True,
            "network.cookie.cookieBehavior": 2,
            "network.cookie.cookieBehavior.pbmode": 2,
            "privacy.resistFingerprinting": True,
            "webgl.disabled": True,
            "media.peerconnection.enabled": False,
            "media.navigator.enabled": False,
            "geo.enabled": False,
            "dom.battery.enabled": False,
            "dom.netinfo.enabled": False,
            "browser.privatebrowsing.autostart": True,
            "browser.cache.disk.enable": False,
            "places.history.enabled": False,
            "signon.rememberSignons": False,
        }
        for name, value in expected.items():
            self.assertEqual(FIREFOX_PREFERENCES.get(name), value, name)
        self.assertNotIn("general.useragent.override", FIREFOX_PREFERENCES)
        self.assertNotIn("security.sandbox.content.level", FIREFOX_PREFERENCES)

    def test_prepare_creates_restrictive_isolated_profile(self):
        self.prepare()
        profile = self.manager.profile_path
        self.assertEqual(profile.parent, self.config_dir)
        self.assertEqual(profile.name, "browser_profile")
        result = self.manager.inspect()
        self.assertTrue(result["configured"])
        self.assertTrue(result["safe"])
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(profile.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE((profile / "user.js").stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE((profile / self.manager.MARKER_NAME).stat().st_mode), 0o600)

    def test_prepare_is_idempotent_and_preserves_other_profile_files(self):
        self.prepare()
        profile = self.manager.profile_path
        unknown = profile / "my_notes.txt"
        unknown.write_text("keep this", encoding="utf-8")
        original = (profile / "user.js").read_bytes()
        self.prepare()
        self.assertEqual((profile / "user.js").read_bytes(), original)
        self.assertEqual(unknown.read_text(encoding="utf-8"), "keep this")
        self.assertEqual(set(profile.glob(".cyberbreak-*")), {profile / self.manager.MARKER_NAME})

    def test_existing_unowned_profile_is_never_adopted_or_reset(self):
        self.manager.profile_path.mkdir(parents=True)
        prefs = self.manager.profile_path / "prefs.js"
        prefs.write_text('user_pref("existing.user", true);\n', encoding="utf-8")
        original = prefs.read_bytes()
        for operation in (self.manager.prepare_profile, self.manager.reset_profile):
            success, message = operation()
            self.assertFalse(success)
            self.assertIn("unowned", message)
            self.assertEqual(prefs.read_bytes(), original)
        self.assertFalse(self.manager.inspect()["safe"])
        self.assertFalse((self.manager.profile_path / "user.js").exists())

    def test_existing_application_settings_are_preserved(self):
        self.config_dir.mkdir()
        settings = self.config_dir / "settings.json"
        settings.write_text('{"theme": "glass"}', encoding="utf-8")
        self.prepare()
        self.assertEqual(settings.read_text(encoding="utf-8"), '{"theme": "glass"}')

    def test_non_application_directory_is_rejected(self):
        for directory in (self.directory, self.directory / "firefox", self.config_dir / ".." / "cyberbreak"):
            with self.assertRaises(ValueError):
                BrowserPrivacyManager(config_dir=directory)
        self.assertFalse(self.config_dir.exists())

    def test_symlinked_application_directory_is_rejected(self):
        destination = self.directory / "outside"
        destination.mkdir()
        self.create_symlink(self.config_dir, destination, directory=True)
        success, _ = self.manager.prepare_profile()
        self.assertFalse(success)
        self.assertEqual(list(destination.iterdir()), [])
        self.assertFalse(self.manager.inspect()["safe"])

    def test_symlinked_ancestor_directory_is_rejected(self):
        destination = self.directory / "outside"
        destination.mkdir()
        link = self.directory / "redirected"
        self.create_symlink(link, destination, directory=True)
        manager = BrowserPrivacyManager(config_dir=link / "cyberbreak")
        success, _ = manager.prepare_profile()
        self.assertFalse(success)
        self.assertEqual(list(destination.iterdir()), [])

    def test_symlinked_profile_is_rejected(self):
        self.config_dir.mkdir()
        destination = self.directory / "outside"
        destination.mkdir()
        self.create_symlink(self.manager.profile_path, destination, directory=True)
        success, _ = self.manager.prepare_profile()
        self.assertFalse(success)
        self.assertEqual(list(destination.iterdir()), [])

    def test_redirected_directory_guard_without_symlink_privileges(self):
        self.config_dir.mkdir()
        original_lstat = Path.lstat

        def redirected_lstat(path, *arguments, **options):
            if path == self.config_dir:
                return SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_file_attributes=1024)
            return original_lstat(path, *arguments, **options)

        with patch("cyberbreak.core.browser_privacy.stat.FILE_ATTRIBUTE_REPARSE_POINT", 1024, create=True), patch.object(Path, "lstat", redirected_lstat):
            self.assertFalse(self.manager.prepare_profile()[0])
            self.assertFalse(self.manager.inspect()["safe"])
        self.assertFalse(self.manager.profile_path.exists())

    def test_symlink_guard_without_symlink_privileges(self):
        self.config_dir.mkdir()
        original_lstat = Path.lstat

        def redirected_lstat(path, *arguments, **options):
            if path == self.config_dir:
                return SimpleNamespace(st_mode=stat.S_IFLNK | 0o700)
            return original_lstat(path, *arguments, **options)

        with patch.object(Path, "lstat", redirected_lstat):
            self.assertFalse(self.manager.prepare_profile()[0])
            self.assertFalse(self.manager.reset_profile()[0])
        self.assertFalse(self.manager.profile_path.exists())

    def test_symlinked_managed_file_is_rejected(self):
        self.prepare()
        outside = self.directory / "outside.js"
        outside.write_text("preserve", encoding="utf-8")
        user_js = self.manager.profile_path / "user.js"
        user_js.unlink()
        self.create_symlink(user_js, outside)
        self.assertFalse(self.manager.prepare_profile()[0])
        self.assertFalse(self.manager.reset_profile()[0])
        self.assertEqual(outside.read_text(encoding="utf-8"), "preserve")

    def test_hardlinked_managed_file_is_rejected(self):
        self.prepare()
        user_js = self.manager.profile_path / "user.js"
        outside = self.directory / "outside.js"
        try:
            os.link(user_js, outside)
        except OSError as exc:
            self.skipTest(f"Hard links are unavailable: {exc}")
        original = outside.read_bytes()
        self.assertFalse(self.manager.prepare_profile()[0])
        self.assertFalse(self.manager.reset_profile()[0])
        self.assertEqual(outside.read_bytes(), original)

    def test_wrong_directory_owner_is_rejected(self):
        self.config_dir.mkdir()
        owner = self.config_dir.stat().st_uid
        with patch("cyberbreak.core.browser_privacy.os.getuid", return_value=owner + 1, create=True):
            success, message = self.manager.prepare_profile()
        self.assertFalse(success)
        self.assertIn("does not own", message)
        self.assertFalse(self.manager.profile_path.exists())

    def test_foreign_ownership_marker_is_rejected(self):
        self.prepare()
        marker = self.manager.profile_path / self.manager.MARKER_NAME
        data = json.loads(marker.read_text(encoding="utf-8"))
        data["profile_path"] = str(self.directory / "another_profile")
        marker.write_text(json.dumps(data), encoding="utf-8")
        original = (self.manager.profile_path / "user.js").read_bytes()
        self.assertFalse(self.manager.prepare_profile()[0])
        self.assertFalse(self.manager.reset_profile()[0])
        self.assertEqual((self.manager.profile_path / "user.js").read_bytes(), original)

    def test_externally_edited_user_js_is_preserved(self):
        self.prepare()
        user_js = self.manager.profile_path / "user.js"
        original = user_js.read_text(encoding="utf-8") + 'user_pref("user.custom", 42);\n'
        user_js.write_text(original, encoding="utf-8")
        self.assertFalse(self.manager.prepare_profile()[0])
        self.assertFalse(self.manager.reset_profile()[0])
        self.assertEqual(user_js.read_text(encoding="utf-8"), original)

    def test_profile_lock_prevents_prepare_and_reset(self):
        self.prepare()
        (self.manager.profile_path / "parent.lock").touch()
        original = (self.manager.profile_path / "user.js").read_bytes()
        self.assertTrue(self.manager.inspect()["running"])
        self.assertFalse(self.manager.prepare_profile()[0])
        self.assertFalse(self.manager.reset_profile()[0])
        self.assertEqual((self.manager.profile_path / "user.js").read_bytes(), original)

    def test_launch_validates_url_before_any_write(self):
        invalid = [None, 5, "", "--profile=other", "file:///etc/passwd", "javascript:alert(1)", "https://", "https://user:password@example.com", "https://example.com\n--profile=other", "https://example.com/a b", "https://example.com:99999", "https://example.com\\other"]
        with patch("cyberbreak.core.browser_privacy.subprocess.Popen") as popen:
            for url in invalid:
                with self.subTest(url=url):
                    self.assertFalse(self.manager.launch(url)[0])
                    self.assertFalse(self.config_dir.exists())
            popen.assert_not_called()

    def test_launch_without_browser_never_writes(self):
        with patch.object(self.manager, "_find_browser", return_value=None):
            success, _ = self.manager.launch()
        self.assertFalse(success)
        self.assertFalse(self.config_dir.exists())

    def test_launch_passes_profile_and_url_as_separate_arguments(self):
        process = Mock()
        process.poll.return_value = None
        with patch.object(self.manager, "_find_browser", return_value="/usr/bin/firefox"), patch("cyberbreak.core.browser_privacy.subprocess.Popen", return_value=process) as popen:
            success, message = self.manager.launch()
        self.assertTrue(success, message)
        arguments, options = popen.call_args
        self.assertEqual(arguments[0], ["/usr/bin/firefox", "--no-remote", "--new-instance", "--profile", str(self.manager.profile_path), CHECK_URL])
        self.assertFalse(options["shell"])
        self.assertFalse(self.manager.reset_profile()[0])

    def test_reset_removes_persisted_managed_preferences_and_keeps_unknowns(self):
        self.prepare()
        profile = self.manager.profile_path
        prefs = profile / "prefs.js"
        unknown = 'user_pref("user.custom.setting", "keep this");\n'
        prefs.write_text('user_pref("webgl.disabled", true);\n' + unknown + 'user_pref("network.cookie.cookieBehavior", 2);\n', encoding="utf-8")
        other = profile / "bookmarks-backup.json"
        other.write_text("preserve", encoding="utf-8")
        success, message = self.manager.reset_profile()
        self.assertTrue(success, message)
        self.assertEqual(prefs.read_text(encoding="utf-8"), unknown)
        self.assertEqual(other.read_text(encoding="utf-8"), "preserve")
        self.assertFalse((profile / "user.js").exists())
        self.assertFalse(self.manager.inspect()["configured"])
        self.assertTrue(self.manager.reset_profile()[0])
        self.prepare()
        self.assertTrue(self.manager.inspect()["configured"])

    def test_reset_without_profile_never_creates_files(self):
        success, message = self.manager.reset_profile()
        self.assertTrue(success, message)
        self.assertFalse(self.config_dir.exists())

    def test_failed_atomic_write_preserves_previous_config(self):
        self.prepare()
        profile = self.manager.profile_path
        original = (profile / "user.js").read_bytes()
        with patch("cyberbreak.core.browser_privacy.os.replace", side_effect=OSError("replacement failed")):
            success, _ = self.manager.prepare_profile()
        self.assertFalse(success)
        self.assertEqual((profile / "user.js").read_bytes(), original)
        self.assertEqual(set(profile.glob(".cyberbreak-*")), {profile / self.manager.MARKER_NAME})


if __name__ == "__main__":
    unittest.main()
