import os
import re
import json
import secrets
import glob
from typing import List, Dict, Any, Tuple
from cyberbreak.core.executor import log, run_sync, run_privileged

class USBArmory:

    @staticmethod
    def get_keys_dir() -> str:
        home = os.path.expanduser("~")
        keys_dir = os.path.join(home, ".config", "cyberbreak", "vault_keys")
        os.makedirs(keys_dir, mode=0o700, exist_ok=True)
        return keys_dir

    @staticmethod
    def get_registry_path() -> str:
        home = os.path.expanduser("~")
        cfg_dir = os.path.join(home, ".config", "cyberbreak")
        os.makedirs(cfg_dir, mode=0o700, exist_ok=True)
        return os.path.join(cfg_dir, "vault_registry.json")

    @classmethod
    def load_registry(cls) -> List[Dict[str, Any]]:
        path = cls.get_registry_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def save_registry(cls, items: List[Dict[str, Any]]):
        path = cls.get_registry_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def list_devices() -> List[Dict[str, Any]]:
        devices = []
        rc, out, _ = run_sync("lsblk -J -b -o NAME,KNAME,PATH,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINT,MODEL,RM,HOTPLUG,TRAN")
        if rc == 0 and out:
            try:
                data = json.loads(out)
                block_devices = data.get("blockdevices", [])


                root_dev = ""
                try:
                    with open("/proc/mounts", "r") as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 2 and parts[1] == "/":
                                root_dev = parts[0]
                                break
                except Exception:
                    pass

                def parse_node(node):
                    name = node.get("name", "")
                    path = node.get("path", f"/dev/{name}")
                    size_b = int(node.get("size") or 0)
                    size_gb = round(size_b / (1024**3), 2)
                    mountpoint = node.get("mountpoint") or ""
                    fstype = node.get("fstype") or "RAW"
                    label = node.get("label") or ""
                    model = (node.get("model") or "Storage Device").strip()
                    tran = node.get("tran") or ""
                    rm = node.get("rm") or False

                    is_system = False
                    if root_dev and root_dev.startswith(path):
                        is_system = True
                    if mountpoint in ("/", "/boot", "/boot/efi", "[SWAP]"):
                        is_system = True

                    is_usb = (tran == "usb") or rm or ("sd" in name and not is_system and name not in ("sda", "nvme0n1"))

                    dev_info = {
                        "name": name,
                        "path": path,
                        "size_gb": size_gb,
                        "size_bytes": size_b,
                        "mountpoint": mountpoint,
                        "fstype": fstype,
                        "label": label,
                        "model": model,
                        "is_system": is_system,
                        "is_usb": is_usb,
                        "children": []
                    }

                    for child in node.get("children", []):
                        dev_info["children"].append(parse_node(child))

                    return dev_info

                for bd in block_devices:
                    parsed = parse_node(bd)
                    devices.append(parsed)

            except Exception as e:
                log(f"Error parsing lsblk JSON: {e}", "WARN")

        return devices

    @classmethod
    def encode_and_format_luks(cls, target_dev: str, vault_label: str = "CyberVault") -> Tuple[bool, str]:
        if not target_dev or not target_dev.startswith("/dev/"):
            return False, "Invalid target block device"


        vault_label = re.sub(r"[^a-zA-Z0-9_\-]", "", vault_label) or "CyberVault"
        vault_id = f"vault_{secrets.token_hex(4)}"
        mapper_name = f"cb_{vault_id}"


        key_bytes = secrets.token_bytes(64)
        key_file = os.path.join(cls.get_keys_dir(), f"{vault_id}.key")
        try:
            with open(key_file, "wb") as f:
                f.write(key_bytes)
            os.chmod(key_file, 0o600)
        except Exception as e:
            return False, f"Failed generating keyfile: {e}"

        log(f"Encoding USB Vault on {target_dev} with LUKS2 encryption...", "EXEC")
        rc, out, err = run_privileged("usb-luks-format", target_dev, key_file)
        if rc != 0:
            if os.path.exists(key_file):
                os.remove(key_file)
            return False, f"LUKS format error: {err or out}"


        log(f"Opening encrypted mapper {mapper_name}...", "EXEC")
        rc, out, err = run_privileged("usb-luks-open", target_dev, mapper_name, key_file)
        if rc != 0:
            return False, f"Failed opening mapper: {err or out}"


        mapped_dev = f"/dev/mapper/{mapper_name}"
        log(f"Formatting {mapped_dev} as EXT4 ({vault_label})...", "EXEC")
        rc, out, err = run_privileged("usb-format", mapped_dev, "ext4", vault_label)
        if rc != 0:
            run_privileged("usb-luks-close", mapper_name)
            return False, f"Filesystem format error: {err or out}"


        user_name = os.getenv("USER") or "user"
        mount_dir = f"/media/{user_name}/{vault_label}"
        rc, out, err = run_privileged("usb-mount", mapped_dev, mount_dir, "ext4")
        if rc != 0:
            log(f"Auto-mount notice: {err or out}", "WARN")


        registry = cls.load_registry()
        registry.append({
            "vault_id": vault_id,
            "label": vault_label,
            "device": target_dev,
            "mapper": mapper_name,
            "key_file": key_file,
            "mount_dir": mount_dir,
            "created_by": "lilami"
        })
        cls.save_registry(registry)

        log(f"USB Vault '{vault_label}' successfully encoded & armed by lilami!", "OK")
        return True, f"Encrypted Vault '{vault_label}' created! Windows will see only raw unreadable bytes."

    @classmethod
    def unlock_vault(cls, vault_id: str) -> Tuple[bool, str]:
        registry = cls.load_registry()
        v = next((item for item in registry if item.get("vault_id") == vault_id), None)
        if not v:
            return False, "Vault ID not found in registry"

        target_dev = v["device"]
        mapper_name = v["mapper"]
        key_file = v["key_file"]
        mount_dir = v.get("mount_dir", f"/media/{os.getenv('USER') or 'user'}/{v['label']}")

        if not os.path.exists(key_file):
            return False, f"Keyfile missing: {key_file}"

        log(f"Decoding & Unlocking vault '{v['label']}'...", "EXEC")
        rc, out, err = run_privileged("usb-luks-open", target_dev, mapper_name, key_file)
        if rc != 0 and "already exists" not in (err or "").lower():
            return False, f"Unlock error: {err or out}"

        mapped_dev = f"/dev/mapper/{mapper_name}"
        rc, out, err = run_privileged("usb-mount", mapped_dev, mount_dir, "ext4")
        if rc == 0:
            log(f"Vault '{v['label']}' mounted to {mount_dir}", "OK")
            return True, f"Vault unlocked and mounted to {mount_dir}"
        return False, f"Mount error: {err or out}"

    @classmethod
    def lock_vault(cls, vault_id: str) -> Tuple[bool, str]:
        registry = cls.load_registry()
        v = next((item for item in registry if item.get("vault_id") == vault_id), None)
        if not v:
            return False, "Vault ID not found in registry"

        mapper_name = v["mapper"]
        mount_dir = v.get("mount_dir", "")

        if mount_dir:
            run_privileged("usb-umount", mount_dir)

        rc, out, err = run_privileged("usb-luks-close", mapper_name)
        if rc == 0:
            log(f"Vault '{v['label']}' closed and locked.", "OK")
            return True, f"Vault '{v['label']}' locked and encrypted."
        return False, f"Lock error: {err or out}"

    @classmethod
    def delete_vault(cls, vault_id: str) -> Tuple[bool, str]:
        registry = cls.load_registry()
        v = next((item for item in registry if item.get("vault_id") == vault_id), None)
        if not v:
            return False, "Vault ID not found in registry"

        label = v.get("label", vault_id)
        mapper_name = v.get("mapper")
        mount_dir = v.get("mount_dir", "")
        if mount_dir:
            run_privileged("usb-umount", mount_dir)
        if mapper_name:
            run_privileged("usb-luks-close", mapper_name)

        key_file = v.get("key_file", "")
        if key_file and os.path.exists(key_file):
            try:
                sz = os.path.getsize(key_file)
                with open(key_file, "wb") as f:
                    f.write(b"\x00" * max(sz, 64))
                os.remove(key_file)
                log(f"Keyfile {key_file} securely shredded and deleted.", "OK")
            except Exception as e:
                log(f"Error removing keyfile: {e}", "WARN")

        updated = [item for item in registry if item.get("vault_id") != vault_id]
        cls.save_registry(updated)
        log(f"Vault '{label}' ({vault_id}) removed from registry and armed keys deleted.", "OK")
        return True, f"Vault '{label}' successfully deleted and encryption key shredded."

    @classmethod
    def format_partition(cls, device: str, fstype: str, label: str) -> Tuple[bool, str]:
        rc, out, err = run_privileged("usb-format", device, fstype, label)
        if rc == 0:
            log(f"Device {device} formatted as {fstype} ({label})", "OK")
            return True, f"Drive formatted as {fstype.upper()} ({label})"
        return False, f"Format error: {err or out}"

    @classmethod
    def wipe_drive(cls, device: str) -> Tuple[bool, str]:
        rc, out, err = run_privileged("usb-wipe-zero", device)
        if rc == 0:
            log(f"Device {device} wiped clean.", "OK")
            return True, f"Sanitization complete: Partition tables wiped."
        return False, f"Wipe error: {err or out}"

    @classmethod
    def flash_iso(cls, iso_path: str, device: str) -> Tuple[bool, str]:
        if not os.path.exists(iso_path):
            return False, f"ISO file not found: {iso_path}"
        log(f"Writing ISO {iso_path} to {device}...", "EXEC")
        rc, out, err = run_privileged("usb-flash-iso", iso_path, device)
        if rc == 0:
            log(f"ISO flashed successfully to {device}", "OK")
            return True, f"ISO successfully burned to {device}!"
        return False, f"ISO flash error: {err or out}"

    @classmethod
    def backup_system_to_usb(cls, target_dir: str, mode: str = "home") -> Tuple[bool, str]:
        user_name = os.getenv("USER") or "user"
        log(f"Creating system backup ({mode}) to {target_dir}...", "EXEC")
        rc, out, err = run_privileged("system-backup-usb", target_dir, mode, user_name)
        if rc == 0:
            log(f"System backup completed to {target_dir}", "OK")
            return True, f"Backup successfully saved to {target_dir}!"
        return False, f"Backup error: {err or out}"

    @classmethod
    def trim_drives(cls) -> Tuple[bool, str]:
        log("Running deep SSD TRIM and discarded block purge...", "EXEC")
        rc, out, err = run_privileged("drive-trim")
        if rc == 0:
            log("SSD TRIM discard completed successfully.", "OK")
            return True, f"SSD TRIM completed:\n{out or 'All mounted filesystems trimmed.'}"
        return False, f"TRIM error: {err or out}"
