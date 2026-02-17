import sys
import os
import warnings
import subprocess
import time
import shlex

# Suppress warnings and stderr output that can interfere with MCP protocol
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Redirect stderr to devnull to prevent library warnings from breaking MCP
import io
_original_stderr = sys.stderr
sys.stderr = io.StringIO()

from mcp.server.fastmcp import FastMCP,Image
from argparse import ArgumentParser
from src.mobile import Mobile
from src.recorder import TestRecorder
from textwrap import dedent

# Restore stderr after imports (optional, but can help with debugging)
# sys.stderr = _original_stderr

parser = ArgumentParser()
parser.add_argument('--emulator',action='store_true',help='Use the emulator')
parser.add_argument('--device',type=str,default=None,help='Specific device ID (e.g., b44fbcc9 or emulator-5554)')
args = parser.parse_args()

instructions=dedent('''
Android MCP server provides tools to interact directly with the Android device,
thus enabling to operate the mobile device like an actual USER.
It also includes test recording capabilities to capture and export test scripts.''')

mcp=FastMCP(name="Android-MCP",instructions=instructions)

# Determine device: explicit device > emulator flag > auto-detect
device_id = args.device
if device_id is None:
    if args.emulator:
        device_id = 'emulator-5554'  
    # else: None means auto-detect (uiautomator2 will find default device)

mobile=Mobile(device=device_id, use_mcp_helper=True)
recorder=TestRecorder()

# Helper function to execute ADB commands without using uiautomator2's accessibility service
def adb_shell(command: str) -> str:
    """Execute ADB shell command using the configured device."""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", command])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"ADB command failed: {result.stderr}")
    return result.stdout.strip()

@mcp.tool(name='Click-Tool',description='Click on a specific cordinate')
def click_tool(x:int,y:int):
    # Use ADB input tap instead of uiautomator2 to avoid accessibility service conflict
    adb_shell(f"input tap {x} {y}")
    recorder.record_action('click', {'x': x, 'y': y}, result=f'Clicked on ({x},{y})')
    return f'Clicked on ({x},{y})'

@mcp.tool('State-Tool',description='Get the state of the device. Optionally includes visual screenshot when use_vision=True.')
def state_tool(use_vision:bool=False):
    mobile_state=mobile.get_state(use_vision=use_vision)
    return [mobile_state.tree_state.to_string()]+([Image(data=mobile_state.screenshot,format='PNG')] if use_vision else [])

@mcp.tool(name='Long-Click-Tool',description='Long click on a specific cordinate')
def long_click_tool(x:int,y:int):
    # Use ADB input swipe with long duration to simulate long click
    adb_shell(f"input swipe {x} {y} {x} {y} 1000")
    recorder.record_action('long_click', {'x': x, 'y': y}, result=f'Long Clicked on ({x},{y})')
    return f'Long Clicked on ({x},{y})'

@mcp.tool(name='Swipe-Tool',description='Swipe on a specific cordinate')
def swipe_tool(x1:int,y1:int,x2:int,y2:int):
    # Use ADB input swipe
    adb_shell(f"input swipe {x1} {y1} {x2} {y2} 300")
    recorder.record_action('swipe', {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}, result=f'Swiped from ({x1},{y1}) to ({x2},{y2})')
    return f'Swiped from ({x1},{y1}) to ({x2},{y2})'

@mcp.tool(name='Type-Tool',description='Type on a specific cordinate')
def type_tool(text:str,x:int,y:int,clear:bool=False):
    # First click on the coordinates to focus the input field
    adb_shell(f"input tap {x} {y}")
    # Use ADB input text for typing (simpler and doesn't require IME setup)
    # Note: Special characters may need escaping
    escaped_text = text.replace(' ', '%s').replace("'", "\\'")
    adb_shell(f"input text '{escaped_text}'")
    recorder.record_action('type', {'text': text, 'x': x, 'y': y, 'clear': clear}, result=f'Typed "{text}" on ({x},{y})')
    return f'Typed "{text}" on ({x},{y})'

@mcp.tool(name='Drag-Tool',description='Drag from location and drop on another location')
def drag_tool(x1:int,y1:int,x2:int,y2:int):
    # Use ADB input swipe with longer duration for drag
    adb_shell(f"input swipe {x1} {y1} {x2} {y2} 500")
    recorder.record_action('drag', {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}, result=f'Dragged from ({x1},{y1}) and dropped on ({x2},{y2})')
    return f'Dragged from ({x1},{y1}) and dropped on ({x2},{y2})'

