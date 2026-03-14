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
                      screen_activity: str = ""):
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
            '"""',
            '',
            'import uiautomator2 as u2',
            'import time',
            '',
            'def run_test(device=None):',
            '    """Run the recorded test sequence."""',
            '    if device is None:',
            '        device = u2.connect()',
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
            '    """Direct ADB device controller - no external dependencies."""',
            '    ',
            '    def __init__(self, device_id="emulator-5554"):',
            '        self.device_id = device_id',
            '        self._verify_device()',
            '    ',
            '    def _verify_device(self):',
            '        """Verify device is connected."""',
            '        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)',
            '        if self.device_id not in result.stdout:',
            '            raise Exception(f"Device {self.device_id} not found. Available devices:\\n{result.stdout}")',
            '    ',
            '    def click(self, x, y):',
            '        """Click at coordinates."""',
            '        cmd = f"adb -s {self.device_id} shell input tap {x} {y}"',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def long_click(self, x, y, duration=1000):',
            '        """Long click at coordinates."""',
            '        cmd = f"adb -s {self.device_id} shell input touchscreen swipe {x} {y} {x} {y} {duration}"',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def swipe(self, x1, y1, x2, y2, duration=300):',
            '        """Swipe from one point to another."""',
            '        cmd = f"adb -s {self.device_id} shell input touchscreen swipe {x1} {y1} {x2} {y2} {duration}"',
            '        subprocess.run(cmd, shell=True)',
            '    ',
            '    def drag(self, x1, y1, x2, y2, duration=500):',
            '        """Drag from one point to another."""',
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

        if action.action == "click":
            comment = self._make_step_comment(action, action_num, f'Tap at ({params["x"]}, {params["y"]})')
            return f'{indent}{comment}\n{indent}device.click({params["x"]}, {params["y"]})'

        elif action.action == "click_by_label":
            name = params.get("name", "")
            etype = action.element_type or "element"
            label = f'Tap "{name}" {etype} at ({params["x"]}, {params["y"]})'
            comment = self._make_step_comment(action, action_num, label)
            return f'{indent}{comment}\n{indent}device.click({params["x"]}, {params["y"]})'

        elif action.action == "long_click":
            comment = self._make_step_comment(action, action_num, f'Long press at ({params["x"]}, {params["y"]})')
            return f'{indent}{comment}\n{indent}device.long_click({params["x"]}, {params["y"]})'

        elif action.action == "swipe":
            comment = self._make_step_comment(action, action_num, f'Swipe from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})')
            return f'{indent}{comment}\n{indent}device.swipe({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

        elif action.action == "type":
            text = params["text"].replace('"', '\\"')
            field_name = action.element_name or f'({params["x"]}, {params["y"]})'
            comment = self._make_step_comment(action, action_num, f'Type "{text}" in {field_name}')
            lines = f'{indent}{comment}\n'
            lines += f'{indent}device.click({params["x"]}, {params["y"]})\n'
            lines += f'{indent}device.send_keys("{text}")'
            return lines

        elif action.action == "drag":
            comment = self._make_step_comment(action, action_num, f'Drag from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})')
            return f'{indent}{comment}\n{indent}device.drag({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

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

    def _generate_action_code_adb(self, action: TestAction, action_num: int) -> str:
        """Generate Python code for a single action using direct ADB commands."""
        params = action.parameters
        indent = "    "

        if action.action == "click":
            comment = self._make_step_comment(action, action_num, f'Tap at ({params["x"]}, {params["y"]})')
            return f'{indent}{comment}\n{indent}device.click({params["x"]}, {params["y"]})'

        elif action.action == "click_by_label":
            name = params.get("name", "")
            etype = action.element_type or "element"
            label = f'Tap "{name}" {etype} at ({params["x"]}, {params["y"]})'
            comment = self._make_step_comment(action, action_num, label)
            return f'{indent}{comment}\n{indent}device.click({params["x"]}, {params["y"]})'

        elif action.action == "long_click":
            comment = self._make_step_comment(action, action_num, f'Long press at ({params["x"]}, {params["y"]})')
            return f'{indent}{comment}\n{indent}device.long_click({params["x"]}, {params["y"]})'

        elif action.action == "swipe":
            comment = self._make_step_comment(action, action_num, f'Swipe from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})')
            return f'{indent}{comment}\n{indent}device.swipe({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

        elif action.action == "type":
            text = params["text"].replace('"', '\\"')
            field_name = action.element_name or f'({params["x"]}, {params["y"]})'
            comment = self._make_step_comment(action, action_num, f'Type "{text}" in {field_name}')
            lines = f'{indent}{comment}\n'
            lines += f'{indent}device.click({params["x"]}, {params["y"]})\n'
            lines += f'{indent}device.type_text("{text}")'
            return lines

        elif action.action == "drag":
            comment = self._make_step_comment(action, action_num, f'Drag from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})')
            return f'{indent}{comment}\n{indent}device.drag({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

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

    def _compute_assertions(self) -> dict:
        """Pre-compute assertion data by analyzing screen transitions between actions.

        Returns a dict mapping action index (0-based) to a list of assertion dicts.
        Each assertion dict has: type, expected, message.
        """
        assertions = {}
        for i, action in enumerate(self.actions):
            action_asserts = []
            next_action = self.actions[i + 1] if i + 1 < len(self.actions) else None

            # Detect screen transition: next action has different app or activity
            if next_action and next_action.screen_app:
                app_changed = (action.screen_app and
                               next_action.screen_app != action.screen_app)
                activity_changed = (action.screen_activity and
                                    next_action.screen_activity and
                                    next_action.screen_activity != action.screen_activity)

                if app_changed:
                    action_asserts.append({
                        'type': 'app',
                        'expected': next_action.screen_app,
                        'message': f'Expected to navigate to {next_action.screen_app}',
                    })
                if activity_changed:
                    action_asserts.append({
                        'type': 'activity',
                        'expected': next_action.screen_activity,
                        'message': f'Expected screen {next_action.screen_activity}',
                    })
                elif not app_changed and action.action in ('click_by_label', 'click', 'press'):
                    # Same screen — assert app didn't crash
                    action_asserts.append({
                        'type': 'app_alive',
                        'expected': action.screen_app or next_action.screen_app,
                        'message': 'App should still be in foreground',
                    })

            # After type: assert app didn't crash
            if action.action == 'type' and action.screen_app and not action_asserts:
                action_asserts.append({
                    'type': 'app_alive',
                    'expected': action.screen_app,
                    'message': 'App should still be in foreground after typing',
                })

            if action_asserts:
                assertions[i] = action_asserts

        return assertions

    def _generate_assertion_code(self, asserts: list, indent: str) -> str:
        """Generate Python assertion lines from assertion dicts."""
        lines = []
        for a in asserts:
            if a['type'] == 'activity':
                lines.append(f'{indent}time.sleep(0.5)  # wait for navigation')
                lines.append(
                    f'{indent}assert "{a["expected"]}" in device.get_current_activity(), '
                    f'"{a["message"]}"'
                )
            elif a['type'] == 'app':
                lines.append(f'{indent}time.sleep(0.5)  # wait for navigation')
                lines.append(
                    f'{indent}assert "{a["expected"]}" in device.get_current_app(), '
                    f'"{a["message"]}"'
                )
            elif a['type'] == 'app_alive':
                lines.append(
                    f'{indent}assert "{a["expected"]}" in device.get_current_app(), '
                    f'"{a["message"]}"'
                )
        return '\n'.join(lines)

    def export_as_pytest(self, filename: str = None, test_name: str = None) -> str:
        """Export recorded actions as a pytest-compatible test file with assertions."""
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

        # Pre-compute assertions from screen transition analysis
        assertions = self._compute_assertions()

        script_lines = [
            '"""',
            f'Auto-generated pytest test: {test_name}',
            f'Generated: {self.start_time.isoformat()}',
            f'Total actions: {len(self.actions)}',
            f'Assertions: {sum(len(v) for v in assertions.values())}',
            '',
            f'Run with: pytest {filename} -v',
            '"""',
            '',
            'import subprocess',
            'import re',
            'import time',
            'import pytest',
            '',
            '',
            'class DeviceController:',
            '    """Direct ADB device controller - no external dependencies."""',
            '    ',
            '    def __init__(self, device_id="emulator-5554"):',
            '        self.device_id = device_id',
            '        self._verify_device()',
            '    ',
            '    def _verify_device(self):',
            '        """Verify device is connected."""',
            '        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)',
            '        if self.device_id not in result.stdout:',
            '            raise Exception(f"Device {self.device_id} not found. Available devices:\\n{result.stdout}")',
            '    ',
            '    def _adb(self, *args):',
            '        """Run an ADB command and return stdout."""',
            '        cmd = ["adb", "-s", self.device_id] + list(args)',
            '        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)',
            '        return result.stdout.strip()',
            '    ',
            '    def click(self, x, y):',
            '        """Click at coordinates."""',
            '        self._adb("shell", f"input tap {x} {y}")',
            '    ',
            '    def long_click(self, x, y, duration=1000):',
            '        """Long click at coordinates."""',
            '        self._adb("shell", f"input touchscreen swipe {x} {y} {x} {y} {duration}")',
            '    ',
            '    def swipe(self, x1, y1, x2, y2, duration=300):',
            '        """Swipe from one point to another."""',
            '        self._adb("shell", f"input touchscreen swipe {x1} {y1} {x2} {y2} {duration}")',
            '    ',
            '    def drag(self, x1, y1, x2, y2, duration=500):',
            '        """Drag from one point to another."""',
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
            '    def get_current_app(self) -> str:',
            '        """Returns current foreground package name via ADB."""',
            '        output = self._adb("shell", "dumpsys activity activities")',
            '        for line in output.splitlines():',
            '            if "mCurrentFocus" in line or "mFocusedApp" in line:',
            '                return line',
            '        return ""',
            '    ',
            '    def get_current_activity(self) -> str:',
            '        """Returns current foreground activity (package/activity) via ADB."""',
            '        output = self._adb("shell", "dumpsys activity activities")',
            '        for line in output.splitlines():',
            '            if "mCurrentFocus" in line or "mFocusedApp" in line:',
            '                match = re.search(r"(\\S+/\\S+)\\}", line)',
            '                if match:',
            '                    return match.group(1)',
            '        return ""',
            '    ',
            '    def has_text_on_screen(self, text: str) -> bool:',
            '        """Check if text exists in current UI hierarchy."""',
            '        output = self._adb("exec-out", "uiautomator dump /dev/tty")',
            '        return text in output',
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
            '@pytest.fixture(scope="module")',
            'def device():',
            '    """Create a device controller for the test module."""',
            '    d = DeviceController("emulator-5554")',
            '    yield d',
            '',
            '',
            f'class Test{class_name}:',
            f'    """Recorded test: {test_name}"""',
            '',
            f'    def test_{test_name}(self, device, request):',
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

            # Insert assertions after this action
            if i in assertions:
                assertion_code = self._generate_assertion_code(assertions[i], test_indent)
                script_lines.append(assertion_code)

        # Final assertion: verify app is still alive at end of test
        last_app = ""
        for action in reversed(self.actions):
            if action.screen_app:
                last_app = action.screen_app
                break
        if last_app:
            script_lines.append(f'{test_indent}')
            script_lines.append(f'{test_indent}# Final verification: app is still running')
            script_lines.append(
                f'{test_indent}assert "{last_app}" in device.get_current_app(), '
                f'"App {last_app} should still be in foreground at end of test"'
            )

        script_lines.extend([
            '        except Exception as e:',
            '            # Screenshot on failure for debugging',
            '            device.screenshot(f"failure_{request.node.name}.png")',
            '            raise',
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
