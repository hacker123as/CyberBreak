import os
import shutil
from typing import Tuple, Dict
from cyberbreak.core.executor import run_sync, log

class DesktopIntegrator:

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

    BROWSER_DESKTOP_ENTRY_CONTENT = """[Desktop Entry]
Name=CyberBreak Private Browser
GenericName=Zero-Tracking Web Browser
Comment=Hardened Titanium Web Browser with 100/100 PixelDefence Anti-Fingerprinting (By lilami only)
Exec=/usr/local/bin/cyberbreak --browser %u
Icon=cyberbreak
Terminal=false
Type=Application
Categories=Network;WebBrowser;Security;
StartupNotify=true
MimeType=x-scheme-handler/http;x-scheme-handler/https;text/html;
Keywords=browser;privacy;zero-tracking;pixeldefence;webrtc;canvas;fingerprint;
X-Kicksecure-Security-Level=Hardened
"""

    @staticmethod
    def get_status() -> Dict[str, bool]:
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
        home = os.path.expanduser("~")
        desktop_dir = os.path.join(home, "Desktop")
        os.makedirs(desktop_dir, exist_ok=True)
        desktop_file = os.path.join(desktop_dir, "cyberbreak.desktop")

        try:
            with open(desktop_file, "w") as f:
                f.write(DesktopIntegrator.DESKTOP_ENTRY_CONTENT)
            os.chmod(desktop_file, 0o755)

            run_sync(f"gio set '{desktop_file}' metadata::trusted true")
            log(f"Desktop launcher created at {desktop_file}", "OK")
            return True, "Shortcut created on Desktop"
        except Exception as e:
            log(f"Failed to create desktop shortcut: {e}", "ERR")
            return False, str(e)

    @staticmethod
    def install_to_app_grid() -> Tuple[bool, str]:
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

    @staticmethod
    def install_browser_app() -> Tuple[bool, str]:
        home = os.path.expanduser("~")
        desktop_dir = os.path.join(home, "Desktop")
        user_apps_dir = os.path.join(home, ".local", "share", "applications")
        
        successes = []
        errors = []
        
        # 1. Desktop shortcut
        try:
            os.makedirs(desktop_dir, exist_ok=True)
            desktop_file = os.path.join(desktop_dir, "cyberbreak-browser.desktop")
            with open(desktop_file, "w") as f:
                f.write(DesktopIntegrator.BROWSER_DESKTOP_ENTRY_CONTENT)
            os.chmod(desktop_file, 0o755)
            run_sync(f"gio set '{desktop_file}' metadata::trusted true")
            successes.append("Desktop")
            log(f"Browser desktop launcher created at {desktop_file}", "OK")
        except Exception as e:
            errors.append(f"Desktop: {e}")
            log(f"Failed to create browser desktop launcher: {e}", "WARN")

        # 2. User Application Grid
        try:
            os.makedirs(user_apps_dir, exist_ok=True)
            user_app_file = os.path.join(user_apps_dir, "cyberbreak-browser.desktop")
            with open(user_app_file, "w") as f:
                f.write(DesktopIntegrator.BROWSER_DESKTOP_ENTRY_CONTENT)
            os.chmod(user_app_file, 0o644)
            run_sync(f"update-desktop-database '{user_apps_dir}'")
            successes.append("Applications Menu")
            log(f"Browser registered in user applications: {user_app_file}", "OK")
        except Exception as e:
            errors.append(f"Apps Menu: {e}")
            log(f"Failed to register user app grid launcher: {e}", "WARN")

        # 3. System-wide /usr/share/applications (if running as root)
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            try:
                sys_file = "/usr/share/applications/cyberbreak-browser.desktop"
                with open(sys_file, "w") as f:
                    f.write(DesktopIntegrator.BROWSER_DESKTOP_ENTRY_CONTENT)
                os.chmod(sys_file, 0o644)
                run_sync("update-desktop-database")
                successes.append("System Grid")
            except Exception as e:
                log(f"Failed to register /usr/share/applications browser launcher: {e}", "WARN")

        if successes:
            return True, f"CyberBreak Browser installed to {', '.join(successes)}!"
        return False, f"Failed to install browser launcher: {'; '.join(errors)}"