@mcp.tool(name='Press-Tool',description='Press on specific button on the device')
def press_tool(button:str):
    # Map button names to Android keycodes
    keycode_map = {
        'home': 'KEYCODE_HOME',
        'back': 'KEYCODE_BACK',
        'menu': 'KEYCODE_MENU',
        'power': 'KEYCODE_POWER',
        'volume_up': 'KEYCODE_VOLUME_UP',
        'volume_down': 'KEYCODE_VOLUME_DOWN',
        'enter': 'KEYCODE_ENTER',
        'delete': 'KEYCODE_DEL',
    }
    keycode = keycode_map.get(button.lower(), button)
    adb_shell(f"input keyevent {keycode}")
    recorder.record_action('press', {'button': button}, result=f'Pressed the "{button}" button')
    return f'Pressed the "{button}" button'

@mcp.tool(name='Notification-Tool',description='Access the notifications seen on the device')
def notification_tool():
    # Open notification panel by swiping down from top or using service call
    adb_shell("cmd statusbar expand-notifications")
    recorder.record_action('notification', {}, result='Accessed notification bar')
    return 'Accessed notification bar'

@mcp.tool(name='Wait-Tool',description='Wait for a specific amount of time')
def wait_tool(duration:int):
    # Use Python's time.sleep instead of uiautomator2 to avoid accessibility service conflict
    time.sleep(duration)
    recorder.record_action('wait', {'duration': duration}, result=f'Waited for {duration} seconds')
    return f'Waited for {duration} seconds'

@mcp.tool(name='Start-Recording-Tool',description='Start recording test actions')
def start_recording_tool():
    recorder.start()
    return 'Test recording started. All subsequent actions will be recorded.'

@mcp.tool(name='Stop-Recording-Tool',description='Stop recording test actions')
def stop_recording_tool():
    recorder.stop()
    return f'Test recording stopped. {len(recorder.get_actions())} actions recorded.'

@mcp.tool(name='Export-Test-Script',description='Export recorded test actions as executable test script. Supported formats: python, json, readable')
def export_test_script(format:str='python',filename:str=None,test_name:str=None)->str:
    """
    Export recorded test actions.

    Parameters:
    - format: 'python' (executable Python script), 'json' (JSON data), 'readable' (human-readable steps)
    - filename: Optional custom filename (without extension)
    - test_name: Optional custom test name for Python exports
    """
    try:
        if not recorder.get_actions():
            return 'No actions recorded. Start recording with Start-Recording-Tool first.'

        format = format.lower().strip()

        if format == 'python':
            filepath = recorder.export_as_python(filename=filename, test_name=test_name)
            return f'Test script exported as Python: {filepath}\n\nYou can now run this script directly with: python {filepath}'

        elif format == 'json':
            filepath = recorder.export_as_json(filename=filename)
            return f'Test data exported as JSON: {filepath}'

        elif format == 'readable':
            filepath = recorder.export_as_readable(filename=filename)
            return f'Test steps exported as readable format: {filepath}'

        else:
            return f'Unknown format: {format}. Supported formats: python, json, readable'

    except Exception as e:
        return f'Error exporting test script: {str(e)}'

@mcp.tool(name='Clear-Recording-Tool',description='Clear all recorded test actions')
def clear_recording_tool():
    count = len(recorder.get_actions())
    recorder.clear()
    return f'Cleared {count} recorded actions.'

@mcp.tool(name='Get-Recording-Stats-Tool',description='Get statistics about recorded test actions')
def get_recording_stats_tool():
    actions = recorder.get_actions()
    if not actions:
        return 'No actions recorded yet.'

    action_types = {}
    for action in actions:
        action_types[action.action] = action_types.get(action.action, 0) + 1

    total_duration = actions[-1].timestamp if actions else 0

    stats = f'Recording Statistics:\n'
    stats += f'- Total actions: {len(actions)}\n'
    stats += f'- Duration: {total_duration:.2f} seconds\n'
    stats += f'- Recording status: {"Active" if recorder.is_recording else "Inactive"}\n'
    stats += f'\nAction breakdown:\n'
    for action_type, count in sorted(action_types.items()):
        stats += f'  - {action_type}: {count}\n'

    return stats

