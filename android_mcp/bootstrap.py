"""Device bootstrap: get the Portal app installed and its a11y service enabled.

The MCP Helper fast path needs the Portal app (https://github.com/HadyAhmed00/Android-MCP-Portal)
installed on the device with its accessibility service enabled. Doing that by
hand is the single biggest install hurdle, so this module does it: download the
pinned APK, install it, flip the secure settings, verify with a ping.

Everything here is best-effort — on any failure it returns a report with manual
steps rather than raising, so the server still starts and falls back to the
UIAutomator2 backend.
"""

import hashlib
import os
import shutil
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from android_mcp.adb import Adb

# --- Pinned Portal release -------------------------------------------------
# Bump these two together when a new Portal APK ships; the SHA comes from the
# portal.apk.sha256 asset on that release.
PORTAL_REPO = "HadyAhmed00/Android-MCP-Portal"
PORTAL_APK_TAG = "v0.5.5"
PORTAL_APK_ASSET = "portal.apk"
PORTAL_APK_URL = (
    f"https://github.com/{PORTAL_REPO}/releases/download/{PORTAL_APK_TAG}/{PORTAL_APK_ASSET}"
)
# Set to None only to intentionally skip verification; keep it pinned in releases.
PORTAL_APK_SHA256: Optional[str] = "4caf8999bef1b5865a55c966c16a1a1c051b432d11a1ae285d879904c45723b7"

# applicationId == content provider authority (see MCPHelperClient.PROVIDER_AUTHORITY).
PORTAL_PACKAGE = "io.github.hadyahmed00.portal"
# The Kotlin namespace (com.hadyahmed00.portal) differs from the applicationId,
# so the component string legitimately mixes the two.
PORTAL_A11Y_SERVICE = f"{PORTAL_PACKAGE}/com.hadyahmed00.portal.service.DroidrunAccessibilityService"

MANUAL_STEPS = f"""Manual setup:
  1. Download {PORTAL_APK_ASSET} from https://github.com/{PORTAL_REPO}/releases
  2. adb install -r {PORTAL_APK_ASSET}
  3. On the device: Settings -> Accessibility -> Droidrun Portal -> enable
"""


@dataclass
class BootstrapReport:
    """Outcome of an ensure_portal() run."""

    ok: bool = False
    installed: bool = False          # APK present on device
    apk_installed_now: bool = False  # this run installed it
    a11y_enabled: bool = False
    ping_ok: bool = False
    version: str = ""
    steps: List[str] = field(default_factory=list)
    error: str = ""

    def log(self, message: str) -> None:
        self.steps.append(message)

    def to_string(self) -> str:
        lines = list(self.steps)
        if self.ok:
            lines.append(f"Portal ready (version {self.version or 'unknown'}).")
        else:
            lines.append(f"Portal NOT ready: {self.error or 'unknown error'}")
            lines.append(MANUAL_STEPS)
        return "\n".join(lines)


def cache_dir() -> Path:
    """Per-user cache directory for downloaded APKs.

    ANDROID_MCP_CACHE_DIR overrides it — useful when the default location is
    sandboxed, virtualized, or on a drive adb cannot read.
    """
    override = os.environ.get("ANDROID_MCP_CACHE_DIR")
    if override:
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path

    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    path = Path(base) / "android-mcp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_apk(report: BootstrapReport) -> Path:
    """Fetch the pinned APK into the cache, verifying its checksum."""
    target = cache_dir() / f"portal-{PORTAL_APK_TAG}.apk"

    if target.exists() and (PORTAL_APK_SHA256 is None or _sha256(target) == PORTAL_APK_SHA256):
        report.log(f"Using cached APK {target}")
        return target

    report.log(f"Downloading {PORTAL_APK_URL}")
    tmp = target.with_suffix(".part")
    with urllib.request.urlopen(PORTAL_APK_URL, timeout=60) as response, open(tmp, "wb") as out:
        while True:
            chunk = response.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)

    if PORTAL_APK_SHA256 is not None:
        actual = _sha256(tmp)
        if actual != PORTAL_APK_SHA256:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(
                f"APK checksum mismatch: expected {PORTAL_APK_SHA256}, got {actual}"
            )
        report.log("Checksum verified")
    else:
        report.log("WARNING: no pinned checksum, skipping verification")

    tmp.replace(target)
    return target


def is_installed(adb: Adb) -> bool:
    output = adb.shell_quiet(f"pm list packages {PORTAL_PACKAGE}")
    return PORTAL_PACKAGE in output


