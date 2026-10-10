import os
import shutil
from typing import Tuple, Dict
from cyberbreak.core.executor import run_sync, log

class DesktopIntegrator:
    """Linux FreeDesktop launcher, icon, and desktop environment integration engine."""

    DESKTOP_ENTRY_CONTENT = """[Desktop Entry]
Name=CyberBreak
GenericName=Security & Anti-Forensics Fortress
Comment=Hardened Privacy, Leak Detection, Hardware Spoofing & Panic Isolation
Exec=/usr/local/bin/cyberbreak
Icon=cyberbreak
Terminal=false
Type=Application
Categories=System;Security;Network;Settings;Qt;
StartupNotify=true
Keywords=security;privacy;spoofer;killswitch;tor;leak;firewall;kicksecure;
X-Kicksecure-Security-Level=Hardened
"""

    @staticmethod
    def get_status() -> Dict[str, bool]:
        """Checks if CyberBreak is integrated into desktop environments."""
        home = os.path.expanduser("~")
        desktop_file = os.path.join(home, "Desktop", "cyberbreak.desktop")
        app_grid_sys = "/usr/share/applications/cyberbreak.desktop"
        app_grid_user = os.path.join(home, ".local", "share", "applications", "cyberbreak.desktop")
        autostart_file = os.path.join(home, ".config", "autostart", "cyberbreak.desktop")

        return {
            "on_desktop": os.path.exists(desktop_file),
            "in_app_grid": os.path.exists(app_grid_sys) or os.path.exists(app_grid_user),
            "autostart": os.path.exists(autostart_file)
        }

    @staticmethod
    def install_to_desktop() -> Tuple[bool, str]:
        """Creates trusted desktop icon in ~/Desktop for current user."""
        home = os.path.expanduser("~")
        desktop_dir = os.path.join(home, "Desktop")
        os.makedirs(desktop_dir, exist_ok=True)
        desktop_file = os.path.join(desktop_dir, "cyberbreak.desktop")

        try:
            with open(desktop_file, "w") as f:
                f.write(DesktopIntegrator.DESKTOP_ENTRY_CONTENT)
            os.chmod(desktop_file, 0o755)
            # Mark trusted for GNOME/KDE/XFCE
            run_sync(f"gio set '{desktop_file}' metadata::trusted true")
            log(f"Desktop launcher created at {desktop_file}", "OK")
            return True, "Shortcut created on Desktop"
        except Exception as e:
            log(f"Failed to create desktop shortcut: {e}", "ERR")
            return False, str(e)

    @staticmethod
    def install_to_app_grid() -> Tuple[bool, str]:
        """Installs launcher into system or user-level Application Grid."""
        is_root = hasattr(os, "geteuid") and os.geteuid() == 0
        if is_root:
            app_file = "/usr/share/applications/cyberbreak.desktop"
            try:
                with open(app_file, "w") as f:
                    f.write(DesktopIntegrator.DESKTOP_ENTRY_CONTENT)
                os.chmod(app_file, 0o644)
                run_sync("update-desktop-database")
                log("Registered CyberBreak into system Application Grid", "OK")
                return True, "Added to System App Grid"
            except Exception as e:
                log(f"Failed to write /usr/share/applications: {e}", "WARN")

        # User-local applications
        user_apps = os.path.expanduser("~/.local/share/applications")
        os.makedirs(user_apps, exist_ok=True)
        local_file = os.path.join(user_apps, "cyberbreak.desktop")
        try:
            with open(local_file, "w") as f:
                f.write(DesktopIntegrator.DESKTOP_ENTRY_CONTENT)
            os.chmod(local_file, 0o644)
            run_sync(f"update-desktop-database '{user_apps}'")
            log(f"Registered into user Application Grid: {local_file}", "OK")
            return True, "Added to User App Grid"
        except Exception as e2:
            log(f"Failed to install to App Grid: {e2}", "ERR")
            return False, str(e2)

    @staticmethod
    def toggle_autostart(enable: bool) -> Tuple[bool, str]:
        """Enables or disables launch on system boot for current user."""
        home = os.path.expanduser("~")
        autostart_dir = os.path.join(home, ".config", "autostart")
        autostart_file = os.path.join(autostart_dir, "cyberbreak.desktop")

        if enable:
            os.makedirs(autostart_dir, exist_ok=True)
            try:
                with open(autostart_file, "w") as f:
                    f.write(DesktopIntegrator.DESKTOP_ENTRY_CONTENT)
                log("CyberBreak enabled for system autostart", "OK")
                return True, "Autostart Enabled"
            except Exception as e:
                return False, str(e)
        else:
            if os.path.exists(autostart_file):
                os.remove(autostart_file)
            log("CyberBreak removed from autostart", "OK")
            return True, "Autostart Disabled"
