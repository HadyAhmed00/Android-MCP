import sys
import os
import warnings
import subprocess
import time
import shlex
import re

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
_sensitive_counter = 0

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

def _find_element(text, index=0):
    """Find an interactive element by name/text on the current screen.
    Returns a tuple of (element, error_message).
    If element is found, error_message is None.
    If element is not found, element is None and error_message describes the problem.
    Matches against both real names and scrubbed names so agents using
    scrubbed text from State-Tool can still find elements.
    """
    mobile_state = mobile.get_state()
    elements = mobile_state.tree_state.interactive_elements

    # Build unique scrub mapping for collision-safe matching
    all_names = [e.name for e in elements]
    scrub_map = _scrub_pii_unique(all_names)

    matches = []
    for element in elements:
        # Match against real name (normal case)
        if text.lower() in element.name.lower():
            matches.append(element)
        # Also match against unique scrubbed name (when agent uses scrubbed text from State-Tool)
        elif text.lower() in scrub_map.get(element.name, '').lower():
            matches.append(element)

    if not matches:
        # Scrub available element names in error response to avoid leaking PII
        available_names = []
        for element in elements[:20]:
            available_names.append('"' + scrub_map.get(element.name, element.name) + '"')
        available_str = ', '.join(available_names)
        return None, 'Element "' + text + '" not found. Available elements: ' + available_str

    if index >= len(matches):
        return None, 'Index ' + str(index) + ' out of range. Found ' + str(len(matches)) + ' matches for "' + text + '".'

    return matches[index], None

def _mask_email(local, domain, reveal=None):
    """Mask an email local part, keeping 'reveal' chars from start + last char.
    Default reveal scales with local length to always mask at least 1 char.
    If reveal >= len(local)-1, returns full local (no masking possible)."""
    if len(local) <= 2:
        return local[0] + '*@' + domain
    if reveal is None:
        # Default: reveal roughly half, minimum 1, always leave room for at least 1 star
        reveal = min(3, len(local) - 2)
    if reveal >= len(local) - 1:
        # Can't mask anymore, return full local
        return local + '@' + domain
    masked_count = len(local) - reveal - 1
    return local[:reveal] + '*' * masked_count + local[-1] + '@' + domain

def _mask_phone(digits, reveal=4):
    """Mask a phone number, keeping last 'reveal' digits."""
    if len(digits) <= reveal:
        return digits
    return '***-***-' + digits[-reveal:]

def _mask_card(digits, reveal_start=4, reveal_end=4):
    """Mask a credit card, keeping first reveal_start and last reveal_end digits."""
    if len(digits) <= reveal_start + reveal_end:
        return digits
    return digits[:reveal_start] + '-****-' + digits[-reveal_end:]

def _scrub_pii(text):
    """Scrub sensitive patterns from text before sending to MCP response.
    Masks emails, phone numbers, and credit card-like numbers.
    Only used on outward-facing strings, not internal element data."""
    # Email: keep first 3 chars + last char before @ + domain
    def _email_replacer(m):
        local = m.group(0).split('@')[0]
        domain = m.group(1)
        return _mask_email(local, domain)
    text = re.sub(
        r'[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        _email_replacer,
        text
    )
    # Credit card-like: 13-19 digit sequences (with optional spaces/dashes)
    def _card_replacer(m):
        digits = re.sub(r'[\s-]', '', m.group(0))
        if len(digits) < 8:
            return m.group(0)
        return _mask_card(digits)
    text = re.sub(
        r'\b(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})[\s-]?(\d{1,7})\b',
        _card_replacer,
        text
    )
    # Phone numbers: keep last 4 digits
    def _phone_replacer(m):
        digits = re.sub(r'[^\d]', '', m.group(0))
        if len(digits) < 4:
            return m.group(0)
        return _mask_phone(digits)
    text = re.sub(
        r'(?<!\d)(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)',
        _phone_replacer,
        text
    )
    return text

