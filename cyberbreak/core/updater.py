import os
import json
import urllib.request
import subprocess
from typing import Dict, Any, Tuple
from cyberbreak.core.executor import log, run_sync

GITHUB_API_URL = "https://api.github.com/repos/hacker123as/CyberBreak/commits/main"
REPO_URL = "https://github.com/hacker123as/CyberBreak.git"

class Updater:

    @staticmethod
    def get_local_commit() -> str:
        repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if os.path.exists(os.path.join(repo_dir, ".git")):
            rc, out, _ = run_sync(f"git -C '{repo_dir}' rev-parse --short HEAD")
            if rc == 0 and out:
                return out.strip()

        if os.path.exists("/opt/cyberbreak/.git"):
            rc, out, _ = run_sync("git -C /opt/cyberbreak rev-parse --short HEAD")
            if rc == 0 and out:
                return out.strip()
        return "v3.0.0"

    @classmethod
    def check_for_updates(cls) -> Dict[str, Any]:
        result = {
            "status": "CHECKING",
            "update_available": False,
            "local_hash": cls.get_local_commit(),
            "remote_hash": "Unknown",
            "message": "",
            "date": "",
            "author": "lilami"
        }

        log("Checking remote GitHub repository for CyberBreak updates...", "NET")
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"User-Agent": "CyberBreak-Fortress/3.0.0"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                remote_sha = data.get("sha", "")[:7]
                commit_info = data.get("commit", {})
                result["remote_hash"] = remote_sha
                result["message"] = commit_info.get("message", "").split("\n")[0]
                result["date"] = commit_info.get("author", {}).get("date", "")[:10]

                if result["local_hash"] != "v3.0.0" and remote_sha:
                    if result["local_hash"] != remote_sha:
                        result["update_available"] = True
                        result["status"] = "UPDATE_AVAILABLE"
                    else:
                        result["update_available"] = False
                        result["status"] = "UP_TO_DATE"
                else:
                    result["status"] = "UP_TO_DATE"
                log(f"Update check finished: Local={result['local_hash']} Remote={result['remote_hash']}", "OK")
        except Exception as e:
            log(f"GitHub API update probe failed: {e}. Attempting git ls-remote...", "WARN")

            rc, out, _ = run_sync(f"git ls-remote {REPO_URL} HEAD")
            if rc == 0 and out:
                remote_sha = out.split()[0][:7]
                result["remote_hash"] = remote_sha
                if result["local_hash"] != remote_sha and result["local_hash"] != "v3.0.0":
                    result["update_available"] = True
                    result["status"] = "UPDATE_AVAILABLE"
                else:
                    result["status"] = "UP_TO_DATE"
            else:
                result["status"] = "CHECK_FAILED"
                result["message"] = str(e)

        return result

    @classmethod
    def apply_update(cls) -> Tuple[bool, str]:
        repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if os.path.exists(os.path.join(repo_dir, ".git")) and os.access(repo_dir, os.W_OK):
            rc, out, err = run_sync(f"git -C '{repo_dir}' pull origin main")
            if rc == 0:
                log("Repository pull completed successfully.", "OK")
                return True, "Application updated successfully! Please restart CyberBreak."
            else:
                return False, f"Git pull error: {err or out}"


        cmd_guide = (
            "CyberBreak is installed system-wide in /opt/cyberbreak.\n\n"
            "To apply this update on Kicksecure, run in your 'sysmaint' terminal:\n"
            "sudo bash -c 'cd /tmp && rm -rf cb_up && git clone https://github.com/hacker123as/CyberBreak.git cb_up && "
            "bash cb_up/scripts/install.sh && rm -rf cb_up'"
        )
        return False, cmd_guide
