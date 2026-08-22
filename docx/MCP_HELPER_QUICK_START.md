# MCP Helper - Quick Start Guide

## Installation

MCP Helper is already integrated into Android-MCP. Just ensure the MCP Helper app is installed on your device:

```bash
# Check if installed
adb shell pm list packages | grep portal

# Expected output:
# package:io.github.hadyahmed00.portal
```

## Using with Android-MCP

### Default Behavior (Automatic MCP Helper)

```python
from src.mobile import Mobile

# MCP Helper enabled by default
mobile = Mobile(device="emulator-5554")
state = mobile.get_state()
```

MCP Helper will be used automatically. If unavailable, falls back to UIAutomator.

### Force UIAutomator (Disable MCP Helper)

```python
mobile = Mobile(device="emulator-5554", use_mcp_helper=False)
state = mobile.get_state()
```

## Direct Usage Examples

### Get Current App

```python
from src.mcp_helper import MCPHelperClient

client = MCPHelperClient()
state = client.get_phone_state()
print(f"Current app: {state.packageName}")
print(f"Keyboard visible: {state.keyboardVisible}")
```

### Get UI Elements

```python
client = MCPHelperClient()
tree = client.get_a11y_tree()

for node in tree:
    print(f"Button: {node.text} at {node.bounds}")
```

### Send Keyboard Input

```python
client = MCPHelperClient()
client.keyboard_input("username")
client.keyboard_key(66)  # Press Enter
```

### Get Installed Apps

```python
client = MCPHelperClient()
apps = client.get_packages()

user_apps = [app for app in apps if not app.isSystemApp]
for app in user_apps:
    print(f"{app.label} - {app.packageName}")
```

## Common Commands

### Check Connection
```python
from src.mcp_helper import MCPHelperClient
client = MCPHelperClient()
assert client.ping(), "MCP Helper not responding"
print(f"MCP Helper v{client.get_version()}")
```

### Get Tree and Take Screenshot
```python
from src.mobile import Mobile

mobile = Mobile()
state = mobile.get_state(use_vision=True)

if state.screenshot:
    with open("screenshot.png", "wb") as f:
        f.write(state.screenshot)

print(f"Elements: {len(state.tree_state.interactive_elements)}")
```

### Type Text and Press Key
```python
from src.mcp_helper import MCPHelperClient

client = MCPHelperClient()
client.keyboard_input("test@example.com", clear=True)  # Clears field first
client.keyboard_input("password", clear=False)  # Appends to existing text
client.keyboard_key(66)  # Press Enter
```

### Navigate App
```python
from src.mobile import Mobile

mobile = Mobile()

# Get state
state = mobile.get_state()

# Find elements
for elem in state.tree_state.interactive_elements:
    if "Login" in elem.name:
        x, y = elem.coordinates.x, elem.coordinates.y
        mobile.get_device().click(x, y)
        break
```

## Response Examples

### Phone State
```json
{
  "packageName": "com.example.app",
  "activityName": ".LoginActivity",
  "keyboardVisible": false,
  "isEditable": false,
  "focusedElement": {"resourceId": "com.example.app:id/username"}
}
```

### Tree Node
```json
{
  "index": 5,
  "resourceId": "com.example.app:id/login_button",
  "className": "android.widget.Button",
  "text": "Login",
  "bounds": "100, 200, 300, 250",
  "children": []
}
```

### App Info
```json
{
  "packageName": "com.example.app",
  "label": "Example App",
  "versionName": "1.0.0",
  "versionCode": 1,
  "isSystemApp": false
}
```

## Keyboard Key Codes

Common Android key codes for `keyboard_key()`:

| Key | Code | Usage |
|-----|------|-------|
| Back | 4 | `client.keyboard_key(4)` |
| Home | 3 | `client.keyboard_key(3)` |
| Enter | 66 | `client.keyboard_key(66)` |
| Backspace | 67 | `client.keyboard_key(67)` |
| Tab | 27 | `client.keyboard_key(27)` |
| Escape | 111 | `client.keyboard_key(111)` |

## Troubleshooting

### Check if MCP Helper is running
```bash
adb shell dumpsys activity services | grep portal
```

### Test connection
```python
from src.mcp_helper import MCPHelperClient
client = MCPHelperClient()
print(client.ping())  # Should print True
```

### Get version
```python
from src.mcp_helper import MCPHelperClient
client = MCPHelperClient()
print(f"Version: {client.get_version()}")  # e.g., "0.4.8"
```

### Manual ADB query (debug)
```bash
# Query phone state directly
adb shell content query --uri content://io.github.hadyahmed00.portal/phone_state

# Query accessibility tree
adb shell content query --uri content://io.github.hadyahmed00.portal/a11y_tree

# Get installed apps
adb shell content query --uri content://io.github.hadyahmed00.portal/packages
```

## Performance Tips

1. **Reuse client**: Create once, use multiple times
   ```python
   client = MCPHelperClient()  # Create once
   state1 = client.get_phone_state()
   state2 = client.get_phone_state()
   ```

2. **Use caching**: Queries are cached for 0.5 seconds
   ```python
   state = mobile.get_state()  # Cached
   time.sleep(0.2)
   state = mobile.get_state()  # From cache
   time.sleep(0.5)
   state = mobile.get_state()  # Fresh query
   ```

3. **Avoid vision mode**: Screenshots are slower
   ```python
   state = mobile.get_state(use_vision=False)  # Fast
   state = mobile.get_state(use_vision=True)   # Slower
   ```

4. **Use filter parameter**: Reduce tree size
   ```python
   tree = client.get_a11y_tree_full(include_small=False)  # Filtered
   tree = client.get_a11y_tree_full(include_small=True)   # Full
   ```

## Integration with MCP Server

In `main.py`, MCP Helper is automatically used:

```python
mobile = Mobile(device=None if not args.emulator else 'emulator-5554')

@mcp.tool('State-Tool')
def state_tool(use_vision: bool = False):
    # Automatically uses MCP Helper if available
    mobile_state = mobile.get_state(use_vision=use_vision)
    return [mobile_state.tree_state.to_string()] + ...
```

## See Also

- [MCP Helper Full Documentation](./MCP_HELPER_INTEGRATION.md)
- [Android-MCP README](./README.md)
- [Test Suite](./test_mcp_helper_integration.py)
