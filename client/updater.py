# client/updater.py
"""
Auto-update system.
The client checks a remote JSON file for version info and downloads updates.

Remote JSON format:
{
  "version": "1.1.0",
  "download_url": "https://example.com/EditalSystem-1.1.0.exe",
  "release_notes": "Novidades desta versão...",
  "min_version": "1.0.0"
}
"""
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable


APP_VERSION = "1.0.0"


def _version_tuple(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0, 0, 0)


def check_for_updates(update_url: str, timeout: int = 8) -> dict | None:
    """
    Fetch remote version info.
    Returns dict with update info if a new version is available, else None.
    """
    if not update_url or not update_url.startswith("http"):
        return None
    try:
        req = urllib.request.Request(
            update_url,
            headers={"User-Agent": "EditalSystem/" + APP_VERSION}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        remote_version = data.get("version", "0.0.0")
        if _version_tuple(remote_version) > _version_tuple(APP_VERSION):
            return data
        return None
    except Exception:
        return None


def download_update(download_url: str,
                    progress_cb: Callable[[int, int], None] = None) -> str | None:
    """
    Download the update installer to a temp file.
    Returns path to downloaded file, or None on failure.
    """
    try:
        suffix = ".exe" if sys.platform == "win32" else ".sh"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

        def _report(count, block_size, total_size):
            if progress_cb and total_size > 0:
                downloaded = min(count * block_size, total_size)
                progress_cb(downloaded, total_size)

        urllib.request.urlretrieve(download_url, tmp_path, _report)
        return tmp_path
    except Exception:
        return None


def launch_installer(path: str):
    """Launch the downloaded installer."""
    if sys.platform == "win32":
        os.startfile(path)
    else:
        os.system(f"chmod +x '{path}' && '{path}'")
    sys.exit(0)


def get_current_version() -> str:
    return APP_VERSION
