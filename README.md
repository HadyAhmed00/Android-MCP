# Android-MCP
**Android-MCP** is a lightweight, open-source tool that bridge between AI agents and Android devices. Running as an MCP server, it lets LLM agents perform real-world tasks such as **app navigation, UI interaction and automated QA testing** without relying on traditional computer-vision pipelines or preprogramed scripts.

## Features

- **Direct Device Control**: Click, swipe, drag, type, and press buttons on Android devices
- **UI State Inspection**: Get device state with UI hierarchy and optional annotated screenshots
- **MCP Integration**: Works with any MCP-compatible client (Claude Desktop, VS Code, etc.)
- **Emulator Support**: Works with Android emulators (tested on emulator-5554)
- **Physical Device Support**: Connect to real Android devices via ADB
- **Vision Capabilities**: Generate annotated screenshots with numbered UI elements for vision-based AI agents
- **Test Recording**: Record user interactions and export as executable test scripts (Python, JSON, or human-readable format)
- **Test Script Export**: Export recorded tests as Python (ADB or uiautomator2), pytest, JSON, or human-readable format

## Requirements

- An Android device or emulator with USB debugging enabled
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (it fetches Python for you)

That's it. ADB is bundled, and the Portal helper app is installed onto the device
automatically on first use.

## Installation

```bash
claude mcp add android -- uvx android-mcp@latest --emulator
```

Drop `--emulator` for a physical device, or pass `--device <id>` to pick one.

For any other MCP client, use the equivalent config:

```json
{
  "mcpServers": {
    "android-mcp": {
      "command": "uvx",
      "args": ["android-mcp@latest", "--emulator"]
    }
  }
}
```

### What happens on first use

1. **ADB** — uses `adb` from your PATH, or falls back to the copy bundled with the
   `adbutils` dependency, so no Android SDK install is required.
2. **Portal app** — the fast state-reading backend needs the
   [Portal app](https://github.com/HadyAhmed00/Android-MCP-Portal) on the device. If it is
   missing, the server downloads the pinned APK, installs it, and enables its accessibility
   service, then verifies with a ping.
3. If any of that fails (some OEMs block enabling accessibility services over ADB), the
   server prints manual steps and keeps working on the slower UIAutomator2 backend.

Run it yourself any time with:

```bash
uvx android-mcp setup --device emulator-5554     # add --force-setup to reinstall
```

or ask the agent to call the `Setup-Device` tool.

Flags: `--skip-bootstrap` never touches the device, `--portal-apk <path>` installs a local APK.
The downloaded APK is cached per-user; set `ANDROID_MCP_CACHE_DIR` to move that cache.

### From source (development)

```bash
git clone https://github.com/HadyAhmed00/Android-MCP.git
cd Android-MCP
uv sync
python main.py --emulator          # or: python -m android_mcp --emulator
```

## Available Tools

The MCP server exposes 19 tools for controlling Android devices and recording test cases:

### 1. **State-Tool**
Get the current state of the device including UI hierarchy and optional screenshot.

**Parameters:**
- `use_vision` (bool, optional): Include annotated screenshot with labeled UI elements

**Example:**
```
Get device state with screenshot
```

### 2. **Click-Tool**
Click on a specific coordinate on the screen.

**Parameters:**
- `x` (int): X coordinate
- `y` (int): Y coordinate

**Example:**
```
Click on coordinates 540, 800
```

### 3. **Long-Click-Tool**
Long press (hold) on a specific coordinate.

**Parameters:**
- `x` (int): X coordinate
- `y` (int): Y coordinate

**Example:**
```
Long click on 540, 800 for 2 seconds
```

### 4. **Swipe-Tool**
Perform a swipe gesture from one point to another.

**Parameters:**
- `x1` (int): Starting X coordinate
- `y1` (int): Starting Y coordinate
- `x2` (int): Ending X coordinate
- `y2` (int): Ending Y coordinate

**Example:**
```
Swipe from top to bottom (refresh)
```

### 5. **Type-Tool**
Type text at a specific coordinate (automatically focuses the field).

**Parameters:**
- `text` (str): Text to type
- `x` (int): X coordinate
- `y` (int): Y coordinate
- `clear` (bool, optional): Clear existing text before typing

**Example:**
```
Type "hello world" into the search field
```

### 6. **Drag-Tool**
Drag from one location and drop at another.

**Parameters:**
- `x1` (int): Starting X coordinate
- `y1` (int): Starting Y coordinate
- `x2` (int): Ending X coordinate
- `y2` (int): Ending Y coordinate

**Example:**
```
Drag and drop item from position to trash
```

### 7. **Press-Tool**
Press device buttons (home, back, power, volume, etc.).

**Parameters:**
- `button` (str): Button name (back, home, power, volume_up, volume_down)

**Example:**
```
Press the back button
```

### 8. **Notification-Tool**
Open the notification bar to access notifications.

**Parameters:** None

**Example:**
```
Open notification bar
```

### 9. **Wait-Tool**
Wait for a specified duration (useful for allowing apps to load).

**Parameters:**
- `duration` (int): Seconds to wait

**Example:**
```
Wait for 2 seconds
```

### 9b. **Click-By-Label**
Tap an element by its label index from the most recent `State-Tool` output. Preferred over
raw coordinates. **Indices are positional and only valid against the latest state** — they
shift whenever the screen changes.

**Parameters:**
- `label` (int): Index from the `--- Interactive Elements ---` list

### 9c. **Setup-Device**
Install the Portal helper app and enable its accessibility service. Use it when `State-Tool`
is slow or the fast backend is unavailable.

**Parameters:**
- `force` (bool, optional): Reinstall even if the app already works

### 10. **Start-Recording-Tool**
Start recording test actions for later export and playback.

**Parameters:** None

**Example:**
```
Start recording test actions
```

### 11. **Stop-Recording-Tool**
Stop recording test actions.

**Parameters:** None

**Example:**
```
Stop recording and finalize test
```

### 12. **Export-Test-Script**
Export recorded test actions as an executable test script in multiple formats.

**Parameters:**
- `format` (str): Export format - 'python', 'json', or 'readable' (default: 'python')
- `filename` (str, optional): Custom filename without extension
- `test_name` (str, optional): Custom test name for Python exports

**Example:**
```
Export recorded actions as a Python test script
```

### 13. **Clear-Recording-Tool**
Clear all recorded test actions.

**Parameters:** None

**Example:**
```
Clear the recording
```

### 14. **Get-Recording-Stats-Tool**
Get statistics about recorded test actions.

**Parameters:** None

**Example:**
```
Show recording statistics
```
## Architecture

The project is organized into three main modules:

### `main.py`
- Entry point that creates the FastMCP server
- Defines and exposes all 14 tools
- Handles command-line arguments (`--emulator`)
- Integrates test recording functionality

### `src/mobile/`
- **Mobile class**: Manages device connection and state
- **MobileState**: Data class representing device state
- Captures screenshots and processes them

### `src/tree/`
- **Tree class**: Parses Android UI XML hierarchy
- Extracts interactive elements (buttons, inputs, etc.)
- Generates annotated screenshots with numbered labels
- Helper utilities for coordinate extraction

### `src/recorder.py`
- **TestRecorder class**: Records user actions during testing
- **TestAction**: Data class representing a single action
- Supports multiple export formats (Python, JSON, Readable)
- Generates fully independent ADB-based Python scripts
- Exports structured test data for CI/CD integration
