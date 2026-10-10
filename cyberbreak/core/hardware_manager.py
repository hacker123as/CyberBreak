import os
from typing import Tuple
from cyberbreak.core.executor import run_privileged, run_sync, log

class HardwareManager:
    """USBGuard, BadUSB defense, Webcam, and Microphone hardware interlock."""

    @staticmethod
    def set_usb_lockdown(enable: bool) -> Tuple[bool, str]:
        """Controls USB port auto-authorization in Linux sysfs via privileged helper."""
        action = "ENABLING BadUSB defense" if enable else "DISABLING USB port lockdown"
        log(action, "HW")
        code, out, err = run_privileged("usb-lockdown", "1" if enable else "0")
        if code == 0:
            status_str = f"USB lockdown {'active' if enable else 'disabled'}"
            log(status_str, "OK")
            return True, status_str
        else:
            log(f"USB lockdown failed: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def set_webcam_state(disabled: bool) -> Tuple[bool, str]:
        """Disables or enables webcam hardware driver (uvcvideo) via privileged helper."""
        log(f"Setting webcam driver state: {'DISABLE' if disabled else 'ENABLE'}", "HW")
        code, out, err = run_privileged("webcam-toggle", "1" if disabled else "0")
        if code == 0:
            status_str = "Webcam Disabled" if disabled else "Webcam Enabled"
            log(f"Webcam state updated: {status_str}", "OK")
            return True, status_str
        else:
            log(f"Webcam toggle failed: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def set_microphone_mute(mute: bool) -> Tuple[bool, str]:
        """Toggles hardware microphone capture state in user desktop audio session."""
        log(f"Setting microphone hardware capture: {'MUTED' if mute else 'ACTIVE'}", "HW")
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
