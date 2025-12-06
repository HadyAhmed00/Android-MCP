# Android-MCP

**Android-MCP** is a lightweight, open-source tool that bridges between AI agents and Android devices. Running as an MCP server, it lets LLM agents perform real-world tasks such as **app navigation, UI interaction and automated QA testing** without relying on traditional computer-vision pipelines or preprogrammed scripts.

**Forked and customized by Hady Ahmed**

## Demo Video

[![Android-MCP Demo](https://img.shields.io/badge/Watch-Demo%20Video-FF0000?style=for-the-badge&logo=youtube)](MCP%20video.mp4)

Watch a quick demonstration of Android-MCP in action showing test recording and device control features.

## Features

- **Direct Device Control**: Click, swipe, drag, type, and press buttons on Android devices
- **UI State Inspection**: Get device state with UI hierarchy and optional annotated screenshots
- **MCP Integration**: Works with any MCP-compatible client (Claude Desktop, VS Code, etc.)
- **Emulator Support**: Works with Android emulators (tested on emulator-5554)
- **Physical Device Support**: Connect to real Android devices via ADB
- **Vision Capabilities**: Generate annotated screenshots with numbered UI elements for vision-based AI agents
- **Test Recording**: Record user interactions and export as executable test scripts (Python, JSON, or human-readable format)
- **Test Script Export**: Export recorded tests in multiple formats for CI/CD integration

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

The MCP server exposes 14 tools for controlling Android devices and recording test cases:

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

## Test Recording Workflow

The test recording feature allows you to capture user interactions with Android devices and export them as executable test scripts. This is useful for:
- **Automating Regression Testing**: Replay recorded user flows
- **CI/CD Integration**: Run tests automatically in your pipeline
- **Documentation**: Create executable documentation of app workflows
- **Test Maintenance**: Easily update and maintain test scripts

### Basic Test Recording Workflow

1. **Start Recording:**
   ```
   Start recording test actions
   ```
   This initializes a new recording session.

2. **Perform Device Actions:**
   ```
   Click, swipe, type, and interact with the device normally
   ```
   All actions are automatically recorded.

3. **Stop Recording:**
   ```
   Stop recording and finalize test
   ```
   Recording is paused.

4. **Export Test Script:**
   ```
   Export recorded actions as a Python test script
   ```

5. **Run the Generated Script:**
   ```bash
   python test_script_YYYYMMDD_HHMMSS.py
   ```
   Or with a custom device ID:
   ```bash
   python test_script_YYYYMMDD_HHMMSS.py emulator-5554
   ```

### Export Formats

The test recorder supports three export formats:

#### Python Format (Executable)
Exports as a fully independent Python script using ADB commands. No external dependencies required.
```bash
Export recorded actions as Python
```
This generates a `test_*.py` file that can be executed directly.

#### JSON Format (Data)
Exports test data as JSON for integration with other tools.
```bash
Export recorded actions as JSON
```
This generates a `test_script_*.json` file with structured action data.

#### Readable Format (Documentation)
Exports test steps as human-readable text.
```bash
Export recorded actions as readable
```
This generates a `test_steps_*.txt` file with step-by-step descriptions.

### Example: Recording a Login Flow

```
1. Start recording
2. Get device state to see the login screen
3. Click on the username field
4. Type your username
5. Click on the password field
6. Type your password
7. Click the login button
8. Wait 2 seconds for login to complete
9. Get device state to verify login success
10. Stop recording
11. Export as Python
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

## Video Documentation

For visual walkthroughs and demonstrations of Android-MCP features, see the video documentation:

- **[Setup & Installation](link-to-video-1)** - Getting started with Android-MCP installation and configuration
- **[Basic Device Interaction](link-to-video-2)** - Demonstrating click, swipe, type, and other interactions
- **[Test Recording Demo](link-to-video-3)** - How to record test cases and export as executable scripts
- **[UI Hierarchy & Vision](link-to-video-4)** - Understanding UI hierarchy parsing and annotated screenshots
- **[CI/CD Integration](link-to-video-5)** - Integrating recorded tests into your CI/CD pipeline

**Note:** Replace the placeholder links with actual video URLs once they are uploaded to your documentation site or YouTube channel.

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
