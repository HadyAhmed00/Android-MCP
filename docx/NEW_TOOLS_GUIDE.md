# New Tools Guide

This document covers the new tools added to Android-MCP. These tools make the agent smarter, faster, and more reliable when interacting with Android devices.

## Smart Element Finder

These tools let you interact with UI elements by their name or text instead of pixel coordinates. The agent no longer needs to call State-Tool first to look up coordinates.

### Click-Element-Tool

Finds an element on screen by its text and clicks it.

**Parameters:**
- `text` (required): The name or text of the element to click. Uses case-insensitive partial matching, so "log" will match "Login".
- `index` (optional, default 0): Which match to click when multiple elements share the same text. 0 means the first match, 1 means the second, and so on.

**Examples:**
```
Click-Element-Tool(text="Login")
Click-Element-Tool(text="OK", index=1)     # clicks the second "OK" button
Click-Element-Tool(text="settings")         # case insensitive, matches "Settings"
```

**What happens when the element is not found:**

The tool returns a list of all available elements on screen so the agent can pick the right one.

```
Element "Login" not found. Available elements: "Settings", "Profile", "Home", "Search"
```

### Long-Click-Element-Tool

Same as Click-Element-Tool but performs a long press (1 second hold).

**Parameters:**
- `text` (required): The name or text of the element.
- `index` (optional, default 0): Which match to long-click.

**Example:**
```
Long-Click-Element-Tool(text="photo.jpg")
```

### Type-Element-Tool

Finds an input field by its text, taps it to give it focus, then types text into it.

**Parameters:**
- `input_text` (required): The text to type.
- `element_text` (required): The name or placeholder text of the input field.
- `index` (optional, default 0): Which match to use.

**Examples:**
```
Type-Element-Tool(input_text="john@email.com", element_text="Email")
Type-Element-Tool(input_text="secret123", element_text="Password")
```

### How matching works

- The search is case-insensitive. "login" matches "Login", "LOGIN", "login button".
- The search is partial. "set" matches "Settings", "Reset", "Offset".
- If there are multiple matches, use the `index` parameter to pick which one.
- Elements are matched against their visible text, content description, or class name.


## Wait-For-Condition

Instead of waiting a fixed number of seconds with Wait-Tool, this tool polls the device screen until a specific condition is met. It checks the screen repeatedly and returns as soon as the condition is true, or returns a timeout message if the condition is never met.

### Wait-For-Condition-Tool

**Parameters:**
- `element_text` (optional): Wait until an element with this text appears on screen.
- `element_gone` (optional): Wait until an element with this text disappears from screen.
- `activity_name` (optional): Wait until the device is on a specific Android activity.
- `timeout` (optional, default 10): Maximum number of seconds to wait.
- `interval` (optional, default 1.0): How often to check, in seconds.

At least one of `element_text`, `element_gone`, or `activity_name` must be provided.

**Examples:**

Wait for a screen to finish loading:
```
Wait-For-Condition-Tool(element_text="Welcome", timeout=15)
```

Wait for a loading spinner to go away:
```
Wait-For-Condition-Tool(element_gone="Loading...", timeout=20)
```

Wait for a specific screen:
```
Wait-For-Condition-Tool(activity_name="HomeActivity", timeout=10)
```

Combine multiple conditions (all must be true):
```
Wait-For-Condition-Tool(element_text="Welcome", element_gone="Loading", timeout=15)
```

**Return values:**

When the condition is met:
```
Condition met after 2.3 seconds: element "Welcome" appeared.
```

When it times out:
```
Timed out after 10 seconds waiting for element "Welcome" to appear.
```

### How it works internally

1. The tool checks the device screen every `interval` seconds.
2. For `element_text`, it looks through all interactive elements for a case-insensitive partial match.
3. For `element_gone`, it checks that no element matches the text.
4. For `activity_name`, it checks the current activity using MCP Helper if available, or falls back to ADB `dumpsys`.
5. All specified conditions must be true at the same time for the tool to return success.
6. If `timeout` seconds pass without all conditions being met, it returns a timeout message.


## App Lifecycle Tools