def _scrub_pii_unique(names):
    """Scrub a list of element names and resolve any collisions by revealing
    more characters until each scrubbed name is unique.
    Returns a dict mapping original name -> unique scrubbed name."""
    result = {}
    # First pass: standard scrub
    for name in names:
        result[name] = _scrub_pii(name)

    # Find collisions and resolve them by revealing more characters
    # Group names by their scrubbed output
    for _attempt in range(5):  # max 5 rounds of collision resolution
        scrubbed_groups = {}
        for original, scrubbed in result.items():
            if scrubbed not in scrubbed_groups:
                scrubbed_groups[scrubbed] = []
            scrubbed_groups[scrubbed].append(original)

        has_collision = False
        for scrubbed, originals in scrubbed_groups.items():
            if len(originals) <= 1:
                continue
            has_collision = True
            # Resolve by revealing one more character for each pattern
            for original in originals:
                current = result[original]
                # Try revealing more chars in emails
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', original)
                if email_match:
                    local = original[email_match.start():email_match.end()].split('@')[0]
                    domain = email_match.group(1)
                    # Find current reveal level by counting leading non-* chars before the first *
                    current_local = current[current.find(local[0]):current.find('@')]
                    star_pos = current_local.find('*')
                    if star_pos == -1:
                        # Fully revealed already, can't unmask further
                        continue
                    current_reveal = star_pos
                    result[original] = re.sub(
                        r'[a-zA-Z0-9*._%-]+@' + re.escape(domain),
                        _mask_email(local, domain, reveal=current_reveal + 1),
                        current
                    )
                    continue
                # Try revealing more digits in phone numbers
                phone_match = re.search(r'(?<!\d)(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)', original)
                if phone_match:
                    digits = re.sub(r'[^\d]', '', phone_match.group(0))
                    current_phone = re.search(r'\*{3}-\*{3}-(\d+)', current)
                    current_reveal = len(current_phone.group(1)) if current_phone else 4
                    result[original] = current.replace(
                        '***-***-' + digits[-current_reveal:],
                        _mask_phone(digits, reveal=min(current_reveal + 2, len(digits)))
                    )
                    continue

        if not has_collision:
            break

    return result

@mcp.tool(name='Click-Tool',description='Click on a specific cordinate')
def click_tool(x:int,y:int):
    # Use ADB input tap instead of uiautomator2 to avoid accessibility service conflict
    adb_shell(f"input tap {x} {y}")
    recorder.record_action('click', {'x': x, 'y': y}, result=f'Clicked on ({x},{y})')
    return f'Clicked on ({x},{y})'

@mcp.tool(name='Click-Element-Tool',description='Click on an element by its name or text instead of coordinates. Finds the element on screen and clicks its center. Use index parameter when multiple elements share the same name.')
def click_element_tool(text:str,index:int=0):
    element, error = _find_element(text, index)
    if error:
        return error
    x = element.coordinates.x
    y = element.coordinates.y
    adb_shell(f"input tap {x} {y}")
    scrubbed_name = _scrub_pii(element.name)
    recorder.record_action('click_element', {'text': text, 'index': index, 'x': x, 'y': y}, result=f'Clicked on element "{scrubbed_name}" at ({x},{y})')
    return f'Clicked on element "{scrubbed_name}" at ({x},{y})'

@mcp.tool(name='Long-Click-Element-Tool',description='Long click on an element by its name or text instead of coordinates. Finds the element on screen and long clicks its center. Use index parameter when multiple elements share the same name.')
def long_click_element_tool(text:str,index:int=0):
    element, error = _find_element(text, index)
    if error:
        return error
    x = element.coordinates.x
    y = element.coordinates.y
    adb_shell(f"input swipe {x} {y} {x} {y} 1000")
    scrubbed_name = _scrub_pii(element.name)
    recorder.record_action('long_click_element', {'text': text, 'index': index, 'x': x, 'y': y}, result=f'Long Clicked on element "{scrubbed_name}" at ({x},{y})')
    return f'Long Clicked on element "{scrubbed_name}" at ({x},{y})'

@mcp.tool(name='Type-Element-Tool',description='Find an input field by its name or text, tap it to focus, and type text into it. Set sensitive=True for passwords or private data to prevent the typed text from appearing in responses. Use index parameter when multiple elements share the same name.')
def type_element_tool(input_text:str,element_text:str,index:int=0,sensitive:bool=False):
    element, error = _find_element(element_text, index)
    if error:
        return error
    x = element.coordinates.x
    y = element.coordinates.y
    adb_shell(f"input tap {x} {y}")
    escaped_text = input_text.replace(' ', '%s').replace("'", "\\'")
    adb_shell(f"input text '{escaped_text}'")
    display_text = '****' if sensitive else input_text
    global _sensitive_counter
    if sensitive:
        _sensitive_counter += 1
    var_name = element_text.upper().replace(' ', '_') + '_INPUT_' + str(_sensitive_counter) if sensitive else None
    scrubbed_name = _scrub_pii(element.name)
    recorder.record_action('type_element', {'input_text': display_text, 'element_text': element_text, 'index': index, 'x': x, 'y': y, 'sensitive': sensitive, 'var_name': var_name}, result=f'Typed "{display_text}" on element "{scrubbed_name}" at ({x},{y})')
    return f'Typed "{display_text}" on element "{scrubbed_name}" at ({x},{y})'

