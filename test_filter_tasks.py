"""
Auto-generated pytest test: test_filter_tasks
Generated: 2026-03-14T22:13:58.286790
Total actions: 4
Assertions: 3

Run with pytest:  pytest test_filter_tasks -v
Run directly:     python test_filter_tasks [device_id]
"""

import subprocess
import re
import time
import sys

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


class DeviceController:
    """Direct ADB device controller - no external dependencies."""
    
    def __init__(self, device_id="emulator-5554"):
        self.device_id = device_id
        self._verify_device()
    
    def _verify_device(self):
        """Verify device is connected."""
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if self.device_id not in result.stdout:
            raise Exception(f"Device {self.device_id} not found. Available devices:\n{result.stdout}")
    
    def _adb(self, *args):
        """Run an ADB command and return stdout."""
        cmd = ["adb", "-s", self.device_id] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    
    def click(self, x, y):
        """Click at coordinates."""
        self._adb("shell", f"input tap {x} {y}")
    
    def long_click(self, x, y, duration=1000):
        """Long click at coordinates."""
        self._adb("shell", f"input touchscreen swipe {x} {y} {x} {y} {duration}")
    
    def swipe(self, x1, y1, x2, y2, duration=300):
        """Swipe from one point to another."""
        self._adb("shell", f"input touchscreen swipe {x1} {y1} {x2} {y2} {duration}")
    
    def drag(self, x1, y1, x2, y2, duration=500):
        """Drag from one point to another."""
        self._adb("shell", f"input touchscreen swipe {x1} {y1} {x2} {y2} {duration}")
    
    def type_text(self, text):
        """Type text on device."""
        escaped = text.replace(' ', '%s').replace("'", "\\\\'")
        self._adb('shell', f"input text '{escaped}'")
    
    def press_key(self, key_code):
        """Press a key code."""
        key_map = {
            "ENTER": "66", "BACK": "4", "HOME": "3", "MENU": "1",
            "POWER": "26", "VOLUME_UP": "24", "VOLUME_DOWN": "25",
        }
        code = key_map.get(key_code.upper(), key_code)
        self._adb("shell", f"input keyevent {code}")
    
    def open_notification(self):
        """Open notification bar."""
        self._adb("shell", "cmd statusbar expand-notifications")
    
    def get_current_app(self) -> str:
        """Returns current foreground package name via ADB."""
        output = self._adb("shell", "dumpsys activity activities")
        for line in output.splitlines():
            if "mCurrentFocus" in line or "mFocusedApp" in line:
                return line
        return ""
    
    def get_current_activity(self) -> str:
        """Returns current foreground activity (package/activity) via ADB."""
        output = self._adb("shell", "dumpsys activity activities")
        for line in output.splitlines():
            if "mCurrentFocus" in line or "mFocusedApp" in line:
                match = re.search(r"(\S+/\S+)\}", line)
                if match:
                    return match.group(1)
        return ""
    
    def has_text_on_screen(self, text: str) -> bool:
        """Check if text exists in current UI hierarchy."""
        output = self._adb("exec-out", "uiautomator dump /dev/tty")
        return text in output
    
    def screenshot(self, path: str):
        """Capture screenshot via ADB screencap."""
        data = subprocess.run(
            ["adb", "-s", self.device_id, "exec-out", "screencap", "-p"],
            capture_output=True, timeout=10
        )
        with open(path, "wb") as f:
            f.write(data.stdout)
    


if HAS_PYTEST:
    @pytest.fixture(scope="module")
    def device():
        """Create a device controller for the test module."""
        d = DeviceController("emulator-5554")
        yield d


class TestTestFilterTasks:
    """Recorded test: test_filter_tasks"""

    def test_test_filter_tasks(self, device, request=None):
        try:
            # Step 1: Tap "Button" button at (871, 224) -- io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
            device.click(871, 224)
            print(device.get_current_app())
            assert "io.github.hadyahmed00.quicktasks_dimo" in device.get_current_app(), "App should still be in foreground"
            time.sleep(1.0)  # navigation wait
            # Step 2: Tap "Filter: Work Only" element at (783, 510) -- io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
            device.click(783, 510)
            assert "io.github.hadyahmed00.quicktasks_dimo" in device.get_current_app(), "App should still be in foreground"
            time.sleep(1.0)  # navigation wait
            # Step 3: Tap "Button" button at (871, 224) -- io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
            device.click(871, 224)
            assert "io.github.hadyahmed00.quicktasks_dimo" in device.get_current_app(), "App should still be in foreground"
            time.sleep(1.0)  # navigation wait
            # Step 4: Tap "Filter: All Tasks" element at (783, 378) -- io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
            device.click(783, 378)
            
            # Final verification: app is still running
            assert "io.github.hadyahmed00.quicktasks_dimo" in device.get_current_app(), "App io.github.hadyahmed00.quicktasks_dimo should still be in foreground at end of test"
        except Exception as e:
            # Screenshot on failure for debugging
            name = request.node.name if request else "direct_run"
            device.screenshot(f"failure_{name}.png")
            raise


def run_test(device_id="emulator-5554"):
    """Run the test directly without pytest."""
    print(f"Connecting to device: {device_id}")
    device = DeviceController(device_id)
    print("Device connected. Running test...")
    test = TestTestFilterTasks()
    try:
        test.test_test_filter_tasks(device)
        print("\nTEST PASSED")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nTEST ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    device_id = sys.argv[1] if len(sys.argv) > 1 else "emulator-5554"
    run_test(device_id)