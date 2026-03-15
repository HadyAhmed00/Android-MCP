"""
Auto-generated test script: test_login_flow
Generated: 2026-03-14T03:38:14.945462
Total actions: 6

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
    
    def get_current_app(self):
        """Returns current foreground package name via ADB."""
        cmd = f"adb -s {self.device_id} shell dumpsys activity activities | grep mCurrentFocus"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    
    def screenshot(self, path):
        """Capture screenshot via ADB screencap."""
        cmd = f"adb -s {self.device_id} exec-out screencap -p"
        result = subprocess.run(cmd, shell=True, capture_output=True)
        with open(path, "wb") as f:
            f.write(result.stdout)
    

def run_test(device_id="emulator-5554"):
    """Run the recorded test sequence."""
    print(f"Connecting to device: {device_id}")
    device = DeviceController(device_id)
    print("Device connected. Starting test...")
    

    # Step 1: Tap "Email input field" element at (540, 1007)  io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
    device.click(540, 1007)
    time.sleep(1.0)  # navigation wait

    # Step 2: Type "demo@test.com" in EditText  io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
    device.click(540, 1007)
    device.type_text("demo@test.com")
    time.sleep(1.0)  # navigation wait

    # Step 3: Tap "Password input field" element at (540, 1227)  io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
    device.click(540, 1227)
    time.sleep(1.0)  # navigation wait

    # Step 4: Type "password123" in EditText  io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
    device.click(540, 1227)
    device.type_text("password123")
    time.sleep(1.0)  # navigation wait

    # Step 5: Press back button  io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
    device.press_key("back")
    time.sleep(1.0)  # navigation wait

    # Step 6: Tap "Login button" element at (540, 1447)  io.github.hadyahmed00.quicktasks_dimo/io.github.hadyahmed00.quicktasks_dimo.MainActivity
    device.click(540, 1447)
    
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