@mcp.tool('State-Tool',description='Get the state of the device. Optionally includes visual screenshot when use_vision=True.')
def state_tool(use_vision:bool=False):
    mobile_state=mobile.get_state(use_vision=use_vision)
    # Get phone state metadata for agent context
    phone_info = ''
    try:
        if mobile.use_mcp_helper and not mobile._mcp_initialized:
            mobile._init_mcp_helper()
        if mobile.use_mcp_helper and mobile.mcp_adapter:
            ps = mobile.mcp_adapter.get_phone_state()
            phone_info = 'App: ' + ps.get('packageName', 'unknown') + ' | Activity: ' + ps.get('activityName', 'unknown') + ' | Keyboard: ' + str(ps.get('keyboardVisible', False)) + '\n'
    except Exception:
        pass
    # Scrub element names with collision resolution for unique identification
    elements = mobile_state.tree_state.interactive_elements
    all_names = [e.name for e in elements]
    scrub_map = _scrub_pii_unique(all_names)
    tree_lines = []
    for index, node in enumerate(elements):
        scrubbed_name = scrub_map.get(node.name, node.name)
        tree_lines.append(f'Label: {index} Name: {scrubbed_name} Coordinates: {node.coordinates.to_string()}')
    tree_output = '\n'.join(tree_lines)
    return [phone_info + tree_output]+([Image(data=mobile_state.screenshot,format='PNG')] if use_vision else [])