def install_apk(adb: Adb, apk: Path, report: BootstrapReport) -> None:
    """adb install -r, with fallbacks for a signature clash and an unreadable path."""
    result = adb.run(["install", "-r", str(apk)], timeout=180)
    output = f"{result.stdout or ''}{result.stderr or ''}"
    if result.returncode == 0 and "Success" in output:
        report.log("Installed Portal APK")
        return

    if "failed to stat" in output:
        # Some cache locations are unreadable by adb (AV quarantine, virtualized
        # or redirected AppData). Retry from the system temp dir.
        report.log("adb cannot read the cached APK; retrying from a temp copy")
        with tempfile.TemporaryDirectory() as tmpdir:
            copy = Path(tmpdir) / PORTAL_APK_ASSET
            shutil.copyfile(apk, copy)
            result = adb.run(["install", "-r", str(copy)], timeout=180)
            output = f"{result.stdout or ''}{result.stderr or ''}"
            if result.returncode == 0 and "Success" in output:
                report.log("Installed Portal APK (from temp copy)")
                return

    if "INSTALL_FAILED_UPDATE_INCOMPATIBLE" in output or "signatures do not match" in output:
        report.log("Signature mismatch; uninstalling old Portal build first")
        adb.run(["uninstall", PORTAL_PACKAGE], timeout=60)
        result = adb.run(["install", "-r", str(apk)], timeout=180)
        output = f"{result.stdout or ''}{result.stderr or ''}"
        if result.returncode == 0 and "Success" in output:
            report.log("Installed Portal APK (after uninstall)")
            return

    raise RuntimeError(f"adb install failed: {output.strip()}")


def enable_accessibility(adb: Adb, report: BootstrapReport, attempts: int = 4) -> bool:
    """Add the Portal service to the enabled a11y services, preserving others.

    Retries: immediately after an install the package may not be registered with
    the accessibility manager yet, which silently drops the write.
    """
    for attempt in range(attempts):
        current = adb.shell_quiet("settings get secure enabled_accessibility_services")
        if current in ("null", "None"):
            current = ""

        services = [service for service in current.split(":") if service]
        if PORTAL_A11Y_SERVICE not in services:
            services.append(PORTAL_A11Y_SERVICE)
            value = ":".join(services)
            adb.shell_quiet(f'settings put secure enabled_accessibility_services "{value}"')
        adb.shell_quiet("settings put secure accessibility_enabled 1")

        if PORTAL_A11Y_SERVICE in adb.shell_quiet(
            "settings get secure enabled_accessibility_services"
        ):
            report.log("Accessibility service enabled")
            return True

        if attempt < attempts - 1:
            time.sleep(1.5)

    report.log("Could not enable accessibility service via ADB (OEM restriction?)")
    adb.shell_quiet("am start -a android.settings.ACCESSIBILITY_SETTINGS")
    return False


def ensure_portal(
    device_id: Optional[str] = None,
    *,
    force: bool = False,
    apk_path: Optional[str] = None,
) -> BootstrapReport:
    """Make the Portal app usable on the device. Never raises.

    Args:
        device_id: ADB serial, or None for the default device.
        force: Reinstall even if the app is already present and pinging.
        apk_path: Use this local APK instead of downloading the pinned one.
    """
    report = BootstrapReport()
    adb = Adb(device_id)

    try:
        from android_mcp.mcp_helper import MCPHelperClient

        client = MCPHelperClient(device_id)

        report.installed = is_installed(adb)
        if report.installed and not force:
            try:
                if client.ping():
                    report.version = _safe_version(client)
                    report.ok = report.ping_ok = report.a11y_enabled = True
                    report.log(f"Portal already running (version {report.version or 'unknown'})")
                    return report
            except Exception:
                report.log("Portal installed but not responding; continuing setup")

        if not report.installed or force:
            apk = Path(apk_path) if apk_path else download_apk(report)
            if not apk.exists():
                raise RuntimeError(f"APK not found: {apk}")
            install_apk(adb, apk, report)
            report.installed = True
            report.apk_installed_now = True

        report.a11y_enabled = enable_accessibility(adb, report)

        # The accessibility service takes a moment to bind after being enabled,
        # and its content provider only answers once it has.
        report.ping_ok = _ping_with_retry(client, report)

        if report.ping_ok:
            report.version = _safe_version(client)
            report.ok = True
        else:
            report.error = "Portal is installed but its content provider is not responding"

    except Exception as exc:
        report.error = str(exc)

    return report


def _ping_with_retry(client, report: BootstrapReport, attempts: int = 6) -> bool:
    last_error = ""
    for attempt in range(attempts):
        try:
            if client.ping():
                return True
        except Exception as exc:
            last_error = str(exc)
        if attempt < attempts - 1:
            time.sleep(1.5)
    if last_error:
        report.log(f"Ping failed: {last_error}")
    return False


def _safe_version(client) -> str:
    try:
        return client.get_version()
    except Exception:
        return ""
