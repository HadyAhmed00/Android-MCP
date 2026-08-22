# MCP Helper Content Provider Integration Guide

## Overview

This document describes the integration of the **MCP Helper Content Provider** with Android-MCP, replacing the slower UIAutomator XML dump approach with a faster, in-process Content Provider interface.

## What is MCP Helper?

**MCP Helper** is a lightweight Android app that exposes a Content Provider API for querying device state. Instead of using UIAutomator's file-based XML dump mechanism (which is slow), MCP Helper provides direct in-process JSON responses.

**Key Benefits:**
- **Faster**: Eliminates file I/O overhead (in-process communication via ADB)
- **JSON Format**: Native structured data (no XML parsing needed)
- **Rich Data**: Direct access to accessibility tree, phone state, installed apps
- **Configurable**: Support for element filtering, overlay configuration, keyboard input
- **Version**: 0.4.8+

## Architecture

### Components

```
┌──────────────────────────────────┐
│     Android-MCP (main.py)        │
│     - State-Tool                 │
│     - Click-Tool, Type-Tool, etc │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│     Mobile class                 │
│  (src/mobile/__init__.py)         │
│  - with MCP Helper support       │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│   MCPHelperMobileAdapter          │
│   (src/mcp_helper_adapter.py)     │
│  - Converts JSON to TreeState    │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│   MCPHelperClient                │
│   (src/mcp_helper.py)            │
│  - ADB communication layer       │
│  - Content Provider interface    │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│   ADB Content Query              │
│  - content query --uri           │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│   MCP Helper App (Android)       │
│   - Content Provider             │
│   - Accessibility API            │
└──────────────────────────────────┘
```

## Files Added

### 1. `src/mcp_helper.py` (Main Client Library)
Contains:
- `MCPHelperClient`: Primary class for communicating with MCP Helper
- `ContentProviderEndpoint`: Enum of available endpoints
- Data classes for type-safe response parsing:
  - `A11yTreeNode`: Simplified accessibility tree node
  - `A11yFullNode`: Complete accessibility node with all properties
  - `PhoneState`: Current device state
  - `AppInfo`: Installed app information
  - `DeviceContext`: Device display metrics

**Key Methods:**
```python
# Query methods (read-only)
ping()                              # Test connection
get_version()                       # Get app version
get_a11y_tree()                    # Get filtered accessibility tree
get_a11y_tree_full(include_small)  # Get full tree with complete info
get_phone_state()                  # Get current app, keyboard, etc.
get_state(include_full_tree)       # Get combined state
get_packages()                     # Get installed apps

# Control methods (write)
keyboard_input(text, clear)        # Send text input
keyboard_clear()                   # Clear focused input
keyboard_key(key_code)             # Send key event
set_overlay_offset(pixels)         # Adjust overlay position
set_overlay_visible(visible)       # Show/hide overlay
set_socket_port(port)              # Configure socket server
```

### 2. `src/mcp_helper_adapter.py` (Adapter Layer)
Converts MCP Helper JSON responses to existing Android-MCP data structures:
- `MCPHelperTreeAdapter`: Converts A11yTreeNode/A11yFullNode to TreeState
- `MCPHelperMobileAdapter`: High-level interface for Mobile class

### 3. Modified `src/mobile/__init__.py`
Updated Mobile class to:
- Accept `use_mcp_helper` parameter (default: True)
- Try MCP Helper first, fallback to UIAutomator
- Initialize MCPHelperClient and MCPHelperMobileAdapter on startup
- Use MCP Helper in get_state() method

### 4. `test_mcp_helper_integration.py` (Test Suite)
Comprehensive test suite covering:
- Direct MCP Helper client functionality
- Adapter layer conversion
- Mobile class integration
- Performance comparison (MCP Helper vs UIAutomator)

## Available Endpoints

### Query Endpoints (Content Query)

#### 1. Ping
```bash
adb shell content query --uri content://io.github.hadyahmed00.portal/ping
```
Returns: `{"status":"success","data":"pong"}`

#### 2. Version
```bash
adb shell content query --uri content://io.github.hadyahmed00.portal/version
```
Returns: `{"status":"success","data":"0.4.8"}`

#### 3. Phone State
```bash
adb shell content query --uri content://io.github.hadyahmed00.portal/phone_state
```
Returns:
```json
{
  "status":"success",
  "data":"{\"packageName\":\"...\",\"activityName\":\"...\",\"keyboardVisible\":false,\"isEditable\":false,\"focusedElement\":{\"resourceId\":\"\"}}"
}
```