These tools manage apps on the device. You can open apps, close them, reset their data, check what app is currently running, and list all installed apps.

### Launch-App-Tool

Opens an app by its package name. Works like tapping the app icon on the home screen.

**Parameters:**
- `package` (required): The Android package name of the app.

**Example:**
```
Launch-App-Tool(package="com.android.settings")
Launch-App-Tool(package="com.example.myapp")
```

### Kill-App-Tool

Force stops an app. The app process is killed immediately. Useful when an app is frozen or when you need to restart it fresh.

**Parameters:**
- `package` (required): The Android package name.

**Example:**
```
Kill-App-Tool(package="com.example.myapp")
```

### Clear-App-Data-Tool

Deletes all data for an app. This includes login sessions, cached files, saved preferences, and databases. After clearing, the app behaves like it was just installed.

**Parameters:**
- `package` (required): The Android package name.

**Example:**
```
Clear-App-Data-Tool(package="com.example.myapp")
```

This is useful for test isolation. Run this before each test scenario to make sure the app starts from a clean state.

### Get-Current-App-Tool

Returns information about the currently active app, including the package name, the current activity (screen), and whether the keyboard is visible.

**Parameters:** None.

**Example output:**
```
Current app: com.example.myapp
Current activity: .LoginActivity
Keyboard visible: false
```

This is useful for verifying that navigation worked correctly. After clicking "Login", you can check if the activity changed to confirm the action succeeded.

### List-Apps-Tool

Returns a list of all installed launchable apps on the device with their package names. Use this to discover the correct package name before calling Launch-App-Tool.

**Parameters:** None.

**Example output:**
```
Settings: com.android.settings
Chrome: com.android.chrome
MyApp: com.example.myapp
Calculator: com.android.calculator2
```


## Test Recording Support

All new tools are fully integrated with the test recording system. When recording is active, every action from these tools is captured and can be exported.

The new actions appear in exported scripts as follows:

**Python export:** Element-based tools export with coordinates resolved at recording time. App lifecycle tools export as direct ADB subprocess calls. Wait-for-condition exports as `time.sleep()` using the actual elapsed time from the recording.

**JSON export:** All parameters are saved including element text, coordinates, package names, and condition results.

**Readable export:** Actions appear as plain English steps like "Click on element Login at (540, 872)" or "Launch app com.example.myapp".


## Complete Tool List

After these additions, Android-MCP has 24 tools:

### Device Interaction
| Tool | What it does |
|------|-------------|
| State-Tool | Get the UI hierarchy and optional screenshot |
| Click-Tool | Click at x,y coordinates |
| Click-Element-Tool | Click an element by its text |
| Long-Click-Tool | Long press at x,y coordinates |
| Long-Click-Element-Tool | Long press an element by its text |
| Type-Tool | Type text at x,y coordinates |
| Type-Element-Tool | Type text into an element found by its text |
| Swipe-Tool | Swipe from one point to another |
| Drag-Tool | Drag and drop between two points |
| Press-Tool | Press a device button (home, back, power, etc.) |
| Notification-Tool | Open the notification panel |
| Wait-Tool | Wait a fixed number of seconds |
| Wait-For-Condition-Tool | Wait until a screen condition is met |

### App Management
| Tool | What it does |
|------|-------------|
| Launch-App-Tool | Open an app by package name |
| Kill-App-Tool | Force stop an app |
| Clear-App-Data-Tool | Wipe all app data |
| Get-Current-App-Tool | Check which app and screen is active |
| List-Apps-Tool | List all installed apps |

### Test Recording
| Tool | What it does |
|------|-------------|
| Start-Recording-Tool | Start capturing actions |
| Stop-Recording-Tool | Stop capturing actions |
| Export-Test-Script | Export recorded actions as a script |
| Clear-Recording-Tool | Clear recorded actions |
| Get-Recording-Stats-Tool | Show recording statistics |

### Bug Reporting
| Tool | What it does |
|------|-------------|
| Report-Bug-To-Azure | Generate an Azure DevOps bug report command |
| Report-Bug-To-Azure-Direct | Execute bug report directly via Azure CLI |
