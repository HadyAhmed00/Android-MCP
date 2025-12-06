from mcp.server.fastmcp import FastMCP,Image
from contextlib import asynccontextmanager
from argparse import ArgumentParser
from src.mobile import Mobile
from src.recorder import TestRecorder
from textwrap import dedent
import asyncio

parser = ArgumentParser()
parser.add_argument('--emulator',action='store_true',help='Use the emulator')
args = parser.parse_args()

instructions=dedent('''
Android MCP server provides tools to interact directly with the Android device,
thus enabling to operate the mobile device like an actual USER.
It also includes test recording capabilities to capture and export test scripts.''')

@asynccontextmanager
async def lifespan(app: FastMCP):
    """Runs initialization code before the server starts and cleanup code after it shuts down."""
    await asyncio.sleep(1) # Simulate startup latency
    yield

mcp=FastMCP(name="Android-MCP",instructions=instructions)

mobile=Mobile(device=None if not args.emulator else 'emulator-5554')
device=mobile.get_device()
recorder=TestRecorder()

@mcp.tool(name='Click-Tool',description='Click on a specific cordinate')
def click_tool(x:int,y:int):
    device.click(x,y)
    recorder.record_action('click', {'x': x, 'y': y}, result=f'Clicked on ({x},{y})')
    return f'Clicked on ({x},{y})'

@mcp.tool('State-Tool',description='Get the state of the device. Optionally includes visual screenshot when use_vision=True.')
def state_tool(use_vision:bool=False):
    mobile_state=mobile.get_state(use_vision=use_vision)
    return [mobile_state.tree_state.to_string()]+([Image(data=mobile_state.screenshot,format='PNG')] if use_vision else [])

@mcp.tool(name='Long-Click-Tool',description='Long click on a specific cordinate')
def long_click_tool(x:int,y:int):
    device.long_click(x,y)
    recorder.record_action('long_click', {'x': x, 'y': y}, result=f'Long Clicked on ({x},{y})')
    return f'Long Clicked on ({x},{y})'

@mcp.tool(name='Swipe-Tool',description='Swipe on a specific cordinate')
def swipe_tool(x1:int,y1:int,x2:int,y2:int):
    device.swipe(x1,y1,x2,y2)
    recorder.record_action('swipe', {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}, result=f'Swiped from ({x1},{y1}) to ({x2},{y2})')
    return f'Swiped from ({x1},{y1}) to ({x2},{y2})'

@mcp.tool(name='Type-Tool',description='Type on a specific cordinate')
def type_tool(text:str,x:int,y:int,clear:bool=False):
    device.set_fastinput_ime(enable=True)
    device.send_keys(text=text,clear=clear)
    recorder.record_action('type', {'text': text, 'x': x, 'y': y, 'clear': clear}, result=f'Typed "{text}" on ({x},{y})')
    return f'Typed "{text}" on ({x},{y})'

@mcp.tool(name='Drag-Tool',description='Drag from location and drop on another location')
def drag_tool(x1:int,y1:int,x2:int,y2:int):
    device.drag(x1,y1,x2,y2)
    recorder.record_action('drag', {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}, result=f'Dragged from ({x1},{y1}) and dropped on ({x2},{y2})')
    return f'Dragged from ({x1},{y1}) and dropped on ({x2},{y2})'

@mcp.tool(name='Press-Tool',description='Press on specific button on the device')
def press_tool(button:str):
    device.press(button)
    recorder.record_action('press', {'button': button}, result=f'Pressed the "{button}" button')
    return f'Pressed the "{button}" button'

@mcp.tool(name='Notification-Tool',description='Access the notifications seen on the device')
def notification_tool():
    device.open_notification()
    recorder.record_action('notification', {}, result='Accessed notification bar')
    return 'Accessed notification bar'

@mcp.tool(name='Wait-Tool',description='Wait for a specific amount of time')
def wait_tool(duration:int):
    device.sleep(duration)
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

if __name__ == '__main__':
    mcp.run()