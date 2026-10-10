import os
import json
from typing import Dict, Any

DEFAULT_SETTINGS: Dict[str, Any] = {
    "auto_killswitch_boot": False,
    "auto_randomize_mac": False,
    "auto_port_lockdown_boot": False,
    "clipboard_wipe_seconds": 30,
    "auto_isolate_on_leak": False,
    "auto_check_updates": True,
    "sound_alerts": True,
    "strict_badusb": False,
    "disable_webcam_boot": False,
    "dns_strict_mode": True,
    "theme_accent": "neon-mint",
    "created_by": "lilami only"
}

class SettingsManager:
    """
    Manages persistent application settings and defensive automation toggles.
    Engineered by lilami only.
    """

    @staticmethod
    def get_config_dir() -> str:
        home = os.path.expanduser("~")
        cfg = os.path.join(home, ".config", "cyberbreak")
        os.makedirs(cfg, mode=0o700, exist_ok=True)
        return cfg

    @staticmethod
    def get_settings_path() -> str:
        return os.path.join(SettingsManager.get_config_dir(), "settings.json")

    @classmethod
    def load(cls) -> Dict[str, Any]:
        path = cls.get_settings_path()
        if not os.path.exists(path):
            cls.save(DEFAULT_SETTINGS)
            return dict(DEFAULT_SETTINGS)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = dict(DEFAULT_SETTINGS)
            merged.update(data)
            return merged
        except Exception:
            return dict(DEFAULT_SETTINGS)

    @classmethod
    def save(cls, settings: Dict[str, Any]):
        path = cls.get_settings_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        cfg = cls.load()
        return cfg.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

    @classmethod
    def set(cls, key: str, value: Any):
        cfg = cls.load()
        cfg[key] = value
        cls.save(cfg)