#### 4. Accessibility Tree (Simplified)
```bash
adb shell content query --uri content://io.github.hadyahmed00.portal/a11y_tree
```
Returns filtered tree with overlay indices:
```json
{
  "status":"success",
  "data":"[{\"index\":1,\"resourceId\":\"...\",\"className\":\"...\",\"text\":\"...\",\"bounds\":\"0, 0, 1080, 2340\",\"children\":[...]}]"
}
```

#### 5. Accessibility Tree (Full)
```bash
adb shell content query --uri content://io.github.hadyahmed00.portal/a11y_tree_full
adb shell content query --uri 'content://io.github.hadyahmed00.portal/a11y_tree_full?filter=false'
```
Returns complete node info with all properties:
- All boolean attributes (clickable, focusable, enabled, visible, etc.)
- Bounds in screen and parent coordinates
- Actions available on element
- Content description and hints

#### 6. Combined State
```bash
adb shell content query --uri content://io.github.hadyahmed00.portal/state
```
Returns: `{"a11y_tree":[...], "phone_state":{...}}`

#### 7. Combined State (Full)
```bash
adb shell content query --uri content://io.github.hadyahmed00.portal/state_full
adb shell content query --uri 'content://io.github.hadyahmed00.portal/state_full?filter=false'
```
Returns: `{"a11y_tree":{...}, "phone_state":{...}, "device_context":{...}}`

#### 8. Installed Packages
```bash
adb shell content query --uri content://io.github.hadyahmed00.portal/packages
```
Returns list of installed apps with package info

### Control Endpoints (Content Insert)

#### 1. Keyboard Input
```bash
adb shell content insert --uri content://io.github.hadyahmed00.portal/keyboard/input \
  --bind base64_text:s:"SGVsbG8=" \
  --bind clear:b:true
```

#### 2. Keyboard Clear
```bash
adb shell content insert --uri content://io.github.hadyahmed00.portal/keyboard/clear
```

#### 3. Keyboard Key Event
```bash
adb shell content insert --uri content://io.github.hadyahmed00.portal/keyboard/key \
  --bind key_code:i:66
```
Common key codes: 4=Back, 66=Enter, 67=Backspace, 27=Tab

#### 4. Overlay Settings
```bash
adb shell content insert --uri content://io.github.hadyahmed00.portal/overlay_offset \
  --bind offset:i:100

adb shell content insert --uri content://io.github.hadyahmed00.portal/overlay_visible \
  --bind visible:b:true
```

#### 5. Socket Configuration
```bash
adb shell content insert --uri content://io.github.hadyahmed00.portal/socket_port \
  --bind port:i:8090
```

## Usage Examples

### Basic Usage (Mobile Class)

```python
from src.mobile import Mobile

# Initialize with MCP Helper enabled (default)
mobile = Mobile(device="emulator-5554")

# Get device state using MCP Helper
state = mobile.get_state(use_vision=False)
print(f"Interactive elements: {len(state.tree_state.interactive_elements)}")

# Get state with annotated screenshot
state = mobile.get_state(use_vision=True)
if state.screenshot:
    with open("screenshot.png", "wb") as f:
        f.write(state.screenshot)
```

### Direct MCPHelperClient Usage

```python
from src.mcp_helper import MCPHelperClient

client = MCPHelperClient(device_id="emulator-5554")

# Test connection
if client.ping():
    print(f"Version: {client.get_version()}")

# Get current app
phone_state = client.get_phone_state()
print(f"Current app: {phone_state.packageName}")

# Get UI tree
tree = client.get_a11y_tree()
for node in tree:
    print(f"{node.className}: {node.text}")

# Get installed apps
apps = client.get_packages()
for app in apps:
    if not app.isSystemApp:
        print(f"{app.label} ({app.packageName})")

# Send text input
client.keyboard_input("Hello World", clear=True)
client.keyboard_key(66)  # Press Enter
```

### Adapter Usage

```python
from src.mcp_helper import MCPHelperClient
from src.mcp_helper_adapter import MCPHelperMobileAdapter

client = MCPHelperClient(device_id="emulator-5554")
adapter = MCPHelperMobileAdapter(client)

# Get state as TreeState object
tree_state = adapter.get_state_tree()

# Get phone state
phone_state = adapter.get_phone_state()

# Get app list
apps = adapter.get_installed_apps()
```

## Fallback Behavior

The integration includes automatic fallback to UIAutomator:

1. **Initialization**: If MCP Helper doesn't respond, use_mcp_helper is set to False
2. **Runtime**: If a query fails, falls back to UIAutomator and disables MCP Helper
3. **Transparent**: Users don't need to change their code

