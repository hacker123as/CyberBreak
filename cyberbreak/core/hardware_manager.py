import os
import glob
from typing import Tuple
from cyberbreak.core.executor import run_sync, log

class HardwareManager:
    """USBGuard, BadUSB defense, Webcam, and Microphone hardware interlock."""

    @staticmethod
    def set_usb_lockdown(enable: bool) -> Tuple[bool, str]:
        """Controls USB port auto-authorization in Linux sysfs."""
        val = "0" if enable else "1"
        action = "ENABLING BadUSB defense" if enable else "DISABLING USB port lockdown"
        log(action, "HW")
        success_count = 0

        # Attempt sysfs write to all USB host controllers
        usb_controllers = glob.glob("/sys/bus/usb/devices/usb*")
        for ctrl in usb_controllers:
            auth_file = os.path.join(ctrl, "authorized_default")
            if os.path.exists(auth_file):
                try:
                    with open(auth_file, "w") as f:
                        f.write(val)
                    success_count += 1
                except Exception as e:
                    # Try via sysfs echo with root
                    run_sync(f"echo {val} > {auth_file}")

        # Also signal usbguard if installed
        run_sync("usbguard set-parameter InsertedDevicePolicy block" if enable else "usbguard set-parameter InsertedDevicePolicy apply-policy")

        status_str = f"USB lockdown {'active' if enable else 'disabled'} ({success_count} controllers updated)"
        log(status_str, "OK" if success_count > 0 else "WARN")
        return True, status_str

    @staticmethod
    def set_webcam_state(disabled: bool) -> Tuple[bool, str]:
        """Disables or enables webcam hardware driver (uvcvideo)."""
        if disabled:
            log("Killing webcam driver (modprobe -r uvcvideo)", "HW")
            code, out, err = run_sync("modprobe -r uvcvideo")
            if code == 0:
                log("Webcam hardware driver neutralized (/dev/video* inaccessible)", "OK")
                return True, "Webcam Disabled"
            return False, err
        else:
            log("Reloading webcam driver (modprobe uvcvideo)", "HW")
            code, out, err = run_sync("modprobe uvcvideo")
            if code == 0:
                log("Webcam hardware driver restored", "OK")
                return True, "Webcam Enabled"
            return False, err

    @staticmethod
    def set_microphone_mute(mute: bool) -> Tuple[bool, str]:
        """Toggles hardware microphone capture state."""
        log(f"Setting microphone hardware capture: {'MUTED' if mute else 'ACTIVE'}", "HW")
        # Try pactl first, then amixer
        if mute:
            run_sync("pactl set-source-mute @DEFAULT_SOURCE@ 1")
            run_sync("amixer set Capture nocap")
            log("Microphone muted", "OK")
            return True, "Microphone Muted"
        else:
            run_sync("pactl set-source-mute @DEFAULT_SOURCE@ 0")
            run_sync("amixer set Capture cap")
            log("Microphone unmuted", "OK")
            return True, "Microphone Active"
