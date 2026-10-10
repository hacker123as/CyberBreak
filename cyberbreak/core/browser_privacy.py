import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


CHECK_URL = "https://pixeldefence.com/data-leaking-check/"

FIREFOX_PREFERENCES = {
    "privacy.donottrackheader.enabled": True,
    "privacy.globalprivacycontrol.enabled": True,
    "privacy.globalprivacycontrol.pbmode.enabled": True,
    "network.cookie.cookieBehavior": 2,
    "network.cookie.cookieBehavior.pbmode": 2,
    "privacy.resistFingerprinting": True,
    "privacy.resistFingerprinting.pbmode": True,
    "privacy.fingerprintingProtection": True,
    "privacy.fingerprintingProtection.pbmode": True,
    "webgl.disabled": True,
    "webgl.enable-debug-renderer-info": False,
    "media.peerconnection.enabled": False,
    "media.navigator.enabled": False,
    "media.navigator.mozgetusermedia.enabled": False,
    "geo.enabled": False,
    "dom.battery.enabled": False,
    "dom.netinfo.enabled": False,
    "device.sensors.enabled": False,
    "dom.webnotifications.enabled": False,
    "browser.contentblocking.category": "custom",
    "privacy.trackingprotection.enabled": True,
    "privacy.trackingprotection.pbmode.enabled": True,
    "privacy.trackingprotection.fingerprinting.enabled": True,
    "privacy.trackingprotection.cryptomining.enabled": True,
    "privacy.trackingprotection.socialtracking.enabled": True,
    "privacy.query_stripping.enabled": True,
    "privacy.query_stripping.enabled.pbmode": True,
    "browser.privatebrowsing.autostart": True,
    "browser.privatebrowsing.forceMediaMemoryCache": True,
    "browser.cache.disk.enable": False,
    "places.history.enabled": False,
    "browser.formfill.enable": False,
    "signon.rememberSignons": False,
    "signon.autofillForms": False,
    "signon.privateBrowsingCapture.enabled": False,
    "browser.sessionstore.resume_from_crash": False,
    "browser.sessionstore.privacy_level": 2,
    "browser.sessionstore.max_tabs_undo": 0,
    "browser.sessionstore.max_windows_undo": 0,
    "browser.sessionstore.persist_closed_tabs_between_sessions": False,
    "network.prefetch-next": False,
    "network.dns.disablePrefetch": True,
    "browser.urlbar.speculativeConnect.enabled": False,
    "dom.security.https_only_mode": True,
    "dom.security.https_only_mode_pbm": True,
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.page": 0,
    "browser.startup.homepage": "about:blank",
    "browser.newtabpage.enabled": False,
}

PROFILE_SETTINGS = (
    {"id": "signals", "label": "Privacy signals", "detail": "Do Not Track and Global Privacy Control enabled.", "preferences": ("privacy.donottrackheader.enabled", "privacy.globalprivacycontrol.enabled")},
    {"id": "cookies", "label": "Cookies", "detail": "All first-party and third-party cookies rejected.", "preferences": ("network.cookie.cookieBehavior", "network.cookie.cookieBehavior.pbmode")},
    {"id": "graphics", "label": "Graphics fingerprinting", "detail": "WebGL disabled; Firefox fingerprinting resistance enabled. Canvas hashes can still be flagged by some checkers.", "preferences": ("webgl.disabled", "privacy.resistFingerprinting", "privacy.fingerprintingProtection")},
    {"id": "webrtc", "label": "WebRTC", "detail": "Peer connections disabled to reduce browser IP exposure.", "preferences": ("media.peerconnection.enabled",)},
    {"id": "devices", "label": "Location and devices", "detail": "Geolocation, battery, network information, camera, microphone and sensor APIs disabled.", "preferences": ("geo.enabled", "dom.battery.enabled", "dom.netinfo.enabled", "media.navigator.enabled", "device.sensors.enabled")},
    {"id": "tracking", "label": "Tracking protection", "detail": "Tracking, fingerprinting, cryptomining and social-tracker blocking with query stripping.", "preferences": ("privacy.trackingprotection.enabled", "privacy.trackingprotection.fingerprinting.enabled", "privacy.trackingprotection.socialtracking.enabled", "privacy.query_stripping.enabled")},
    {"id": "storage", "label": "Local browsing data", "detail": "Private browsing, no disk cache, history, form history or saved passwords. Downloads and manually added profile data remain.", "preferences": ("browser.privatebrowsing.autostart", "browser.cache.disk.enable", "places.history.enabled", "signon.rememberSignons")},
)


