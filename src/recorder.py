"""Test action recorder for capturing and exporting test scripts."""

from dataclasses import dataclass, asdict
from typing import List, Any
from datetime import datetime
import json
from pathlib import Path


@dataclass
class TestAction:
    """Represents a single user action during testing."""
    action: str  # click, swipe, type, press, etc.
    timestamp: float
    parameters: dict
    result: str = ""
    description: str = ""
    element_name: str = ""     # "Login" — human name of tapped element
    element_type: str = ""     # "button", "input", etc.
    screen_app: str = ""       # "io.github.hadyahmed00.quicktasks_dimo"
    screen_activity: str = ""  # ".LoginActivity"
    screen_width: int = 0      # recording device screen width in pixels
    screen_height: int = 0     # recording device screen height in pixels
    status_bar_height: int = 0 # recording device status bar height in pixels
    nav_bar_height: int = 0    # recording device navigation bar height in pixels

    def to_dict(self):
        return asdict(self)


class TestRecorder:
    """Records user actions during testing for export as executable test scripts."""

    def __init__(self):
        self.actions: List[TestAction] = []
        self.start_time = datetime.now()
        self.is_recording = False

    def start(self):
        """Start recording actions."""
        self.actions = []
        self.start_time = datetime.now()
        self.is_recording = True

    def stop(self):
        """Stop recording actions."""
        self.is_recording = False

    def record_action(self, action: str, parameters: dict, result: str = "",
                      description: str = "", element_name: str = "",
                      element_type: str = "", screen_app: str = "",
                      screen_activity: str = "", screen_width: int = 0,
                      screen_height: int = 0, status_bar_height: int = 0,
                      nav_bar_height: int = 0):
        """Record a single action."""
        if not self.is_recording:
            return

        timestamp = (datetime.now() - self.start_time).total_seconds()
        test_action = TestAction(
            action=action,
            timestamp=timestamp,
            parameters=parameters,
            result=result,
            description=description,
            element_name=element_name,
            element_type=element_type,
            screen_app=screen_app,
            screen_activity=screen_activity,
            screen_width=screen_width,
            screen_height=screen_height,
            status_bar_height=status_bar_height,
            nav_bar_height=nav_bar_height,
        )
        self.actions.append(test_action)

    def get_actions(self) -> List[TestAction]:
        """Get all recorded actions."""
        return self.actions

    def clear(self):
        """Clear all recorded actions."""
        self.actions = []

    def export_as_json(self, filename: str = None) -> str:
        """Export recorded actions as JSON."""
        if not filename:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_script_{timestamp}.json"

        filepath = Path(filename)
        data = {
            "test_name": filename.replace(".json", ""),
            "start_time": self.start_time.isoformat(),
            "duration_seconds": self.actions[-1].timestamp if self.actions else 0,
            "total_actions": len(self.actions),
            "actions": [action.to_dict() for action in self.actions]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return str(filepath)

    def export_as_python(self, filename: str = None, test_name: str = None, use_adb: bool = True) -> str:
        """Export recorded actions as executable Python test script.

        Args:
            filename: Output filename
            test_name: Name of the test
            use_adb: If True, generate ADB-based script (independent). If False, use uiautomator2.
        """
        if not filename:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_{timestamp}.py"

        if not test_name:
            test_name = filename.replace(".py", "")

        filepath = Path(filename)

        if use_adb:
            return self._export_as_adb_python(filepath, test_name)
        else:
            return self._export_as_uiautomator_python(filepath, test_name)

    def _normalize_delay(self, time_diff: float) -> tuple[float, str]:
        """Normalize AI thinking delays to realistic replay delays.

        Returns (sleep_seconds, comment) tuple.
        """
        if time_diff > 1.5:
            return (1.0, "navigation wait")
        elif time_diff > 0.5:
            return (0.3, "")
        return (0, "")

    def _export_as_uiautomator_python(self, filepath: Path, test_name: str) -> str:
        """Export as uiautomator2-based script (original behavior)."""
        script_lines = [
            '"""',
            f'Auto-generated test script: {test_name}',
            f'Generated: {self.start_time.isoformat()}',
            f'Total actions: {len(self.actions)}',
            '',
            'Coordinates are percentages (0-100) for resolution independence.',
            'The PctDevice wrapper converts them to pixels at runtime.',
            '"""',
            '',
            'import subprocess',
            'import uiautomator2 as u2',
            'import time',
            '',
            '',
            'class PctDevice:',
            '    """Wrapper around uiautomator2 device that accepts percentage coordinates.',
            '    ',
            '    Y coordinates are percentages of the content area (excluding status bar',
            '    and navigation bar) for resolution independence."""',
            '    ',
            '    def __init__(self, u2_device):',
            '        self._d = u2_device',
            '        info = u2_device.info',
            '        self.screen_width = info["displayWidth"]',
            '        self.screen_height = info["displayHeight"]',
            '        self.status_bar_h, self.nav_bar_h = self._get_system_bar_heights()',
            '        self.content_height = self.screen_height - self.status_bar_h - self.nav_bar_h',
            '    ',
            '    def _get_system_bar_heights(self):',
            '        """Get status bar and navigation bar heights via ADB."""',
            '        import re',
            '        status_h, nav_h = 0, 0',
            '        try:',
            '            result = subprocess.run(',
            '                ["adb", "shell", "dumpsys", "window"],',
            '                capture_output=True, text=True, timeout=5)',
            '            in_status = False',
            '            in_nav = False',
            '            for line in result.stdout.splitlines():',
            '                if "StatusBar" in line and "Window" in line:',
            '                    in_status = True',
            '                    in_nav = False',
            '                elif "NavigationBar" in line and "Window" in line:',
            '                    in_nav = True',
            '                    in_status = False',
            '                elif "Window #" in line:',
            '                    in_status = False',
            '                    in_nav = False',
            '                if in_status and "mFrame=" in line:',
            '                    m = re.search(r"mFrame=\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]", line)',
            '                    if m:',
            '                        status_h = int(m.group(4)) - int(m.group(2))',
            '                    in_status = False',
            '                if in_nav and "mFrame=" in line:',
            '                    m = re.search(r"mFrame=\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]", line)',
            '                    if m:',
            '                        nav_h = int(m.group(4)) - int(m.group(2))',
            '                    in_nav = False',
            '        except Exception:',
            '            pass',
            '        return status_h, nav_h',
            '    ',
            '    def _pct_to_px(self, x_pct, y_pct):',
            '        x = int(x_pct / 100 * self.screen_width)',
            '        y = int(y_pct / 100 * self.content_height + self.status_bar_h)',
            '        return x, y',
            '    ',
            '    def click(self, x_pct, y_pct):',
            '        x, y = self._pct_to_px(x_pct, y_pct)',
            '        self._d.click(x, y)',
            '    ',
            '    def long_click(self, x_pct, y_pct):',
            '        x, y = self._pct_to_px(x_pct, y_pct)',
            '        self._d.long_click(x, y)',
            '    ',
            '    def swipe(self, x1_pct, y1_pct, x2_pct, y2_pct):',
            '        x1, y1 = self._pct_to_px(x1_pct, y1_pct)',
            '        x2, y2 = self._pct_to_px(x2_pct, y2_pct)',
            '        self._d.swipe(x1, y1, x2, y2)',
            '    ',
            '    def drag(self, x1_pct, y1_pct, x2_pct, y2_pct):',
            '        x1, y1 = self._pct_to_px(x1_pct, y1_pct)',
            '        x2, y2 = self._pct_to_px(x2_pct, y2_pct)',
            '        self._d.drag(x1, y1, x2, y2)',
            '    ',
            '    def send_keys(self, text):',
            '        self._d.send_keys(text)',
            '    ',
            '    def press(self, key):',
            '        self._d.press(key)',
            '    ',
            '    def open_notification(self):',
            '        self._d.open_notification()',
            '    ',
            '',
            '',
            'def run_test(device=None):',
            '    """Run the recorded test sequence."""',
            '    if device is None:',
            '        device = PctDevice(u2.connect())',
            '    elif not isinstance(device, PctDevice):',
            '        device = PctDevice(device)',
            '    ',
        ]

        for i, action in enumerate(self.actions, 1):
            wait_before = ""
            if i > 1:
                prev_action = self.actions[i-2]
                time_diff = action.timestamp - prev_action.timestamp
                sleep_secs, delay_comment = self._normalize_delay(time_diff)
                if sleep_secs > 0:
                    comment = f"  # {delay_comment}" if delay_comment else ""
                    wait_before = f"    time.sleep({sleep_secs:.1f}){comment}\n"

            script_lines.append(wait_before)
            script_lines.append(self._generate_action_code_uiautomator(action, i))

        script_lines.extend([
            '',
            'if __name__ == "__main__":',
            '    run_test()',
        ])

        script_content = '\n'.join(script_lines)

        with open(filepath, 'w') as f:
            f.write(script_content)

        return str(filepath)

    def _export_as_adb_python(self, filepath: Path, test_name: str) -> str:
        """Export as ADB-based script (fully independent, no dependencies)."""
        script_lines = [
            '"""',
            f'Auto-generated test script: {test_name}',
            f'Generated: {self.start_time.isoformat()}',
            f'Total actions: {len(self.actions)}',
            '',
            'This script uses direct ADB commands and is fully independent.',
            'No external dependencies required beyond ADB.',
            '"""',
            '',
            'import subprocess',
            'import time',
            'import sys',
            '',
            '',
            'class DeviceController:',
            '    """Direct ADB device controller - no external dependencies.',
            '    ',
            '    Coordinates are passed as percentages (0-100) and converted to pixels',
            '    at runtime based on the actual device screen size. This makes scripts',
            '    resolution-independent."""',
            '    ',
            '    def __init__(self, device_id="emulator-5554"):',
            '        self.device_id = device_id',
            '        self._verify_device()',
            '        self.screen_width, self.screen_height = self._get_screen_size()',
            '        self.status_bar_h, self.nav_bar_h = self._get_system_bar_heights()',
            '        self.content_height = self.screen_height - self.status_bar_h - self.nav_bar_h',
            '        print(f"Screen: {self.screen_width}x{self.screen_height}, '
                         f'status_bar={self.status_bar_h}, nav_bar={self.nav_bar_h}, '
                         f'content={self.content_height}")',
            '    ',
            '    def _verify_device(self):',
            '        """Verify device is connected."""',
            '        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)',
            '        if self.device_id not in result.stdout:',
            '            raise Exception(f"Device {self.device_id} not found. Available devices:\\n{result.stdout}")',
            '    ',
            '    def _get_screen_size(self):',
            '        """Get device screen size via ADB."""',
            '        result = subprocess.run(',
            '            ["adb", "-s", self.device_id, "shell", "wm", "size"],',
            '            capture_output=True, text=True)',
            '        for line in result.stdout.splitlines():',
            '            if "size:" in line.lower():',
            '                w, h = line.split(":")[-1].strip().split("x")',
            '                return int(w), int(h)',
            '        return 1080, 1920  # sensible default',
            '    ',
            '    def _get_system_bar_heights(self):',
            '        """Get status bar and navigation bar heights via ADB."""',
            '        import re',
            '        status_h, nav_h = 0, 0',
            '        try:',
            '            result = subprocess.run(',
            '                ["adb", "-s", self.device_id, "shell", "dumpsys", "window"],',
            '                capture_output=True, text=True, timeout=5)',
            '            in_status = False',
            '            in_nav = False',
            '            for line in result.stdout.splitlines():',
            '                if "StatusBar" in line and "Window" in line:',
            '                    in_status = True',
            '                    in_nav = False',
            '                elif "NavigationBar" in line and "Window" in line:',
            '                    in_nav = True',
            '                    in_status = False',
            '                elif "Window #" in line:',
            '                    in_status = False',
            '                    in_nav = False',
            '                if in_status and "mFrame=" in line:',
            '                    m = re.search(r"mFrame=\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]", line)',
            '                    if m:',
            '                        status_h = int(m.group(4)) - int(m.group(2))',
            '                    in_status = False',
            '                if in_nav and "mFrame=" in line:',
            '                    m = re.search(r"mFrame=\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]", line)',
            '                    if m:',
            '                        nav_h = int(m.group(4)) - int(m.group(2))',
            '                    in_nav = False',
            '        except Exception:',
            '            pass',
            '        return status_h, nav_h',
            '    ',
            '    def _pct_to_px(self, x_pct, y_pct):',
            '        """Convert percentage coordinates to absolute pixels.',
            '        ',
            '        X: percentage of full screen width.',
            '        Y: percentage of content area (screen minus status bar and nav bar),',
            '           then offset by status bar height to get absolute screen Y."""',
            '        x = int(x_pct / 100 * self.screen_width)',
            '        y = int(y_pct / 100 * self.content_height + self.status_bar_h)',
            '        return x, y',
            '    ',
            '    def click(self, x_pct, y_pct):',
            '        """Click at percentage coordinates."""',
            '        x, y = self._pct_to_px(x_pct, y_pct)',
            '        cmd = f"adb -s {self.device_id} shell input tap {x} {y}"',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def long_click(self, x_pct, y_pct, duration=1000):',
            '        """Long click at percentage coordinates."""',
            '        x, y = self._pct_to_px(x_pct, y_pct)',
            '        cmd = f"adb -s {self.device_id} shell input touchscreen swipe {x} {y} {x} {y} {duration}"',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def swipe(self, x1_pct, y1_pct, x2_pct, y2_pct, duration=300):',
            '        """Swipe from one point to another using percentage coordinates."""',
            '        x1, y1 = self._pct_to_px(x1_pct, y1_pct)',
            '        x2, y2 = self._pct_to_px(x2_pct, y2_pct)',
            '        cmd = f"adb -s {self.device_id} shell input touchscreen swipe {x1} {y1} {x2} {y2} {duration}"',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def drag(self, x1_pct, y1_pct, x2_pct, y2_pct, duration=500):',
            '        """Drag from one point to another using percentage coordinates."""',
            '        x1, y1 = self._pct_to_px(x1_pct, y1_pct)',
            '        x2, y2 = self._pct_to_px(x2_pct, y2_pct)',
            '        cmd = f"adb -s {self.device_id} shell input touchscreen swipe {x1} {y1} {x2} {y2} {duration}"',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def type_text(self, text):',
            '        """Type text on device."""',
            '        cmd = f"adb -s {self.device_id} shell input text \\"{text}\\""',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def press_key(self, key_code):',
            '        """Press a key code."""',
            '        key_map = {',
            '            "ENTER": "66",',
            '            "BACK": "4",',
            '            "HOME": "3",',
            '            "MENU": "1",',
            '            "POWER": "26",',
            '            "VOLUME_UP": "24",',
            '            "VOLUME_DOWN": "25",',
            '        }',
            '        code = key_map.get(key_code.upper(), key_code)',
            '        cmd = f"adb -s {self.device_id} shell input keyevent {code}"',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def open_notification(self):',
            '        """Open notification bar."""',
            '        cmd = f"adb -s {self.device_id} shell cmd statusbar expand-notifications"',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def get_current_app(self):',
            '        """Returns current foreground package name via ADB."""',
            '        cmd = f"adb -s {self.device_id} shell dumpsys activity activities | grep mCurrentFocus"',
            '        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)',
            '        return result.stdout.strip()',
            '    ',
            '    def screenshot(self, path):',
            '        """Capture screenshot via ADB screencap."""',
            '        cmd = f"adb -s {self.device_id} exec-out screencap -p"',
            '        result = subprocess.run(cmd, shell=True, capture_output=True)',
            '        with open(path, "wb") as f:',
            '            f.write(result.stdout)',
            '    ',
            '',
            'def run_test(device_id="emulator-5554"):',
            '    """Run the recorded test sequence."""',
            '    print(f"Connecting to device: {device_id}")',
            '    device = DeviceController(device_id)',
            '    print("Device connected. Starting test...")',
            '    ',
        ]

        for i, action in enumerate(self.actions, 1):
            wait_before = ""
            if i > 1:
                prev_action = self.actions[i-2]
                time_diff = action.timestamp - prev_action.timestamp
                sleep_secs, delay_comment = self._normalize_delay(time_diff)
                if sleep_secs > 0:
                    comment = f"  # {delay_comment}" if delay_comment else ""
                    wait_before = f"    time.sleep({sleep_secs:.1f}){comment}\n"

            script_lines.append(wait_before)
            script_lines.append(self._generate_action_code_adb(action, i))

        script_lines.extend([
            '    ',
            '    print("Test completed successfully!")',
            '',
            '',
            'if __name__ == "__main__":',
            '    device_id = sys.argv[1] if len(sys.argv) > 1 else "emulator-5554"',
            '    try:',
            '        run_test(device_id)',
            '    except KeyboardInterrupt:',
            '        print("\\nTest interrupted by user")',
            '    except Exception as e:',
            '        print(f"Error: {e}")',
            '        sys.exit(1)',
        ])

        script_content = '\n'.join(script_lines)

        with open(filepath, 'w') as f:
            f.write(script_content)

        return str(filepath)

    def _make_step_comment(self, action: TestAction, action_num: int, action_label: str) -> str:
        """Build a step comment with optional element/screen context."""
        parts = [f"Step {action_num}: {action_label}"]
        if action.screen_app or action.screen_activity:
            activity = action.screen_activity or ""
            app = action.screen_app or ""
            screen = f"{app}/{activity}" if app and activity else (app or activity)
            parts[0] += f" -- {screen}"
        return "# " + parts[0]

    def _generate_action_code_uiautomator(self, action: TestAction, action_num: int) -> str:
        """Generate Python code for a single action using uiautomator2."""
        params = action.parameters
        indent = "    "
        sw = action.screen_width

        if action.action == "click":
            x_pct = self._to_pct_x(params["x"], sw)
            y_pct = self._to_pct_y(params["y"], action)
            comment = self._make_step_comment(action, action_num, f'Tap at ({x_pct}%, {y_pct}%)')
            return f'{indent}{comment}\n{indent}device.click({x_pct}, {y_pct})'

        elif action.action == "click_by_label":
            name = params.get("name", "")
            etype = action.element_type or "element"
            x_pct = self._to_pct_x(params["x"], sw)
            y_pct = self._to_pct_y(params["y"], action)
            label = f'Tap "{name}" {etype} at ({x_pct}%, {y_pct}%)'
            comment = self._make_step_comment(action, action_num, label)
            return f'{indent}{comment}\n{indent}device.click({x_pct}, {y_pct})'

        elif action.action == "long_click":
            x_pct = self._to_pct_x(params["x"], sw)
            y_pct = self._to_pct_y(params["y"], action)
            comment = self._make_step_comment(action, action_num, f'Long press at ({x_pct}%, {y_pct}%)')
            return f'{indent}{comment}\n{indent}device.long_click({x_pct}, {y_pct})'

        elif action.action == "swipe":
            x1_pct = self._to_pct_x(params["x1"], sw)
            y1_pct = self._to_pct_y(params["y1"], action)
            x2_pct = self._to_pct_x(params["x2"], sw)
            y2_pct = self._to_pct_y(params["y2"], action)
            comment = self._make_step_comment(action, action_num, f'Swipe from ({x1_pct}%, {y1_pct}%) to ({x2_pct}%, {y2_pct}%)')
            return f'{indent}{comment}\n{indent}device.swipe({x1_pct}, {y1_pct}, {x2_pct}, {y2_pct})'

        elif action.action == "type":
            text = params["text"].replace('"', '\\"')
            x_pct = self._to_pct_x(params["x"], sw)
            y_pct = self._to_pct_y(params["y"], action)
            field_name = action.element_name or f'({x_pct}%, {y_pct}%)'
            comment = self._make_step_comment(action, action_num, f'Type "{text}" in {field_name}')
            lines = f'{indent}{comment}\n'
            lines += f'{indent}device.click({x_pct}, {y_pct})\n'
            lines += f'{indent}device.send_keys("{text}")'
            return lines

        elif action.action == "drag":
            x1_pct = self._to_pct_x(params["x1"], sw)
            y1_pct = self._to_pct_y(params["y1"], action)
            x2_pct = self._to_pct_x(params["x2"], sw)
            y2_pct = self._to_pct_y(params["y2"], action)
            comment = self._make_step_comment(action, action_num, f'Drag from ({x1_pct}%, {y1_pct}%) to ({x2_pct}%, {y2_pct}%)')
            return f'{indent}{comment}\n{indent}device.drag({x1_pct}, {y1_pct}, {x2_pct}, {y2_pct})'

        elif action.action == "press":
            button = params["button"]
            comment = self._make_step_comment(action, action_num, f'Press {button} button')
            return f'{indent}{comment}\n{indent}device.press("{button}")'

        elif action.action == "notification":
            comment = self._make_step_comment(action, action_num, 'Open notification bar')
            return f'{indent}{comment}\n{indent}device.open_notification()'

        elif action.action == "wait":
            duration = params["duration"]
            comment = self._make_step_comment(action, action_num, f'Wait {duration} seconds')
            return f'{indent}{comment}\n{indent}time.sleep({duration})'

        else:
            return f'{indent}# Step {action_num}: {action.action} {params}'

    def _to_pct_x(self, x_px, screen_width):
        """Convert an X pixel coordinate to percentage of screen width."""
        if screen_width <= 0:
            return x_px
        return round(x_px / screen_width * 100, 2)

    def _to_pct_y(self, y_px, action: TestAction):
        """Convert a Y pixel coordinate to percentage of the content area.

        The content area excludes the status bar (top) and navigation bar (bottom).
        This makes Y percentages accurate across devices with different system bar sizes.
        """
        sh = action.screen_height
        if sh <= 0:
            return y_px
        sb = action.status_bar_height
        nb = action.nav_bar_height
        content_height = sh - sb - nb
        if content_height <= 0:
            return round(y_px / sh * 100, 2)
        # Map y relative to the content area (y=0 at top of content, below status bar)
        return round((y_px - sb) / content_height * 100, 2)

    def _generate_action_code_adb(self, action: TestAction, action_num: int) -> str:
        """Generate Python code for a single action using direct ADB commands."""
        params = action.parameters
        indent = "    "
        sw = action.screen_width

        if action.action == "click":
            x_pct = self._to_pct_x(params["x"], sw)
            y_pct = self._to_pct_y(params["y"], action)
            comment = self._make_step_comment(action, action_num, f'Tap at ({x_pct}%, {y_pct}%)')
            return f'{indent}{comment}\n{indent}device.click({x_pct}, {y_pct})'

        elif action.action == "click_by_label":
            name = params.get("name", "")
            etype = action.element_type or "element"
            x_pct = self._to_pct_x(params["x"], sw)
            y_pct = self._to_pct_y(params["y"], action)
            label = f'Tap "{name}" {etype} at ({x_pct}%, {y_pct}%)'
            comment = self._make_step_comment(action, action_num, label)
            return f'{indent}{comment}\n{indent}device.click({x_pct}, {y_pct})'

        elif action.action == "long_click":
            x_pct = self._to_pct_x(params["x"], sw)
            y_pct = self._to_pct_y(params["y"], action)
            comment = self._make_step_comment(action, action_num, f'Long press at ({x_pct}%, {y_pct}%)')
            return f'{indent}{comment}\n{indent}device.long_click({x_pct}, {y_pct})'

        elif action.action == "swipe":
            x1_pct = self._to_pct_x(params["x1"], sw)
            y1_pct = self._to_pct_y(params["y1"], action)
            x2_pct = self._to_pct_x(params["x2"], sw)
            y2_pct = self._to_pct_y(params["y2"], action)
            comment = self._make_step_comment(action, action_num, f'Swipe from ({x1_pct}%, {y1_pct}%) to ({x2_pct}%, {y2_pct}%)')
            return f'{indent}{comment}\n{indent}device.swipe({x1_pct}, {y1_pct}, {x2_pct}, {y2_pct})'

        elif action.action == "type":
            text = params["text"].replace('"', '\\"')
            x_pct = self._to_pct_x(params["x"], sw)
            y_pct = self._to_pct_y(params["y"], action)
            field_name = action.element_name or f'({x_pct}%, {y_pct}%)'
            comment = self._make_step_comment(action, action_num, f'Type "{text}" in {field_name}')
            lines = f'{indent}{comment}\n'
            lines += f'{indent}device.click({x_pct}, {y_pct})\n'
            lines += f'{indent}device.type_text("{text}")'
            return lines

        elif action.action == "drag":
            x1_pct = self._to_pct_x(params["x1"], sw)
            y1_pct = self._to_pct_y(params["y1"], action)
            x2_pct = self._to_pct_x(params["x2"], sw)
            y2_pct = self._to_pct_y(params["y2"], action)
            comment = self._make_step_comment(action, action_num, f'Drag from ({x1_pct}%, {y1_pct}%) to ({x2_pct}%, {y2_pct}%)')
            return f'{indent}{comment}\n{indent}device.drag({x1_pct}, {y1_pct}, {x2_pct}, {y2_pct})'

        elif action.action == "press":
            button = params["button"]
            comment = self._make_step_comment(action, action_num, f'Press {button} button')
            return f'{indent}{comment}\n{indent}device.press_key("{button}")'

        elif action.action == "notification":
            comment = self._make_step_comment(action, action_num, 'Open notification bar')
            return f'{indent}{comment}\n{indent}device.open_notification()'

        elif action.action == "wait":
            duration = params["duration"]
            comment = self._make_step_comment(action, action_num, f'Wait {duration} seconds')
            return f'{indent}{comment}\n{indent}time.sleep({duration})'

        else:
            return f'{indent}# Step {action_num}: {action.action} {params}'

    def export_as_pytest(self, filename: str = None, test_name: str = None) -> str:
        """Export recorded actions as a pytest-compatible test file."""
        if not filename:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_{timestamp}_pytest.py"

        if not test_name:
            test_name = filename.replace(".py", "").replace("-", "_")
            # Ensure valid Python identifier
            test_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in test_name)

        filepath = Path(filename)

        # Build class name from test_name (PascalCase)
        class_name = ''.join(word.capitalize() for word in test_name.split('_') if word)

        script_lines = [
            '"""',
            f'Auto-generated pytest test: {test_name}',
            f'Generated: {self.start_time.isoformat()}',
            f'Total actions: {len(self.actions)}',
            '',
            f'Run with pytest:  pytest {filename} -v',
            f'Run directly:     python {filename} [device_id]',
            '"""',
            '',
            'import subprocess',
            'import time',
            'import sys',
            '',
            'try:',
            '    import pytest',
            '    HAS_PYTEST = True',
            'except ImportError:',
            '    HAS_PYTEST = False',
            '',
            '',
            'class DeviceController:',
            '    """Direct ADB device controller - no external dependencies.',
            '    ',
            '    Coordinates are passed as percentages (0-100) and converted to pixels',
            '    at runtime based on the actual device screen size. This makes scripts',
            '    resolution-independent."""',
            '    ',
            '    def __init__(self, device_id="emulator-5554"):',
            '        self.device_id = device_id',
            '        self._verify_device()',
            '        self.screen_width, self.screen_height = self._get_screen_size()',
            '        self.status_bar_h, self.nav_bar_h = self._get_system_bar_heights()',
            '        self.content_height = self.screen_height - self.status_bar_h - self.nav_bar_h',
            '    ',
            '    def _verify_device(self):',
            '        """Verify device is connected."""',
            '        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)',
            '        if self.device_id not in result.stdout:',
            '            raise Exception(f"Device {self.device_id} not found. Available devices:\\n{result.stdout}")',
            '    ',
            '    def _get_screen_size(self):',
            '        """Get device screen size via ADB."""',
            '        result = subprocess.run(',
            '            ["adb", "-s", self.device_id, "shell", "wm", "size"],',
            '            capture_output=True, text=True)',
            '        for line in result.stdout.splitlines():',
            '            if "size:" in line.lower():',
            '                w, h = line.split(":")[-1].strip().split("x")',
            '                return int(w), int(h)',
            '        return 1080, 1920  # sensible default',
            '    ',
            '    def _get_system_bar_heights(self):',
            '        """Get status bar and navigation bar heights via ADB."""',
            '        status_h, nav_h = 0, 0',
            '        try:',
            '            result = subprocess.run(',
            '                ["adb", "-s", self.device_id, "shell", "dumpsys", "window"],',
            '                capture_output=True, text=True, timeout=5)',
            '            in_status = False',
            '            in_nav = False',
            '            for line in result.stdout.splitlines():',
            '                if "StatusBar" in line and "Window" in line:',
            '                    in_status = True',
            '                    in_nav = False',
            '                elif "NavigationBar" in line and "Window" in line:',
            '                    in_nav = True',
            '                    in_status = False',
            '                elif "Window #" in line:',
            '                    in_status = False',
            '                    in_nav = False',
            '                if in_status and "mFrame=" in line:',
            '                    m = re.search(r"mFrame=\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]", line)',
            '                    if m:',
            '                        status_h = int(m.group(4)) - int(m.group(2))',
            '                    in_status = False',
            '                if in_nav and "mFrame=" in line:',
            '                    m = re.search(r"mFrame=\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]", line)',
            '                    if m:',
            '                        nav_h = int(m.group(4)) - int(m.group(2))',
            '                    in_nav = False',
            '        except Exception:',
            '            pass',
            '        return status_h, nav_h',
            '    ',
            '    def _pct_to_px(self, x_pct, y_pct):',
            '        """Convert percentage coordinates to absolute pixels.',
            '        ',
            '        X: percentage of full screen width.',
            '        Y: percentage of content area (screen minus status bar and nav bar),',
            '           then offset by status bar height to get absolute screen Y."""',
            '        x = int(x_pct / 100 * self.screen_width)',
            '        y = int(y_pct / 100 * self.content_height + self.status_bar_h)',
            '        return x, y',
            '    ',
            '    def _adb(self, *args):',
            '        """Run an ADB command and return stdout."""',
            '        cmd = ["adb", "-s", self.device_id] + list(args)',
            '        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)',
            '        return result.stdout.strip()',
            '    ',
            '    def click(self, x_pct, y_pct):',
            '        """Click at percentage coordinates."""',
            '        x, y = self._pct_to_px(x_pct, y_pct)',
            '        self._adb("shell", f"input tap {x} {y}")',
            '    ',
            '    def long_click(self, x_pct, y_pct, duration=1000):',
            '        """Long click at percentage coordinates."""',
            '        x, y = self._pct_to_px(x_pct, y_pct)',
            '        self._adb("shell", f"input touchscreen swipe {x} {y} {x} {y} {duration}")',
            '    ',
            '    def swipe(self, x1_pct, y1_pct, x2_pct, y2_pct, duration=300):',
            '        """Swipe from one point to another using percentage coordinates."""',
            '        x1, y1 = self._pct_to_px(x1_pct, y1_pct)',
            '        x2, y2 = self._pct_to_px(x2_pct, y2_pct)',
            '        self._adb("shell", f"input touchscreen swipe {x1} {y1} {x2} {y2} {duration}")',
            '    ',
            '    def drag(self, x1_pct, y1_pct, x2_pct, y2_pct, duration=500):',
            '        """Drag from one point to another using percentage coordinates."""',
            '        x1, y1 = self._pct_to_px(x1_pct, y1_pct)',
            '        x2, y2 = self._pct_to_px(x2_pct, y2_pct)',
            '        self._adb("shell", f"input touchscreen swipe {x1} {y1} {x2} {y2} {duration}")',
            '    ',
            '    def type_text(self, text):',
            '        """Type text on device."""',
            "        escaped = text.replace(' ', '%s').replace(\"'\", \"\\\\\\\\'\")",
            "        self._adb('shell', f\"input text '{escaped}'\")",
            '    ',
            '    def press_key(self, key_code):',
            '        """Press a key code."""',
            '        key_map = {',
            '            "ENTER": "66", "BACK": "4", "HOME": "3", "MENU": "1",',
            '            "POWER": "26", "VOLUME_UP": "24", "VOLUME_DOWN": "25",',
            '        }',
            '        code = key_map.get(key_code.upper(), key_code)',
            '        self._adb("shell", f"input keyevent {code}")',
            '    ',
            '    def open_notification(self):',
            '        """Open notification bar."""',
            '        self._adb("shell", "cmd statusbar expand-notifications")',
            '    ',
            '    def screenshot(self, path: str):',
            '        """Capture screenshot via ADB screencap."""',
            '        data = subprocess.run(',
            '            ["adb", "-s", self.device_id, "exec-out", "screencap", "-p"],',
            '            capture_output=True, timeout=10',
            '        )',
            '        with open(path, "wb") as f:',
            '            f.write(data.stdout)',
            '    ',
            '',
            '',
            'if HAS_PYTEST:',
            '    @pytest.fixture(scope="module")',
            '    def device():',
            '        """Create a device controller for the test module."""',
            '        d = DeviceController("emulator-5554")',
            '        yield d',
            '',
            '',
            f'class Test{class_name}:',
            f'    """Recorded test: {test_name}"""',
            '',
            f'    def test_{test_name}(self, device, request=None):',
            '        try:',
        ]

        test_indent = "            "
        for i, action in enumerate(self.actions):
            action_num = i + 1

            # Delay between actions
            if i > 0:
                prev_action = self.actions[i - 1]
                time_diff = action.timestamp - prev_action.timestamp
                sleep_secs, delay_comment = self._normalize_delay(time_diff)
                if sleep_secs > 0:
                    comment = f"  # {delay_comment}" if delay_comment else ""
                    script_lines.append(f"{test_indent}time.sleep({sleep_secs:.1f}){comment}")

            # Generate action code and re-indent from 4 to 12 spaces
            action_code = self._generate_action_code_adb(action, action_num)
            reindented_lines = []
            for j, line in enumerate(action_code.split('\n')):
                if line.startswith("    "):
                    reindented_lines.append(test_indent + line[4:])
                else:
                    reindented_lines.append(line)
            script_lines.append('\n'.join(reindented_lines))

        script_lines.extend([
            '        except Exception as e:',
            '            # Screenshot on failure for debugging',
            '            name = request.node.name if request else "direct_run"',
            '            device.screenshot(f"failure_{name}.png")',
            '            raise',
            '',
            '',
            'def run_test(device_id="emulator-5554"):',
            '    """Run the test directly without pytest."""',
            '    print(f"Connecting to device: {device_id}")',
            '    device = DeviceController(device_id)',
            '    print("Device connected. Running test...")',
            f'    test = Test{class_name}()',
            '    try:',
            f'        test.test_{test_name}(device)',
            '        print("\\nTEST PASSED")',
            '    except Exception as e:',
            '        print(f"\\nTEST ERROR: {e}")',
            '        sys.exit(1)',
            '',
            '',
            'if __name__ == "__main__":',
            '    device_id = sys.argv[1] if len(sys.argv) > 1 else "emulator-5554"',
            '    run_test(device_id)',
        ])

        script_content = '\n'.join(script_lines)

        with open(filepath, 'w') as f:
            f.write(script_content)

        return str(filepath)

    def export_as_readable(self, filename: str = None) -> str:
        """Export recorded actions as human-readable test steps."""
        if not filename:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_steps_{timestamp}.txt"

        filepath = Path(filename)

        lines = [
            f"Test Script: {filename.replace('.txt', '')}",
            f"Generated: {self.start_time.isoformat()}",
            f"Total Actions: {len(self.actions)}",
            "",
            "=" * 60,
            "TEST STEPS:",
            "=" * 60,
            "",
        ]

        for i, action in enumerate(self.actions, 1):
            description = self._get_action_description(action, i)
            lines.append(f"{i}. {description}")
            if action.screen_app or action.screen_activity:
                screen = f"{action.screen_app}/{action.screen_activity}" if action.screen_app and action.screen_activity else (action.screen_app or action.screen_activity)
                lines.append(f"   Screen: {screen}")
            if action.description:
                lines.append(f"   Note: {action.description}")
            lines.append("")

        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))

        return str(filepath)

    def _get_action_description(self, action: TestAction, action_num: int) -> str:
        """Generate a human-readable description of an action."""
        params = action.parameters

        if action.action == "click":
            if action.element_name:
                return f"Tap '{action.element_name}' ({action.element_type or 'element'}) at ({params['x']}, {params['y']})"
            return f"Tap at coordinates ({params['x']}, {params['y']})"
        elif action.action == "click_by_label":
            name = params.get("name", "")
            etype = action.element_type or "element"
            return f"Tap '{name}' ({etype}) at ({params['x']}, {params['y']})"
        elif action.action == "long_click":
            return f"Long press at coordinates ({params['x']}, {params['y']})"
        elif action.action == "swipe":
            return f"Swipe from ({params['x1']}, {params['y1']}) to ({params['x2']}, {params['y2']})"
        elif action.action == "type":
            field = f" in '{action.element_name}'" if action.element_name else ""
            return f'Type text: "{params["text"]}"{field}'
        elif action.action == "drag":
            return f"Drag from ({params['x1']}, {params['y1']}) to ({params['x2']}, {params['y2']})"
        elif action.action == "press":
            return f"Press {params['button']} button"
        elif action.action == "notification":
            return "Open notification bar"
        elif action.action == "wait":
            return f"Wait for {params['duration']} seconds"
        else:
            return f"{action.action.capitalize()}: {params}"