@mcp.tool(name='Report-Bug-To-Azure',description='Report a bug to Azure DevOps using Azure CLI with proper bug report structure (generates command to run)')
def report_bug_to_azure_command(
    title: str,
    steps_to_reproduce: str,
    expected_result: str,
    actual_result: str,
    description: str = "",
    project: str = None,
    parent_user_story: str = None,
    severity: str = "3 - Medium",
    priority: int = 2,
    environment: str = None
):
    """
    Generate Azure CLI command to report a bug (for manual execution).
    This avoids subprocess hanging issues.
    """
    # Auto-detect device environment if not provided
    if not environment:
        try:
            device_info = mobile.get_device().device_info
            environment = f"Device: {device_info.get('brand', 'Unknown')} {device_info.get('model', 'Unknown')}\n"
            environment += f"OS Version: Android {device_info.get('version', 'Unknown')}\n"
            environment += f"SDK: {device_info.get('sdk', 'Unknown')}"
        except:
            environment = "Device info not available"

    # Build the Description or Steps field (Custom.DescriptionorSteps)
    description_steps = ""
    if description:
        description_steps += f"<p>{description}</p>"
    description_steps += f"<p><strong>Steps to Reproduce:</strong></p>"
    description_steps += f"<ol>"
    for step in steps_to_reproduce.split("\n"):
        step = step.strip()
        if step:
            # Remove leading number/dot/dash if present
            import re
            step_text = re.sub(r'^[\d]+[\.\)\-\s]+', '', step).strip()
            if step_text:
                description_steps += f"<li>{step_text}</li>"
    description_steps += f"</ol>"
    if environment:
        description_steps += f"<p><strong>Environment:</strong> {environment}</p>"

    # Build the command string
    cmd = f'az boards work-item create --type Bug --title "{title}"'

    if project:
        cmd += f' --project "{project}"'

    # Wrap actual_result and expected_result in HTML for proper rendering
    actual_result_html = f'<div><span style="display:inline !important;">{actual_result}</span><br> </div>'
    expected_result_html = f'<div><span style="display:inline !important;">{expected_result}</span><br> </div>'

    cmd += f' --fields "Custom.DescriptionorSteps={description_steps}"'
    cmd += f' "Microsoft.VSTS.TCM.ReproSteps={actual_result_html}"'
    cmd += f' "Microsoft.VSTS.TCM.SystemInfo={expected_result_html}"'
    cmd += f' "Microsoft.VSTS.Common.Severity={severity}"'
    cmd += f' "Microsoft.VSTS.Common.Priority={priority}"'
    if parent_user_story:
        cmd += f' "System.Parent={parent_user_story}"'

    result = f"""
📋 Bug Report Ready!

**Title:** {title}
**Severity:** {severity}
**Priority:** {priority}
**Project:** {project or "Default"}
**Parent Story:** #{parent_user_story if parent_user_story else "None"}

🔧 **Run this command in your terminal:**

```bash
{cmd}
```
"""
    return result