class BrowserPrivacyManager:
    MARKER_NAME = ".cyberbreak-browser-profile.json"
    PROFILE_NAME = "browser_profile"

    def __init__(self, config_dir=None, browser_path=None):
        directory = Path.home() / ".config" / "cyberbreak" if config_dir is None else Path(config_dir).expanduser()
        if ".." in directory.parts or directory.name != "cyberbreak":
            raise ValueError("The browser profile must be inside an application directory named cyberbreak.")
        self._config_dir = directory.absolute()
        self._browser_path = None if browser_path is None else Path(browser_path).expanduser().absolute()
        self._process = None

    @property
    def profile_path(self):
        return self._config_dir / self.PROFILE_NAME

    @staticmethod
    def _file_exists(path):
        return os.path.lexists(path)

    @staticmethod
    def _check_path(path, directory=False, check_owner=True):
        if not os.path.lexists(path):
            return
        entry = path.lstat()
        if stat.S_ISLNK(entry.st_mode) or getattr(entry, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError(f"Refusing a symlink or redirected path: {path}")
        valid = stat.S_ISDIR(entry.st_mode) if directory else stat.S_ISREG(entry.st_mode)
        if not valid:
            raise ValueError(f"Unexpected file type: {path}")
        if check_owner and hasattr(os, "getuid") and entry.st_uid != os.getuid():
            raise ValueError(f"The current user does not own {path}")
        if not directory and entry.st_nlink != 1:
            raise ValueError(f"Refusing a linked managed file: {path}")

    def _validate_paths(self):
        for ancestor in reversed(self._config_dir.parents):
            self._check_path(ancestor, directory=True, check_owner=False)
        self._check_path(self._config_dir, directory=True)
        self._check_path(self.profile_path, directory=True)
        for name in (self.MARKER_NAME, "user.js", "prefs.js"):
            self._check_path(self.profile_path / name)

    @staticmethod
    def _render_preferences():
        return "".join(f"user_pref({json.dumps(name)}, {json.dumps(value)});\n" for name, value in FIREFOX_PREFERENCES.items())

    def _read_marker(self):
        marker_path = self.profile_path / self.MARKER_NAME
        if not marker_path.exists():
            if self.profile_path.exists() and any(self.profile_path.iterdir()):
                raise ValueError("An existing unowned browser profile was found. Its files were preserved.")
            return None
        if marker_path.stat().st_size > 32768:
            raise ValueError("The managed profile ownership file is invalid.")
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if not isinstance(marker, dict) or marker.get("application") != "cyberbreak" or marker.get("schema") != 1 or marker.get("profile_path") != str(self.profile_path):
            raise ValueError("The browser profile ownership does not match this application.")
        digest = marker.get("user_js_sha256")
        if digest is not None and (not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest)):
            raise ValueError("The managed profile ownership file is invalid.")
        return marker

    def _check_user_js(self, marker):
        user_js = self.profile_path / "user.js"
        if not user_js.exists():
            return
        if marker is None or marker.get("user_js_sha256") is None or user_js.stat().st_size > 1048576:
            raise ValueError("An unmanaged user.js file was found. It was preserved.")
        digest = hashlib.sha256(user_js.read_bytes()).hexdigest()
        if digest != marker["user_js_sha256"]:
            raise ValueError("The managed user.js was edited outside CyberBreak. It was preserved.")

    def _profile_locked(self):
        if self._process is not None and self._process.poll() is None:
            return True
        if any(self._file_exists(self.profile_path / name) for name in ("parent.lock", "lock")):
            return True
        parent_lock = self.profile_path / ".parentlock"
        if not self._file_exists(parent_lock):
            return False
        if os.name != "posix":
            return True
        try:
            import fcntl
            self._check_path(parent_lock)
            descriptor = os.open(parent_lock, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
            try:
                fcntl.lockf(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.lockf(descriptor, fcntl.LOCK_UN)
                return False
            finally:
                os.close(descriptor)
        except FileNotFoundError:
            return False
        except (OSError, ValueError):
            return True

    def _find_browser(self):
        if self._browser_path is not None:
            candidates = [str(self._browser_path)]
        else:
            candidates = [shutil.which("firefox"), shutil.which("firefox-esr"), "/usr/bin/firefox", "/usr/bin/firefox-esr", "/opt/firefox/firefox"]
            if os.name == "nt":
                candidates.extend(str(Path(os.environ[root]) / "Mozilla Firefox" / "firefox.exe") for root in ("PROGRAMFILES", "PROGRAMFILES(X86)") if os.environ.get(root))
        for candidate in candidates:
            if candidate and Path(candidate).name.lower() in ("firefox", "firefox-esr", "firefox.exe") and Path(candidate).is_file() and os.access(candidate, os.X_OK):
                return str(Path(candidate).absolute())
        return None

    def inspect(self):
        browser_path = self._find_browser()
        result = {
            "available": browser_path is not None,
            "browser_path": browser_path,
            "profile_path": str(self.profile_path),
            "configured": False,
            "safe": True,
            "running": False,
            "error": "",
            "status": "not_created",
            "preference_count": len(FIREFOX_PREFERENCES),
            "limitations": "Websites always see the public exit IP, including a VPN IP. Firefox canvas resistance may still be flagged as a unique hash. Settings apply only to this isolated profile.",
        }
        try:
            self._validate_paths()
            marker = self._read_marker()
            self._check_user_js(marker)
            user_js = self.profile_path / "user.js"
            result["configured"] = marker is not None and user_js.exists() and user_js.read_text(encoding="utf-8") == self._render_preferences()
            result["running"] = self._profile_locked()
            if result["configured"]:
                result["status"] = "configured"
            elif marker is not None:
                result["status"] = "inactive"
            if result["running"]:
                result["status"] = "in_use"
        except (OSError, ValueError, UnicodeError) as exc:
            result["safe"] = False
            result["status"] = "unavailable"
            result["error"] = str(exc)
        result["profile_status"] = result["status"]
        result["settings"] = [dict(setting, state="configured" if result["configured"] else "planned", preferences={key: FIREFOX_PREFERENCES[key] for key in setting["preferences"]}) for setting in PROFILE_SETTINGS]
        return result

    def _atomic_write(self, path, content):
        self._validate_paths()
        self._check_path(path)
        descriptor, temporary = tempfile.mkstemp(prefix=".cyberbreak-", dir=self.profile_path)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                os.chmod(temporary_path, 0o600)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            self._validate_paths()
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def prepare_profile(self):
        try:
            self._validate_paths()
            marker = self._read_marker()
            self._check_user_js(marker)
            if self._profile_locked():
                return False, "Close the managed Firefox window before changing its privacy settings. A profile lock is present."
            self._config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            self.profile_path.mkdir(mode=0o700, exist_ok=True)
            self._validate_paths()
            os.chmod(self._config_dir, 0o700)
            os.chmod(self.profile_path, 0o700)
            content = self._render_preferences()
            marker = {"application": "cyberbreak", "schema": 1, "profile_path": str(self.profile_path), "user_js_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}
            self._atomic_write(self.profile_path / self.MARKER_NAME, json.dumps(marker, indent=2) + "\n")
            self._atomic_write(self.profile_path / "user.js", content)
            return True, "Isolated Firefox privacy profile prepared. Existing Firefox and Tor profiles were preserved."
        except (OSError, ValueError, UnicodeError) as exc:
            return False, str(exc)

    @staticmethod
    def _validate_url(url):
        if not isinstance(url, str) or not url or len(url) > 4096 or "\\" in url or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in url):
            raise ValueError("Enter a valid HTTP or HTTPS URL.")
        parsed = urlsplit(url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username is not None or parsed.password is not None:
            raise ValueError("Only HTTP and HTTPS URLs without embedded credentials are supported.")
        parsed.port

    def find_any_privacy_browser(self):
        candidates = [
            shutil.which("librewolf"),
            shutil.which("tor-browser"),
            shutil.which("torbrowser-launcher"),
            shutil.which("brave-browser"),
            shutil.which("brave"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            shutil.which("google-chrome"),
            "/usr/bin/librewolf",
            "/usr/bin/torbrowser-launcher",
            "/usr/bin/brave-browser",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
                return str(Path(candidate).absolute())
        return None

    def launch_alternate_browser(self, browser_path, url):
        cmd = [browser_path]
        name = Path(browser_path).name.lower()
        if "brave" in name or "chrom" in name:
            cmd.extend(["--incognito", "--disable-sync", "--disable-plugins-discovery", url])
        elif "librewolf" in name:
            cmd.extend(["--private-window", url])
        elif "tor" in name:
            cmd.append(url)
        else:
            cmd.append(url)
        self._process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        return True, f"Launched external private browser ({Path(browser_path).name}) with anti-tracking flags."

    def launch(self, url=CHECK_URL):
        try:
            self._validate_url(url)
            browser_path = self._find_browser()
            if browser_path is None:
                alt = self.find_any_privacy_browser()
                if alt:
                    return self.launch_alternate_browser(alt, url)
                return False, "Firefox was not found. Install Firefox or Firefox ESR to use the isolated profile."
            ready, message = self.prepare_profile()
            if not ready:
                return False, message
            self._process = subprocess.Popen([browser_path, "--no-remote", "--new-instance", "--profile", str(self.profile_path), url], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            return True, "Firefox launch requested with the isolated privacy profile. Check the results in its browser window."
        except (OSError, ValueError) as exc:
            return False, f"Could not launch the private browser: {exc}"

    def reset_profile(self):
        try:
            self._validate_paths()
            marker = self._read_marker()
            if marker is None:
                return True, "No managed Firefox privacy settings exist."
            self._check_user_js(marker)
            if self._profile_locked():
                return False, "Close the managed Firefox window before resetting its privacy settings. A profile lock is present."
            prefs_path = self.profile_path / "prefs.js"
            if prefs_path.exists():
                if prefs_path.stat().st_size > 16777216:
                    return False, "The Firefox preference file is too large to reset safely. Its files were preserved."
                original = prefs_path.read_text(encoding="utf-8")
                retained = []
                for line in original.splitlines(keepends=True):
                    match = re.match(r'^\s*user_pref\(("(?:[^"\\]|\\.)*")\s*,', line)
                    if match and json.loads(match.group(1)) in FIREFOX_PREFERENCES:
                        continue
                    retained.append(line)
                cleaned = "".join(retained)
                if cleaned != original:
                    self._atomic_write(prefs_path, cleaned)
            self._validate_paths()
            (self.profile_path / "user.js").unlink(missing_ok=True)
            marker["user_js_sha256"] = None
            self._atomic_write(self.profile_path / self.MARKER_NAME, json.dumps(marker, indent=2) + "\n")
            return True, "Managed Firefox privacy settings removed. Other profile files and downloads were preserved."
        except (OSError, ValueError, UnicodeError) as exc:
            return False, str(exc)
