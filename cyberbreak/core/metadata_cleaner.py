import os
import shutil
from typing import Tuple
from cyberbreak.core.executor import run_sync, run_privileged, log

class MetadataCleaner:
    """
    Document, media metadata stripping via mat2, exiftool, native PIL, and military-grade shredding.
    Engineered by lilami only.
    """

    @staticmethod
    def clean_metadata(file_path: str) -> Tuple[bool, str]:
        """
        Sanitizes document and image metadata.
        Tries mat2 first, then exiftool, and finally native Python scrubbing for images.
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"

        log(f"Sanitizing file metadata: {file_path}", "META")

        # 1. Primary: mat2
        code, out, err = run_sync(f"mat2 '{file_path}'")
        if code == 0:
            log(f"Metadata stripped successfully via mat2 for {file_path}", "OK")
            return True, "Metadata Cleaned (mat2)"

        # 2. Secondary fallback: exiftool
        code2, out2, err2 = run_sync(f"exiftool -all= -overwrite_original '{file_path}'")
        if code2 == 0:
            log(f"Metadata stripped successfully via exiftool for {file_path}", "OK")
            return True, "Metadata Cleaned (exiftool)"

        # 3. Tertiary fallback: Native Python image cleaning
        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".jpg", ".jpeg", ".png", ".webp"):
            try:
                from PIL import Image
                img = Image.open(file_path)
                data = list(img.getdata())
                image_without_exif = Image.new(img.mode, img.size)
                image_without_exif.putdata(data)
                image_without_exif.save(file_path)
                log(f"Image EXIF and metadata scrubbed via native PIL engine: {file_path}", "OK")
                return True, "Metadata Cleaned (Native Engine)"
            except Exception as e:
                pass

        log(f"mat2 and exiftool processing failed: {err or err2}", "WARN")
        return False, err or err2 or "Metadata cleaning tools not installed"

    @staticmethod
    def secure_shred(file_path: str, passes: int = 3) -> Tuple[bool, str]:
        """Cryptographically shreds a file with multiple overwrite passes and zeroes."""
        if not os.path.exists(file_path):
            return False, "File does not exist"

        log(f"Overwriting and shredding file: {file_path} ({passes} passes)", "SHRED")
        # Try system shred first
        code, out, err = run_sync(f"shred -u -z -n {passes} '{file_path}'")
        if code == 0:
            log(f"File obliterated from filesystem: {file_path}", "OK")
            return True, "File Shredded"

        # Python manual overwrite fallback
        try:
            length = os.path.getsize(file_path)
            with open(file_path, "wb") as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(length))
                    f.flush()
                # Final zero pass
                f.seek(0)
                f.write(b"\x00" * length)
                f.flush()
            os.remove(file_path)
            log(f"File wiped via urandom fallback: {file_path}", "OK")
            return True, "File Shredded (Fallback)"
        except Exception as e:
            log(f"Failed to shred file: {e}", "ERR")
            return False, str(e)

    @staticmethod
    def purge_ram_cache() -> Tuple[bool, str]:
        """Flushes memory buffers and drops pagecache, dentries, and inodes via privileged helper."""
        log("Flushing kernel RAM buffers and dropping memory cache", "MEM")
        code, out, err = run_privileged("purge-ram")
        if code == 0:
            log("Kernel memory cache purged successfully", "OK")
            return True, "RAM Cache Purged"
        else:
            log(f"Failed to purge RAM cache: {err or out}", "ERR")
            return False, err or out
