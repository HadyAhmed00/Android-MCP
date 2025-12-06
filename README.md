# Android-MCP

**Android-MCP** is a lightweight, open-source tool that bridges between AI agents and Android devices. Running as an MCP server, it lets LLM agents perform real-world tasks such as **app navigation, UI interaction and automated QA testing** without relying on traditional computer-vision pipelines or preprogrammed scripts.

**Forked and customized by Hady Ahmed**

## Features

- **Direct Device Control**: Click, swipe, drag, type, and press buttons on Android devices
- **UI State Inspection**: Get device state with UI hierarchy and optional annotated screenshots
- **MCP Integration**: Works with any MCP-compatible client (Claude Desktop, VS Code, etc.)
- **Emulator Support**: Works with Android emulators (tested on emulator-5554)
- **Physical Device Support**: Connect to real Android devices via ADB
- **Vision Capabilities**: Generate annotated screenshots with numbered UI elements for vision-based AI agents

## Requirements

- Python 3.12+
- Android device or emulator running
- ADB (Android Debug Bridge) installed and configured
- `uiautomator2` compatible Android device (Android 4.4+)

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/HadyAhmed00/Android-MCP.git
cd Android-MCP
```

2. Install dependencies:
```bash
pip install -e .
```

Or install manually:
```bash
pip install mcp uiautomator2 pillow ipykernel
```

## Quick Start

### 1. Start the MCP Server

**For emulator:**
```bash
python main.py --emulator
```

**For physical device:**
```bash
python main.py
```

The server will connect to your Android device via ADB and start listening for MCP client connections.

### 2. Configure with MCP Client

To use this with Claude Code or other MCP clients, add the following to your MCP configuration:

**Example MCP Config:**
```json
{
  "mcpServers": {
    "android-mcp": {
      "command": "python",
      "args": [
        "/path/to/Android-MCP/main.py",
        "--emulator"
      ]
    }
  }
}
```

## Available Tools

The MCP server exposes 9 tools for controlling Android devices:

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

## Usage Workflow

### Basic Example: Navigate and Click

1. **Get device state with vision:**
   ```
   Get the current state of the device with a screenshot
   ```
   This returns the UI hierarchy and an annotated screenshot showing numbered UI elements.

2. **Click on an element:**
   ```
   Click on element 0 (the button that was labeled as 0)
   ```

3. **Get updated state:**
   ```
   Get the device state again
   ```

### Example: Form Submission

```
1. Get device state with vision to see the form
2. Click on the name field (element 2)
3. Type "John Doe"
4. Click on the email field (element 3)
5. Type "john@example.com"
6. Scroll down to find the submit button
7. Click the submit button
8. Wait 2 seconds for the form to process
9. Get device state to confirm submission
```

### Example: App Navigation

```
1. Get device state to see current screen
2. Click the "Settings" button
3. Wait 1 second for settings to load
4. Get device state to see settings menu
5. Click on "About Phone"
6. Get state to view device information
```

## Architecture

The project is organized into three main modules:

### `main.py`
- Entry point that creates the FastMCP server
- Defines and exposes all 9 tools
- Handles command-line arguments (`--emulator`)

### `src/mobile/`
- **Mobile class**: Manages device connection and state
- **MobileState**: Data class representing device state
- Captures screenshots and processes them

### `src/tree/`
- **Tree class**: Parses Android UI XML hierarchy
- Extracts interactive elements (buttons, inputs, etc.)
- Generates annotated screenshots with numbered labels
- Helper utilities for coordinate extraction

## Troubleshooting

### Device Not Connecting

1. **Check ADB:**
   ```bash
   adb devices
   ```
   Your device should appear in the list.

2. **For emulators:**
   ```bash
   adb connect emulator-5554
   ```

3. **Enable USB Debugging** (for physical devices):
   - Go to Settings > Developer Options
   - Enable USB Debugging
   - Connect your device

### No Interactive Elements Found

This can happen if:
- The app hasn't fully loaded - try waiting with `Wait-Tool`
- The UI uses unusual widgets not in the `INTERACTIVE_CLASSES` list
- Screen is at an unusual rotation

Try getting device state with vision to see what's actually on screen.

### Screenshots Not Working

- Ensure the device screen is on
- Check that the device has enough storage
- Try waiting a moment before requesting screenshots

## Development

### Running Tests

Tests for the UI tree parsing:
```bash
pytest tests/
```

### Adding New Tools

To add a new tool to the MCP server:

1. Add a function in `main.py` decorated with `@mcp.tool()`
2. Define parameters with type hints
3. Return results that can be serialized (strings, lists, or Images)

Example:
```python
@mcp.tool(name='My-Tool', description='Description of what this does')
def my_tool(param1: str, param2: int):
    result = mobile.get_device().some_action(param1, param2)
    return f'Action completed: {result}'
```

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Verify your Android device setup with ADB
3. Open an issue on GitHub with:
   - Device details (type, Android version)
   - Error messages
   - Steps to reproduce
