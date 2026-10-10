import os
import glob
from typing import Tuple, List, Dict, Any
from cyberbreak.core.executor import run_privileged, run_sync, log

class HardwareManager:
    """
    BadUSB defense, USB port lockdown, device authorization, webcam, and microphone hardware interlocks.
    Engineered by lilami only.
    """

    @staticmethod
    def get_connected_usb_devices() -> List[Dict[str, Any]]:
        """
        Enumerates all physical and logical USB devices connected to system controllers.
        Extracts Bus, DevNum, Vendor:Product ID, Manufacturer, Product Name, and Authorization status.
        """
        devices: List[Dict[str, Any]] = []
        base_dir = "/sys/bus/usb/devices"
        if not os.path.exists(base_dir):
            return devices

        for entry in sorted(os.listdir(base_dir)):
            # Device entries match digits and dashes (e.g. 1-1, 1-1.2, usb1, usb2)
            dev_path = os.path.join(base_dir, entry)
            if not os.path.isdir(dev_path):
                continue

            # Check if it has an idVendor or is a root hub
            vendor_path = os.path.join(dev_path, "idVendor")
            product_path = os.path.join(dev_path, "idProduct")
            auth_path = os.path.join(dev_path, "authorized")

            if not os.path.exists(auth_path) and not os.path.exists(vendor_path):
                continue

            vendor = HardwareManager._read_sysfs(vendor_path, "0000")
            product_id = HardwareManager._read_sysfs(product_path, "0000")
            manufacturer = HardwareManager._read_sysfs(os.path.join(dev_path, "manufacturer"), "Generic OEM")
            product_name = HardwareManager._read_sysfs(os.path.join(dev_path, "product"), f"USB Device {entry}")
            busnum = HardwareManager._read_sysfs(os.path.join(dev_path, "busnum"), "1")
            devnum = HardwareManager._read_sysfs(os.path.join(dev_path, "devnum"), "1")
            speed = HardwareManager._read_sysfs(os.path.join(dev_path, "speed"), "USB")
            auth_val = HardwareManager._read_sysfs(auth_path, "1")

            is_root_hub = entry.startswith("usb")
            is_authorized = (auth_val == "1")

            # Determine device class
            dev_type = HardwareManager._determine_device_type(dev_path, is_root_hub, product_name)

            devices.append({
                "dev_id": entry,
                "bus": busnum,
                "devnum": devnum,
                "vid_pid": f"{vendor}:{product_id}".lower(),
                "vendor": vendor,
                "product_id": product_id,
                "manufacturer": manufacturer,
                "product": product_name,
                "speed": f"{speed} Mbps" if speed.isdigit() else speed,
                "authorized": is_authorized,
                "is_root_hub": is_root_hub,
                "type": dev_type
            })

        return devices

    @staticmethod
    def _read_sysfs(path: str, default: str = "") -> str:
        """Safely reads a single line from a sysfs node."""
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return f.read().strip()
            except Exception:
                pass
        return default

    @staticmethod
    def _determine_device_type(dev_path: str, is_root: bool, prod_name: str) -> str:
        """Classifies USB device role based on interface descriptors and name."""
        if is_root:
            return "ROOT HUB"

        name_lower = prod_name.lower()
        if any(w in name_lower for w in ("keyboard", "mouse", "pointer", "touchpad", "trackball")):
            return "HID / INPUT"
        if any(w in name_lower for w in ("flash", "storage", "disk", "drive", "cruzer", "sandisk", "kingston")):
            return "MASS STORAGE"
        if any(w in name_lower for w in ("camera", "webcam", "video")):
            return "VIDEO / CAM"
        if any(w in name_lower for w in ("audio", "headset", "microphone", "sound")):
            return "AUDIO"
        if any(w in name_lower for w in ("wireless", "wifi", "802.11", "ethernet", "lan", "bluetooth")):
            return "NETWORK / COMM"

        # Check sub-interfaces for bInterfaceClass (08 = Mass Storage, 03 = HID)
        for iface_dir in glob.glob(os.path.join(dev_path, "*:*")):
            class_path = os.path.join(iface_dir, "bInterfaceClass")
            if os.path.exists(class_path):
                cls = HardwareManager._read_sysfs(class_path, "")
                if cls == "08":
                    return "MASS STORAGE"
                elif cls == "03":
                    return "HID / INPUT"
                elif cls in ("01", "0e"):
                    return "MEDIA / AV"
                elif cls in ("02", "e0"):
                    return "NETWORK"

        return "PERIPHERAL"

    @staticmethod
    def set_usb_lockdown(enable: bool) -> Tuple[bool, str]:
        """
        Deep USB port lockdown:
        Sets authorized_default = 0 on all root hubs, immediately revokes authorization
        on all connected mass storage/peripherals, unbinds storage drivers, and blocks usb-storage.
        Engineered by lilami only.
        """
        action = "ENABLING BadUSB defense & deep port lockdown" if enable else "DISABLING USB port lockdown"
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
    def set_device_authorization(dev_id: str, authorize: bool) -> Tuple[bool, str]:
        """Toggles authorization for an individual USB device port via sysfs."""
        log(f"Setting authorization for USB device {dev_id}: {'AUTHORIZE' if authorize else 'BLOCK'}", "HW")
        code, out, err = run_privileged("usb-device-auth", dev_id, "1" if authorize else "0")
        if code == 0:
            status = f"USB Device {dev_id} {'Authorized' if authorize else 'Blocked'}"
            log(status, "OK")
            return True, status
        else:
            log(f"Failed to set auth for {dev_id}: {err or out}", "ERR")
            return False, err or out

    @staticmethod
    def set_usb_storage_lock(block: bool) -> Tuple[bool, str]:
        """Unbinds usb-storage / uas drivers and installs modprobe block."""
        log(f"Setting USB mass storage driver lock: {'BLOCK' if block else 'ALLOW'}", "HW")
        code, out, err = run_privileged("usb-storage-block", "1" if block else "0")
        if code == 0:
            status = "Storage Drivers Blocked" if block else "Storage Drivers Allowed"
            log(status, "OK")
            return True, status
        else:
            log(f"Storage lock failed: {err or out}", "ERR")
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
            run_sync("amixer set Capture 0%")
            log("Microphone muted", "OK")
            return True, "Microphone Muted"
        else:
            run_sync("pactl set-source-mute @DEFAULT_SOURCE@ 0")
            run_sync("amixer set Capture cap")
            run_sync("amixer set Capture 80%")
            log("Microphone unmuted", "OK")
            return True, "Microphone Active"

    @staticmethod
    def set_bluetooth_state(disabled: bool) -> Tuple[bool, str]:
        """Disables or enables Bluetooth radios via rfkill."""
        log(f"Setting Bluetooth radio state: {'BLOCK' if disabled else 'UNBLOCK'}", "HW")
        if disabled:
            run_sync("rfkill block bluetooth")
            log("Bluetooth radios blocked", "OK")
            return True, "Bluetooth Disabled"
        else:
            run_sync("rfkill unblock bluetooth")
            log("Bluetooth radios unblocked", "OK")
            return True, "Bluetooth Active"
