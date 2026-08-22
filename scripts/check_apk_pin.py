"""Verify the pinned Portal APK release still exists and matches its checksum.

Run by CI (including on a weekly schedule) so a retagged or deleted release in
Android-MCP-Portal is caught here rather than on a user's first install.
"""

import hashlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, ".")

from android_mcp.bootstrap import PORTAL_APK_SHA256, PORTAL_APK_TAG, PORTAL_APK_URL  # noqa: E402


def main() -> int:
    print(f"Pinned tag: {PORTAL_APK_TAG}")
    print(f"URL:        {PORTAL_APK_URL}")

    try:
        with urllib.request.urlopen(PORTAL_APK_URL, timeout=60) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        if PORTAL_APK_SHA256 is None:
            print(f"WARNING: pin not published yet ({exc}); no checksum pinned either - skipping")
            return 0
        print(f"FAIL: pinned APK is unreachable: {exc}")
        return 1

    digest = hashlib.sha256(data).hexdigest()
    print(f"Downloaded {len(data)} bytes, sha256={digest}")

    if PORTAL_APK_SHA256 is None:
        print("WARNING: PORTAL_APK_SHA256 is None - pin the digest above in bootstrap.py")
        return 0

    if digest != PORTAL_APK_SHA256:
        print(f"FAIL: checksum mismatch, expected {PORTAL_APK_SHA256}")
        return 1

    print("OK: pinned APK matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