```python
mobile = Mobile(device="emulator-5554")  # Tries MCP Helper first
state = mobile.get_state()               # Falls back automatically if needed
```

## Performance Characteristics

- **Query latency**: ~100-300ms per query (depending on tree complexity)
- **Cached state**: 0.5 second TTL (same as UIAutomator)
- **Network**: All communication via ADB (no direct network access needed)

**Expected speedup over UIAutomator**: 2-3x for simple queries, similar for large complex trees

## Data Structures

### TreeState (from existing code)
```python
@dataclass
class TreeState:
    interactive_elements: List[ElementNode]

@dataclass
class ElementNode:
    name: str
    coordinates: CenterCord  # (x, y) center point
    bounding_box: BoundingBox  # (x1, y1, x2, y2)
```

### PhoneState (new)
```python
@dataclass
class PhoneState:
    packageName: str          # Current package
    activityName: str         # Current activity
    keyboardVisible: bool     # IME visible
    isEditable: bool          # Focused element is editable
    focusedElement: Dict      # Resource ID of focused element
```

### A11yTreeNode (new - simplified)
```python
@dataclass
class A11yTreeNode:
    index: int                # Overlay index
    resourceId: str           # View resource ID
    className: str            # Class name (e.g., "android.widget.Button")
    text: str                 # Display text or content description
    bounds: str               # "x1, y1, x2, y2" format
    children: List            # Child nodes
```

### A11yFullNode (new - complete)
```python
@dataclass
class A11yFullNode:
    resourceId: str
    className: str
    packageName: str
    text: str
    contentDescription: str
    isClickable: bool
    isLongClickable: bool
    isFocusable: bool
    isFocused: bool
    isEnabled: bool
    isVisibleToUser: bool
    isEditable: bool
    boundsInScreen: Dict[str, int]  # {left, top, right, bottom}
    actionList: List[Dict]          # Available actions
    children: List[A11yFullNode]
```

## Error Handling

The integration provides multi-level error handling:

1. **Connection level**: Ping check on initialization
2. **Query level**: Try-except with automatic fallback
3. **Parsing level**: JSON validation with helpful error messages

```python
try:
    tree = client.get_a11y_tree()
except RuntimeError as e:
    print(f"Failed to get tree: {e}")
    # Falls back to UIAutomator automatically
```

## Testing

Run the comprehensive test suite:

```bash
python test_mcp_helper_integration.py
```

Tests included:
1. Direct MCP Helper client functionality
2. Adapter layer conversion
3. Mobile class integration
4. Performance comparison

## Troubleshooting

### "MCP Helper not responding" warning
- Ensure MCP Helper app is installed on device
- Check: `adb shell pm list packages | grep portal`
- App will automatically fallback to UIAutomator

### Empty or incorrect tree data
- Try with `filter=false`: `get_a11y_tree_full(include_small=False)`
- Check device is awake and responsive
- Verify current app and UI state

### Encoding errors on Windows
- UTF-8 encoding is handled automatically
- If issues persist, check Python 3.10+ is installed

### Performance slower than expected
- Check device connectivity with `adb devices`
- Complex UI hierarchies may be slower than simple screens
- UIAutomator fallback provides consistent baseline

## Integration Checklist

- [x] MCP Helper client library created (`src/mcp_helper.py`)
- [x] Adapter layer for compatibility (`src/mcp_helper_adapter.py`)
- [x] Mobile class updated with MCP Helper support
- [x] Automatic fallback to UIAutomator
- [x] Comprehensive test suite
- [x] Documentation and examples
- [x] Error handling and logging
- [x] Cross-platform support (Windows, Linux, macOS)

## Future Enhancements

Potential improvements for future versions:

1. **Caching Strategy**: Implement smarter caching based on app state
2. **Batch Queries**: Support multiple queries in single ADB call
3. **Streaming**: Real-time UI updates via streaming API
4. **Gesture Recording**: Record complex user interactions
5. **Vision Integration**: Better screenshot annotation with ML
6. **Metrics**: Performance profiling and optimization

## References

- [Android Accessibility API](https://developer.android.com/guide/topics/ui/accessibility)
- [Content Provider Basics](https://developer.android.com/guide/topics/providers/content-providers)
- [ADB Content Query Documentation](https://developer.android.com/studio/command-line/adb)

## Contributing

When modifying MCP Helper integration:

1. Update tests when adding new endpoints
2. Maintain backward compatibility with UIAutomator path
3. Add error handling for new queries
4. Document new data structures
5. Update this guide with new features

## License

Same as Android-MCP (MIT License 2025, Hady Ahmed)
