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

    def export_as_python(self, filename: str = None, test_name: str = None) -> str:
        """Export recorded actions as executable Python test script."""
        if not filename:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_{timestamp}.py"

        if not test_name:
            test_name = filename.replace(".py", "")

        filepath = Path(filename)

        # Generate Python script content
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
                if time_diff > 0.5:  # Add delay if there was a significant gap
                    wait_before = f"    time.sleep({time_diff:.1f})\n"

            script_lines.append(wait_before)
            script_lines.append(self._generate_action_code(action, i))

        script_lines.extend([
            '',
            'if __name__ == "__main__":',
            '    run_test()',
        ])

        script_content = '\n'.join(script_lines)

        with open(filepath, 'w') as f:
            f.write(script_content)

        return str(filepath)

    def _generate_action_code(self, action: TestAction, action_num: int) -> str:
        """Generate Python code for a single action."""
        params = action.parameters
        indent = "    "

        if action.action == "click":
            return f'{indent}# Action {action_num}: Click at ({params["x"]}, {params["y"]})\n{indent}device.click({params["x"]}, {params["y"]})'

        elif action.action == "long_click":
            return f'{indent}# Action {action_num}: Long click at ({params["x"]}, {params["y"]})\n{indent}device.long_click({params["x"]}, {params["y"]})'

        elif action.action == "swipe":
            return f'{indent}# Action {action_num}: Swipe from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})\n{indent}device.swipe({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

        elif action.action == "type":
            text = params["text"].replace('"', '\\"')
            return f'{indent}# Action {action_num}: Type "{text}"\n{indent}device.send_keys("{text}")'

        elif action.action == "drag":
            return f'{indent}# Action {action_num}: Drag from ({params["x1"]}, {params["y1"]}) to ({params["x2"]}, {params["y2"]})\n{indent}device.drag({params["x1"]}, {params["y1"]}, {params["x2"]}, {params["y2"]})'

        elif action.action == "press":
            button = params["button"]
            return f'{indent}# Action {action_num}: Press {button} button\n{indent}device.press("{button}")'

        elif action.action == "notification":
            return f'{indent}# Action {action_num}: Open notification bar\n{indent}device.open_notification()'

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
            return f"Type text: \"{params['text']}\""
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
