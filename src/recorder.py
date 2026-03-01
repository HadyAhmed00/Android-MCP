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

    def record_action(self, action: str, parameters: dict, result: str = "", description: str = ""):
        """Record a single action."""
        if not self.is_recording:
            return

        timestamp = (datetime.now() - self.start_time).total_seconds()
        test_action = TestAction(
            action=action,
            timestamp=timestamp,
            parameters=parameters,
            result=result,
            description=description
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
            "duration_seconds": sum(
                action.timestamp for action in self.actions
            ) if self.actions else 0,
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
            'import subprocess',
            'import time',
            'import os',
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
                if time_diff > 0.5:  # Add delay if there was a significant gap
                    capped = min(time_diff, 2.0)  # cap at 2s; recording overhead is not needed on replay
                    wait_before = f"    time.sleep({capped:.1f})\n"

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
            'import os',
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
            '    def click_element_by_text(self, text, x_fallback, y_fallback):',
            '        """Smart click: text first (handles screen resize), coords fallback (handles text changes)."""',
            '        import re',
            '        try:',
            '            subprocess.run(f"adb -s {self.device_id} shell uiautomator dump /sdcard/_d.xml",',
            '                           shell=True, capture_output=True, timeout=8)',
            '            r = subprocess.run(f"adb -s {self.device_id} shell cat /sdcard/_d.xml",',
            '                               shell=True, capture_output=True, text=True, timeout=5)',
            '            for node in re.findall(r"<node[^>]+>", r.stdout):',
            '                t_m = re.search(r\'text="([^"]*)"\', node)',
            '                cd_m = re.search(r\'content-desc="([^"]*)"\', node)',
            '                found = ((t_m and text.lower() in t_m.group(1).lower()) or',
            '                         (cd_m and text.lower() in cd_m.group(1).lower()))',
            '                if found and \'bounds="\' in node:',
            '                    coords = re.findall(r\'\\d+\', node.split(\'bounds="\')[1].split(\'"\')[0])',
            '                    if len(coords) >= 4:',
            '                        x = (int(coords[0]) + int(coords[2])) // 2',
            '                        y = (int(coords[1]) + int(coords[3])) // 2',
            '                        self.click(x, y)',
            '                        return',
            '        except Exception:',
            '            pass',
            '        self.click(x_fallback, y_fallback)  # coords fallback',
            '    ',
            '    def long_click_element_by_text(self, text, x_fallback, y_fallback):',
            '        """Smart long click: text first (handles screen resize), coords fallback (handles text changes)."""',
            '        import re',
            '        try:',
            '            subprocess.run(f"adb -s {self.device_id} shell uiautomator dump /sdcard/_d.xml",',
            '                           shell=True, capture_output=True, timeout=8)',
            '            r = subprocess.run(f"adb -s {self.device_id} shell cat /sdcard/_d.xml",',
            '                               shell=True, capture_output=True, text=True, timeout=5)',
            '            for node in re.findall(r"<node[^>]+>", r.stdout):',
            '                t_m = re.search(r\'text="([^"]*)"\', node)',
            '                cd_m = re.search(r\'content-desc="([^"]*)"\', node)',
            '                found = ((t_m and text.lower() in t_m.group(1).lower()) or',
            '                         (cd_m and text.lower() in cd_m.group(1).lower()))',
            '                if found and \'bounds="\' in node:',
            '                    coords = re.findall(r\'\\d+\', node.split(\'bounds="\')[1].split(\'"\')[0])',
            '                    if len(coords) >= 4:',
            '                        x = (int(coords[0]) + int(coords[2])) // 2',
            '                        y = (int(coords[1]) + int(coords[3])) // 2',
            '                        self.long_click(x, y)',
            '                        return',
            '        except Exception:',
            '            pass',
            '        self.long_click(x_fallback, y_fallback)  # coords fallback',
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
                if time_diff > 0.5:  # Add delay if there was a significant gap
                    capped = min(time_diff, 2.0)  # cap at 2s; recording overhead is not needed on replay
                    wait_before = f"    time.sleep({capped:.1f})\n"

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

    def _generate_action_code_uiautomator(self, action: TestAction, action_num: int) -> str:
        """Generate Python code for a single action using uiautomator2."""
        params = action.parameters
        indent = "    "

        if action.action == "click":
            return f'{indent}# Action {action_num}: Click at ({params["x"]}, {params["y"]})\n{indent}device.click({params["x"]}, {params["y"]})'

        elif action.action == "long_click":
            return f'{indent}# Action {action_num}: Long click at ({params["x"]}, {params["y"]})\n{indent}device.long_click({params["x"]}, {params["y"]})'

        elif action.action == "swipe":
            return f'{indent}# Action {action_num}: Swipe from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})\n{indent}device.swipe({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

        elif action.action == "type":
            if params.get('sensitive'):
                var_name = params.get('var_name', 'SENSITIVE_INPUT')
                return f'{indent}# Action {action_num}: Type sensitive input (from env var)\n{indent}device.send_keys(os.environ["{var_name}"])'
            text = params["text"].replace('"', '\\"')
            return f'{indent}# Action {action_num}: Type "{text}"\n{indent}device.send_keys("{text}")'

        elif action.action == "drag":
            return f'{indent}# Action {action_num}: Drag from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})\n{indent}device.drag({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

        elif action.action == "press":
            button = params["button"]
            return f'{indent}# Action {action_num}: Press {button} button\n{indent}device.press("{button}")'

        elif action.action == "notification":
            return f'{indent}# Action {action_num}: Open notification bar\n{indent}device.open_notification()'

        elif action.action == "click_element":
            text = params["text"].replace('"', '\\"')
            x, y = params["x"], params["y"]
            return '\n'.join([
                f'{indent}# Action {action_num}: Click element "{text}"  [coords: ({x}, {y})]',
                f'{indent}_el = device(text="{text}")',
                f'{indent}if not _el.exists(timeout=3):',
                f'{indent}    _el = device(textContains="{text}")',
                f'{indent}if _el.exists(timeout=2):',
                f'{indent}    _el.click()',
                f'{indent}else:',
                f'{indent}    device.click({x}, {y})  # coords fallback',
            ])

        elif action.action == "long_click_element":
            text = params["text"].replace('"', '\\"')
            x, y = params["x"], params["y"]
            return '\n'.join([
                f'{indent}# Action {action_num}: Long click element "{text}"  [coords: ({x}, {y})]',
                f'{indent}_el = device(text="{text}")',
                f'{indent}if not _el.exists(timeout=3):',
                f'{indent}    _el = device(textContains="{text}")',
                f'{indent}if _el.exists(timeout=2):',
                f'{indent}    _el.long_click()',
                f'{indent}else:',
                f'{indent}    device.long_click({x}, {y})  # coords fallback',
            ])

        elif action.action == "type_element":
            if params.get('sensitive'):
                var_name = params.get('var_name', 'SENSITIVE_INPUT')
                return f'{indent}# Action {action_num}: Type sensitive input on element "{params["element_text"]}" (from env var)\n{indent}device.click({params["x"]}, {params["y"]})\n{indent}device.send_keys(os.environ["{var_name}"])'
            text = params["input_text"].replace('"', '\\"')
            return f'{indent}# Action {action_num}: Type "{text}" on element "{params["element_text"]}" at ({params["x"]}, {params["y"]})\n{indent}device.click({params["x"]}, {params["y"]})\n{indent}device.send_keys("{text}")'

        elif action.action == "launch_app":
            pkg = params["package"]
            return f'{indent}# Action {action_num}: Launch app {pkg}\n{indent}subprocess.run(["adb", "shell", "monkey", "-p", "{pkg}", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True)'

        elif action.action == "kill_app":
            pkg = params["package"]
            return f'{indent}# Action {action_num}: Force stop app {pkg}\n{indent}subprocess.run(["adb", "shell", "am", "force-stop", "{pkg}"], capture_output=True)'

        elif action.action == "clear_app_data":
            pkg = params["package"]
            return f'{indent}# Action {action_num}: Clear data for app {pkg}\n{indent}subprocess.run(["adb", "shell", "pm", "clear", "{pkg}"], capture_output=True)'

        elif action.action == "wait_for_condition":
            elapsed = params.get("elapsed", params.get("timeout", 5))
            conditions = []
            if params.get("element_text"):
                conditions.append('element "' + params["element_text"] + '" to appear')
            if params.get("element_gone"):
                conditions.append('element "' + params["element_gone"] + '" to disappear')
            if params.get("activity_name"):
                conditions.append('activity "' + params["activity_name"] + '" to load')
            desc = ', '.join(conditions) if conditions else 'condition'
            return f'{indent}# Action {action_num}: Wait for {desc} (took {elapsed}s during recording)\n{indent}time.sleep({elapsed})'

        elif action.action == "wait":
            duration = params["duration"]
            return f'{indent}# Action {action_num}: Wait {duration} seconds\n{indent}time.sleep({duration})'

        else:
            return f'{indent}# Action {action_num}: {action.action} {params}'

    def _generate_action_code_adb(self, action: TestAction, action_num: int) -> str:
        """Generate Python code for a single action using direct ADB commands."""
        params = action.parameters
        indent = "    "

        if action.action == "click":
            return f'{indent}# Action {action_num}: Click at ({params["x"]}, {params["y"]})\n{indent}device.click({params["x"]}, {params["y"]})'

        elif action.action == "long_click":
            return f'{indent}# Action {action_num}: Long click at ({params["x"]}, {params["y"]})\n{indent}device.long_click({params["x"]}, {params["y"]})'

        elif action.action == "swipe":
            return f'{indent}# Action {action_num}: Swipe from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})\n{indent}device.swipe({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

        elif action.action == "type":
            if params.get('sensitive'):
                var_name = params.get('var_name', 'SENSITIVE_INPUT')
                return f'{indent}# Action {action_num}: Type sensitive input (from env var)\n{indent}device.type_text(os.environ["{var_name}"])'
            text = params["text"].replace('"', '\\"')
            return f'{indent}# Action {action_num}: Type "{text}"\n{indent}device.type_text("{text}")'

        elif action.action == "drag":
            return f'{indent}# Action {action_num}: Drag from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})\n{indent}device.drag({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

        elif action.action == "press":
            button = params["button"]
            return f'{indent}# Action {action_num}: Press {button} button\n{indent}device.press_key("{button}")'

        elif action.action == "notification":
            return f'{indent}# Action {action_num}: Open notification bar\n{indent}device.open_notification()'

        elif action.action == "click_element":
            text = params["text"].replace('"', '\\"')
            x, y = params["x"], params["y"]
            return (f'{indent}# Action {action_num}: Click element "{text}"  [coords: ({x}, {y})]\n'
                    f'{indent}device.click_element_by_text("{text}", {x}, {y})')

        elif action.action == "long_click_element":
            text = params["text"].replace('"', '\\"')
            x, y = params["x"], params["y"]
            return (f'{indent}# Action {action_num}: Long click element "{text}"  [coords: ({x}, {y})]\n'
                    f'{indent}device.long_click_element_by_text("{text}", {x}, {y})')

        elif action.action == "type_element":
            if params.get('sensitive'):
                var_name = params.get('var_name', 'SENSITIVE_INPUT')
                return f'{indent}# Action {action_num}: Type sensitive input on element "{params["element_text"]}" (from env var)\n{indent}device.click({params["x"]}, {params["y"]})\n{indent}device.type_text(os.environ["{var_name}"])'
            text = params["input_text"].replace('"', '\\"')
            return f'{indent}# Action {action_num}: Type "{text}" on element "{params["element_text"]}" at ({params["x"]}, {params["y"]})\n{indent}device.click({params["x"]}, {params["y"]})\n{indent}device.type_text("{text}")'

        elif action.action == "launch_app":
            pkg = params["package"]
            return f'{indent}# Action {action_num}: Launch app {pkg}\n{indent}subprocess.run(f"adb -s {{device.device_id}} shell monkey -p {pkg} -c android.intent.category.LAUNCHER 1", shell=True, capture_output=True)'

        elif action.action == "kill_app":
            pkg = params["package"]
            return f'{indent}# Action {action_num}: Force stop app {pkg}\n{indent}subprocess.run(f"adb -s {{device.device_id}} shell am force-stop {pkg}", shell=True, capture_output=True)'

        elif action.action == "clear_app_data":
            pkg = params["package"]
            return f'{indent}# Action {action_num}: Clear data for app {pkg}\n{indent}subprocess.run(f"adb -s {{device.device_id}} shell pm clear {pkg}", shell=True, capture_output=True)'

        elif action.action == "wait_for_condition":
            elapsed = params.get("elapsed", params.get("timeout", 5))
            conditions = []
            if params.get("element_text"):
                conditions.append('element "' + params["element_text"] + '" to appear')
            if params.get("element_gone"):
                conditions.append('element "' + params["element_gone"] + '" to disappear')
            if params.get("activity_name"):
                conditions.append('activity "' + params["activity_name"] + '" to load')
            desc = ', '.join(conditions) if conditions else 'condition'
            return f'{indent}# Action {action_num}: Wait for {desc} (took {elapsed}s during recording)\n{indent}time.sleep({elapsed})'

        elif action.action == "wait":
            duration = params["duration"]
            return f'{indent}# Action {action_num}: Wait {duration} seconds\n{indent}time.sleep({duration})'

        else:
            return f'{indent}# Action {action_num}: {action.action} {params}'

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
            return f"Click at coordinates ({params['x']}, {params['y']})"
        elif action.action == "long_click":
            return f"Long click at coordinates ({params['x']}, {params['y']})"
        elif action.action == "swipe":
            return f"Swipe from ({params['x1']}, {params['y1']}) to ({params['x2']}, {params['y2']})"
        elif action.action == "type":
            if params.get('sensitive'):
                return f"Type sensitive input (env var: {params.get('var_name', 'SENSITIVE_INPUT')})"
            return f"Type text: \"{params['text']}\""
        elif action.action == "drag":
            return f"Drag from ({params['x1']}, {params['y1']}) to ({params['x2']}, {params['y2']})"
        elif action.action == "press":
            return f"Press {params['button']} button"
        elif action.action == "click_element":
            return f"Click on element \"{params['text']}\" at ({params['x']}, {params['y']})"
        elif action.action == "long_click_element":
            return f"Long click on element \"{params['text']}\" at ({params['x']}, {params['y']})"
        elif action.action == "type_element":
            if params.get('sensitive'):
                return f"Type sensitive input (env var: {params.get('var_name', 'SENSITIVE_INPUT')}) on element \"{params['element_text']}\" at ({params['x']}, {params['y']})"
            return f"Type \"{params['input_text']}\" on element \"{params['element_text']}\" at ({params['x']}, {params['y']})"
        elif action.action == "launch_app":
            return f"Launch app {params['package']}"
        elif action.action == "kill_app":
            return f"Force stop app {params['package']}"
        elif action.action == "clear_app_data":
            return f"Clear all data for app {params['package']}"
        elif action.action == "wait_for_condition":
            conditions = []
            if params.get("element_text"):
                conditions.append('element "' + params["element_text"] + '" to appear')
            if params.get("element_gone"):
                conditions.append('element "' + params["element_gone"] + '" to disappear')
            if params.get("activity_name"):
                conditions.append('activity "' + params["activity_name"] + '" to load')
            desc = ', '.join(conditions) if conditions else 'condition'
            result = params.get("result", "unknown")
            elapsed = params.get("elapsed", "?")
            return f"Wait for {desc} (result: {result}, took {elapsed}s)"
        elif action.action == "notification":
            return "Open notification bar"
        elif action.action == "wait":
            return f"Wait for {params['duration']} seconds"
        else:
            return f"{action.action.capitalize()}: {params}"