@mcp.tool(name='Launch-App-Tool',description='Launch an app by its package name. Opens the app as if the user tapped its icon on the home screen.')
def launch_app_tool(package:str):
    adb_shell(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")
    recorder.record_action('launch_app', {'package': package}, result=f'Launched app {package}')
    return f'Launched app {package}'

@mcp.tool(name='Kill-App-Tool',description='Force stop an app by its package name. Useful for resetting app state or closing a frozen app.')
def kill_app_tool(package:str):
    adb_shell(f"am force-stop {package}")
    recorder.record_action('kill_app', {'package': package}, result=f'Force stopped app {package}')
    return f'Force stopped app {package}'

@mcp.tool(name='Clear-App-Data-Tool',description='Clear all data for an app by its package name. Resets the app to a fresh install state including login, cache, and preferences.')
def clear_app_data_tool(package:str):
    adb_shell(f"pm clear {package}")
    recorder.record_action('clear_app_data', {'package': package}, result=f'Cleared data for app {package}')
    return f'Cleared data for app {package}'

@mcp.tool(name='Get-Current-App-Tool',description='Get the currently active app package name and activity. Useful for verifying navigation or detecting unexpected screens.')
def get_current_app_tool():
    if mobile.use_mcp_helper and not mobile._mcp_initialized:
        mobile._init_mcp_helper()
    if mobile.use_mcp_helper and mobile.mcp_adapter:
        try:
            phone_state = mobile.mcp_adapter.get_phone_state()
            package = phone_state.get('packageName', 'unknown')
            activity = phone_state.get('activityName', 'unknown')
            keyboard = phone_state.get('keyboardVisible', False)
            result = f'Current app: {package}\nCurrent activity: {activity}\nKeyboard visible: {keyboard}'
            return result
        except Exception:
            pass
    # Fallback to ADB
    output = adb_shell("dumpsys activity activities | grep mResumedActivity")
    return f'Current activity: {output}'

@mcp.tool(name='List-Apps-Tool',description='List all installed launchable apps on the device with their package names.')
def list_apps_tool():
    if mobile.use_mcp_helper and not mobile._mcp_initialized:
        mobile._init_mcp_helper()
    if mobile.use_mcp_helper and mobile.mcp_adapter:
        try:
            apps = mobile.mcp_adapter.get_installed_apps()
            lines = []
            for app in apps:
                label = app.get('label', 'Unknown')
                pkg = app.get('packageName', '')
                lines.append(f'{label}: {pkg}')
            return '\n'.join(lines)
        except Exception:
            pass
    # Fallback to ADB
    output = adb_shell("pm list packages -3")
    return output

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

@mcp.tool(name='Type-Tool',description='Type on a specific cordinate. Set sensitive=True for passwords or private data to prevent the typed text from appearing in responses.')
def type_tool(text:str,x:int,y:int,clear:bool=False,sensitive:bool=False):
    # First click on the coordinates to focus the input field
    adb_shell(f"input tap {x} {y}")
    # Use ADB input text for typing (simpler and doesn't require IME setup)
    # Note: Special characters may need escaping
    escaped_text = text.replace(' ', '%s').replace("'", "\\'")
    adb_shell(f"input text '{escaped_text}'")
    display_text = '****' if sensitive else text
    global _sensitive_counter
    if sensitive:
        _sensitive_counter += 1
    var_name = 'SENSITIVE_INPUT_' + str(_sensitive_counter) if sensitive else None
    recorder.record_action('type', {'text': display_text, 'x': x, 'y': y, 'clear': clear, 'sensitive': sensitive, 'var_name': var_name}, result=f'Typed "{display_text}" on ({x},{y})')
    return f'Typed "{display_text}" on ({x},{y})'

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

@mcp.tool(name='Wait-For-Condition-Tool',description='Wait until a specific condition is met on screen. Can wait for an element to appear, disappear, or a specific activity to load. Polls the device state every interval until the condition is met or timeout is reached.')
def wait_for_condition_tool(element_text:str=None,element_gone:str=None,activity_name:str=None,timeout:int=10,interval:float=1.0):
    """
    Wait until a condition is met on the device screen.

    Parameters:
    - element_text: Wait until an element with this text appears on screen
    - element_gone: Wait until an element with this text disappears from screen
    - activity_name: Wait until the device is on this activity
    - timeout: Maximum seconds to wait before giving up (default 10)
    - interval: Seconds between each check (default 1.0)
    """
    if not element_text and not element_gone and not activity_name:
        return 'Error: At least one condition must be specified (element_text, element_gone, or activity_name).'

    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            conditions = []
            if element_text:
                conditions.append('element "' + element_text + '" to appear')
            if element_gone:
                conditions.append('element "' + element_gone + '" to disappear')
            if activity_name:
                conditions.append('activity "' + activity_name + '" to load')
            condition_str = ', '.join(conditions)
            recorder.record_action('wait_for_condition', {'element_text': element_text, 'element_gone': element_gone, 'activity_name': activity_name, 'timeout': timeout, 'result': 'timeout'}, result='Timed out waiting for ' + condition_str)
            return 'Timed out after ' + str(timeout) + ' seconds waiting for ' + condition_str + '.'

        mobile_state = mobile.get_state()
        elements = mobile_state.tree_state.interactive_elements
        element_names = [e.name.lower() for e in elements]

        # Check element_text condition: element should appear
        if element_text:
            found = False
            for name in element_names:
                if element_text.lower() in name:
                    found = True
                    break
            if not found:
                time.sleep(interval)
                continue

        # Check element_gone condition: element should disappear
        if element_gone:
            still_there = False
            for name in element_names:
                if element_gone.lower() in name:
                    still_there = True
                    break
            if still_there:
                time.sleep(interval)
                continue

        # Check activity_name condition via MCP Helper or ADB fallback
        if activity_name:
            activity_matched = False
            if mobile.use_mcp_helper and mobile.mcp_adapter:
                try:
                    phone_state = mobile.mcp_adapter.get_phone_state()
                    current_activity = phone_state.get('activityName', '')
                    if activity_name.lower() in current_activity.lower():
                        activity_matched = True
                except Exception:
                    pass
            if not activity_matched:
                try:
                    output = adb_shell("dumpsys activity activities | grep mResumedActivity")
                    if activity_name.lower() in output.lower():
                        activity_matched = True
                except Exception:
                    pass
            if not activity_matched:
                time.sleep(interval)
                continue

        # All conditions met
        elapsed = round(time.time() - start_time, 1)
        conditions_met = []
        if element_text:
            conditions_met.append('element "' + element_text + '" appeared')
        if element_gone:
            conditions_met.append('element "' + element_gone + '" disappeared')
        if activity_name:
            conditions_met.append('activity "' + activity_name + '" loaded')
        result_str = ', '.join(conditions_met)
        recorder.record_action('wait_for_condition', {'element_text': element_text, 'element_gone': element_gone, 'activity_name': activity_name, 'timeout': timeout, 'elapsed': elapsed, 'result': 'success'}, result='Condition met: ' + result_str + ' after ' + str(elapsed) + 's')
        return 'Condition met after ' + str(elapsed) + ' seconds: ' + result_str + '.'

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