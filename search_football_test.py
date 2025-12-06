"""
Auto-generated test script: search_football_on_google
Generated: 2025-12-06T09:45:52.595047
Total actions: 8

This script uses direct ADB commands and is fully independent.
No external dependencies required beyond ADB.
"""

import subprocess
import time
import sys


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

    def click(self, x, y):
        """Click at coordinates."""
        cmd = f"adb -s {self.device_id} shell input tap {x} {y}"
        subprocess.run(cmd, shell=True)

    def long_click(self, x, y, duration=1000):
        """Long click at coordinates."""
        cmd = f"adb -s {self.device_id} shell input touchscreen swipe {x} {y} {x} {y} {duration}"
        subprocess.run(cmd, shell=True)

    def swipe(self, x1, y1, x2, y2, duration=300):
        """Swipe from one point to another."""
        cmd = f"adb -s {self.device_id} shell input touchscreen swipe {x1} {y1} {x2} {y2} {duration}"
        subprocess.run(cmd, shell=True)

    def drag(self, x1, y1, x2, y2, duration=500):
        """Drag from one point to another."""
        cmd = f"adb -s {self.device_id} shell input touchscreen swipe {x1} {y1} {x2} {y2} {duration}"
        subprocess.run(cmd, shell=True)

    def type_text(self, text):
        """Type text on device."""
        cmd = f"adb -s {self.device_id} shell input text \"{text}\""
        subprocess.run(cmd, shell=True)

    def press_key(self, key_code):
        """Press a key code."""
        key_map = {
            "ENTER": "66",
            "BACK": "4",
            "HOME": "3",
            "MENU": "1",
            "POWER": "26",
            "VOLUME_UP": "24",
            "VOLUME_DOWN": "25",
        }
        code = key_map.get(key_code.upper(), key_code)
        cmd = f"adb -s {self.device_id} shell input keyevent {code}"
        subprocess.run(cmd, shell=True)

    def open_notification(self):
        """Open notification bar."""
        cmd = f"adb -s {self.device_id} shell cmd statusbar expand-notifications"
        subprocess.run(cmd, shell=True)


def run_test(device_id="emulator-5554"):
    """Run the recorded test sequence."""
    print(f"Connecting to device: {device_id}")
    device = DeviceController(device_id)
    print("Device connected. Starting test...")

    # Action 1: Click at (741, 1862)
    device.click(741, 1862)
    

    # Action 2: Wait 2 seconds
    time.sleep(2)
   

    # Action 3: Click at (471, 766)
    device.click(471, 766)
    

    # Action 4: Wait 1 seconds
    time.sleep(1)
   

    # Action 5: Type "Football"
    device.type_text("Football")
    

    # Action 6: Wait 1 seconds
    time.sleep(1)
    

    # Action 7: Press ENTER button
    device.press_key("ENTER")
    

    # Action 8: Wait 3 seconds
    time.sleep(3)

    print("Test completed successfully!")


if __name__ == "__main__":
    device_id = sys.argv[1] if len(sys.argv) > 1 else "emulator-5554"
    try:
        run_test(device_id)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)