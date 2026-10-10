import os
import shutil
from typing import Tuple
from cyberbreak.core.executor import run_sync, log

class MetadataCleaner:
    """Document, media metadata stripping via mat2 and military-grade shredding."""

    @staticmethod
    def clean_metadata(file_path: str) -> Tuple[bool, str]:
        """Cleans document and image metadata using mat2."""
        if not os.path.exists(file_path):
            return False, "File does not exist"

        log(f"Sanitizing file metadata: {file_path}", "META")
        code, out, err = run_sync(f"mat2 '{file_path}'")
        if code == 0:
            log(f"Metadata stripped successfully for {file_path}", "OK")
            return True, "Metadata Cleaned"
        else:
            log(f"mat2 failed or not installed: {err}", "WARN")
            return False, err or "mat2 processing failed"

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
        """Flushes memory buffers and drops pagecache, dentries, and inodes."""
        log("Flushing kernel RAM buffers and dropping memory cache", "MEM")
        run_sync("sync")
        code, out, err = run_sync("echo 3 > /proc/sys/vm/drop_caches")
        if code == 0:
            log("Kernel memory cache purged successfully", "OK")
            return True, "RAM Cache Purged"
        return False, err