@mcp.tool(name='Report-Bug-To-Azure-Direct',description='[EXPERIMENTAL] Report a bug to Azure DevOps - direct execution (may hang)')
def report_bug_to_azure(
    title: str,
    steps_to_reproduce: str,
    expected_result: str,
    actual_result: str,
    description: str = "",
    project: str = None,
    parent_user_story: str = None,
    severity: str = "3 - Medium",
    priority: int = 2,
    environment: str = None
):
    """
    Report a bug to Azure DevOps using Azure CLI with proper bug report structure.

    Parameters:
    - title: Bug title (required) - Short, clear description of the issue
    - steps_to_reproduce: Clear steps to replicate the bug (required)
    - expected_result: What should happen (required)
    - actual_result: What actually happened (required)
    - description: Additional context or details (optional)
    - project: Azure DevOps project name (optional, uses default if not specified)
    - parent_user_story: Parent user story ID to link this bug to (optional)
    - severity: Bug severity (default: "3 - Medium")
    - priority: Bug priority 1-4 (default: 2)
    - environment: Device/OS/App version info (optional)
    """
    try:
        # First, test if Azure CLI is accessible
        try:
            test_result = subprocess.run("az --version", capture_output=True, text=True, timeout=5, shell=True)
            if test_result.returncode != 0:
                return "❌ Error: Azure CLI is not responding. Please ensure it's properly installed and configured."
        except subprocess.TimeoutExpired:
            return "❌ Error: Azure CLI is not responding (timeout). Please check your Azure CLI installation."
        except Exception as e:
            return f"❌ Error: Cannot access Azure CLI: {str(e)}"

        # Auto-detect device environment if not provided
        if not environment:
            try:
                # Get device info from mobile instance
                device_info = mobile.get_device().device_info
                environment = f"Device: {device_info.get('brand', 'Unknown')} {device_info.get('model', 'Unknown')}\n"
                environment += f"OS Version: Android {device_info.get('version', 'Unknown')}\n"
                environment += f"SDK: {device_info.get('sdk', 'Unknown')}"
            except:
                environment = "Device info not available"

        # Build the Description or Steps field as HTML (Custom.DescriptionorSteps)
        import re
        description_steps = ""
        if description:
            description_steps += f"<p>{description}</p>"
        description_steps += "<p><strong>Steps to Reproduce:</strong></p><ol>"
        for step in steps_to_reproduce.split("\n"):
            step = step.strip()
            if step:
                step_text = re.sub(r'^[\d]+[\.\)\-\s]+', '', step).strip()
                if step_text:
                    description_steps += f"<li>{step_text}</li>"
        description_steps += "</ol>"
        if environment:
            description_steps += f"<p><strong>Environment:</strong> {environment}</p>"

        # Build the Azure CLI command
        cmd = ["az", "boards", "work-item", "create", "--type", "Bug"]

        # Add title
        cmd.extend(["--title", title])

        # Add project if specified
        if project:
            cmd.extend(["--project", project])

        # Wrap actual_result and expected_result in HTML for proper rendering
        actual_result_html = f"<div><span style=\"display:inline !important;\">{actual_result}</span><br> </div>"
        expected_result_html = f"<div><span style=\"display:inline !important;\">{expected_result}</span><br> </div>"

        # Use the correct Azure DevOps fields matching the board layout
        fields = [
            f"Custom.DescriptionorSteps={description_steps}",
            f"Microsoft.VSTS.TCM.ReproSteps={actual_result_html}",
            f"Microsoft.VSTS.TCM.SystemInfo={expected_result_html}",
            f"Microsoft.VSTS.Common.Severity={severity}",
            f"Microsoft.VSTS.Common.Priority={priority}"
        ]

        # Add parent user story if specified
        if parent_user_story:
            fields.append(f"System.Parent={parent_user_story}")

        # Add all fields
        for field in fields:
            cmd.extend(["--fields", field])

        # Add output format and suppress warnings
        cmd.extend(["--output", "json", "--only-show-errors"])

        # Execute the command (shell=True for Windows compatibility)
        # Properly quote arguments for shell execution
        try:
            cmd_string = shlex.join(cmd)  # Python 3.8+
        except AttributeError:
            # Fallback for older Python versions
            cmd_string = " ".join(shlex.quote(arg) for arg in cmd)

        # Reduced timeout to 15 seconds to avoid long waits
        result = subprocess.run(cmd_string, capture_output=True, text=True, timeout=15, shell=True)

        if result.returncode != 0:
            error_msg = result.stderr.strip()

            # Check for common errors and provide helpful messages
            if "not logged in" in error_msg.lower() or "authentication" in error_msg.lower():
                return "❌ Error: Not logged in to Azure. Please run 'az login' first."
            elif "project" in error_msg.lower() and "not found" in error_msg.lower():
                return f"❌ Error: Project '{project}' not found. Please specify a valid project name or use the default project."
            elif "az boards" in error_msg:
                return "❌ Error: Azure DevOps extension not found. Please install it with: az extension add --name azure-devops"
            else:
                return f"❌ Error creating bug in Azure DevOps:\n{error_msg}"

        # Parse the response
        import json
        response = json.loads(result.stdout)
        bug_id = response.get("id", "Unknown")
        bug_url = response.get("url", "")

        success_msg = f"✅ Bug reported successfully to Azure DevOps!\n\n"
        success_msg += f"📋 Bug ID: #{bug_id}\n"
        success_msg += f"📝 Title: {title}\n"
        success_msg += f"⚠️ Severity: {severity} | Priority: {priority}\n"
        if project:
            success_msg += f"🗂️ Project: {project}\n"
        if parent_user_story:
            success_msg += f"🔗 Linked to User Story: #{parent_user_story}\n"
        success_msg += f"\n📊 Bug Report Structure:\n"
        success_msg += f"   ✓ Steps to Reproduce\n"
        success_msg += f"   ✓ Expected Result\n"
        success_msg += f"   ✓ Actual Result\n"
        success_msg += f"   ✓ Environment Info\n"
        if bug_url:
            success_msg += f"\n🔗 View in Azure DevOps: {bug_url}\n"

        return success_msg

    except FileNotFoundError:
        return "❌ Error: Azure CLI not found. Please install Azure CLI first: https://aka.ms/installazurecliwindows"
    except subprocess.TimeoutExpired:
        return "❌ Error: Command timed out after 15 seconds. This might be due to:\n  - Network connectivity issues\n  - Azure CLI waiting for authentication\n  - Large project size\nPlease check 'az login' status and try again."
    except json.JSONDecodeError:
        return f"❌ Error: Failed to parse Azure CLI response. Output:\n{result.stdout}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

if __name__ == '__main__':
    mcp.run()
    #print the server have started and print alos the currnt working device
    print('Server started on ' + mcp.get_url())
    print('Current working device:', mobile.get_device().device_info)