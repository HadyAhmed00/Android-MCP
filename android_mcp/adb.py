"""ADB binary resolution and command helpers.

Every ADB invocation in this package goes through here. Nothing else should
spell the string ``"adb"``.

Resolution order:
1. ``adb`` on PATH (respects a user's existing platform-tools install)
2. the ``adb`` binary bundled inside ``adbutils`` (a dependency of uiautomator2),
   so a plain ``uvx android-mcp`` works with no manual SDK setup
3. RuntimeError with an install hint
"""

import os
import shutil
import subprocess
from functools import lru_cache
from typing import List, Optional

PLATFORM_TOOLS_URL = "https://developer.android.com/tools/releases/platform-tools"


@lru_cache(maxsize=1)
def adb_path() -> str:
    """Absolute path to a usable adb binary."""
    found = shutil.which("adb")
    if found:
        return found

    try:
        import adbutils

        bundled = os.path.join(os.path.dirname(adbutils.__file__), "binaries")
        for name in ("adb.exe", "adb"):
            candidate = os.path.join(bundled, name)
            if os.path.isfile(candidate):
                return candidate
    except Exception:
        pass

    raise RuntimeError(
        "ADB not found. Install Android platform-tools and put 'adb' on your "
        f"PATH: {PLATFORM_TOOLS_URL}"
    )


def adb_base(device_id: Optional[str] = None) -> List[str]:
    """Command prefix: the adb binary plus ``-s <device>`` when one is set."""
    cmd = [adb_path()]
    if device_id:
        cmd.extend(["-s", device_id])
    return cmd


class Adb:
    """Thin wrapper around adb for one device."""

    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id

    def run(self, args: List[str], timeout: int = 10, text: bool = True):
        """Run a raw adb subcommand (no implicit 'shell')."""
        return subprocess.run(
            adb_base(self.device_id) + args,
            capture_output=True,
            text=text,
            timeout=timeout,
            **({"encoding": "utf-8", "errors": "ignore"} if text else {}),
        )

    def shell(self, command: str, timeout: int = 10) -> str:
        """Run an adb shell command, raising on a non-zero exit."""
        result = self.run(["shell", command], timeout=timeout)
        if result.returncode != 0:
            raise RuntimeError(f"ADB command failed: {result.stderr}")
        return (result.stdout or "").strip()

    def shell_quiet(self, command: str, timeout: int = 10) -> str:
        """Run an adb shell command, returning '' instead of raising."""
        try:
            result = self.run(["shell", command], timeout=timeout)
        except Exception:
            return ""
        return (result.stdout or "").strip()

    def devices(self) -> List[str]:
        """Serials of devices currently in the 'device' state."""
        result = subprocess.run(
            [adb_path(), "devices"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="ignore",
        )
        serials = []
        for line in (result.stdout or "").splitlines()[1:]:
            parts = line.split()
            if len(parts) == 2 and parts[1] == "device":
                serials.append(parts[0])
        return serials
