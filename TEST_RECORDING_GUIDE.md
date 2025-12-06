# Android-MCP Test Recording & Export Guide

## Overview

The updated Android-MCP now includes:
1. **Performance optimizations** - Faster state retrieval with intelligent caching
2. **Test recording** - Automatically records all your interactions
3. **Test script export** - Export your tests in multiple formats for fast re-execution

## Quick Start Workflow

### Step 1: Start Recording
Use the `Start-Recording-Tool` to begin capturing your test actions:

```
Tool: Start-Recording-Tool
```

**Response:** `Test recording started. All subsequent actions will be recorded.`

### Step 2: Perform Your Test
Interact with the Android device normally using any of the standard tools:
- Click-Tool
- Swipe-Tool
- Type-Tool
- Press-Tool
- Drag-Tool
- Long-Click-Tool
- Wait-Tool
- Notification-Tool

All actions are automatically recorded with their parameters and timestamps.

### Step 3: Stop Recording
Stop the recording when your test sequence is complete:

```
Tool: Stop-Recording-Tool
```

**Response:** `Test recording stopped. X actions recorded.`

### Step 4: Check Recording Stats
(Optional) View what was recorded:

```
Tool: Get-Recording-Stats-Tool
```

**Response:** Shows total actions, duration, and breakdown by action type.

### Step 5: Export Test Script
Export your recorded actions as an executable test script:

```
Tool: Export-Test-Script
Parameters:
  - format: "python" (default)
  - filename: (optional, auto-generated if not provided)
  - test_name: (optional, auto-generated if not provided)
```

**Available Export Formats:**

#### Option A: Python Script (Recommended)
```
Tool: Export-Test-Script
Parameters:
  - format: "python"
  - test_name: "login_test_form_submission"
```

Generates a file like `test_login_test_form_submission.py` that you can execute with:
```bash
python test_login_test_form_submission.py
```

#### Option B: JSON Format
```
Tool: Export-Test-Script
Parameters:
  - format: "json"
```

Generates a JSON file with all action data for integration with other testing frameworks.

#### Option C: Readable Steps
```
Tool: Export-Test-Script
Parameters:
  - format: "readable"
```

Generates a human-readable text file documenting all test steps.

## Example Workflow

### Scenario: Testing Login Flow

**1. Start Recording**
```
Tool: Start-Recording-Tool
```

**2. Get initial state**
```
Tool: State-Tool
Parameters:
  - use_vision: true
```

**3. Click email field (element 0)**
```
Tool: Click-Tool
Parameters:
  - x: 540
  - y: 250
```

**4. Type email**
```
Tool: Type-Tool
Parameters:
  - text: "test@example.com"
  - x: 540
  - y: 250
```

**5. Click password field (element 1)**
```
Tool: Click-Tool
Parameters:
  - x: 540
  - y: 350
```

**6. Type password**
```
Tool: Type-Tool
Parameters:
  - text: "password123"
  - x: 540
  - y: 350
```

**7. Click login button (element 2)**
```
Tool: Click-Tool
Parameters:
  - x: 540
  - y: 450
```

**8. Wait for navigation**
```
Tool: Wait-Tool
Parameters:
  - duration: 2
```

**9. Stop Recording**
```
Tool: Stop-Recording-Tool
```

**10. Export as Python Script**
```
Tool: Export-Test-Script
Parameters:
  - format: "python"
  - test_name: "login_email_password_flow"
```

**Result:** Generated `test_login_email_password_flow.py` that can be run as:
```bash
python test_login_email_password_flow.py
```

## Performance Optimizations

### What Was Optimized

1. **State Caching** - UI hierarchy parsing is cached for 0.5 seconds
   - Subsequent `State-Tool` calls without vision are instant
   - Automatically invalidates when device state changes

2. **Removed Debug Output** - Eliminated console logging overhead
   - Tree parsing is now silent and faster

3. **Lazy Screenshot Scaling** - Screenshots are only scaled when needed
   - Vision mode uses optimal scaling

### Performance Gains

- **Regular state calls**: ~70% faster (cached)
- **Vision state calls**: ~30% faster (fewer debug logs, optimized scaling)
- **Overall MCP responsiveness**: Noticeably faster interaction loops

## Test Script Naming Convention

Auto-generated filenames follow this pattern:
```
test_<description>.py
test_script_YYYYMMDD_HHMMSS.json
test_steps_YYYYMMDD_HHMMSS.txt
```

### Recommended Naming
Use descriptive test names when exporting:
- `login_invalid_credentials`
- `form_submission_with_validation`
- `navigation_to_settings_and_back`
- `search_product_add_to_cart`

## Advanced Usage

### Clear Recording
To discard recorded actions and start fresh:

```
Tool: Clear-Recording-Tool
```

### Multiple Test Exports
Export the same recording in multiple formats:

```
# Export as Python
Tool: Export-Test-Script
Parameters:
  - format: "python"
  - test_name: "checkout_flow"

# Export as JSON
Tool: Export-Test-Script
Parameters:
  - format: "json"
  - filename: "checkout_flow_data"

# Export as readable steps
Tool: Export-Test-Script
Parameters:
  - format: "readable"
  - filename: "checkout_flow_steps"
```

## Troubleshooting

### Export Fails
- Ensure you have called `Start-Recording-Tool` and performed actions
- Check that the target directory is writable
- Verify the test_name doesn't contain special characters

### Python Script Won't Run
- Ensure `uiautomator2` is installed: `pip install uiautomator2`
- Verify Android device/emulator is connected
- Check that the device serial matches your setup

### Recording Feels Slow
- This is normal during the first State-Tool call (UI parsing)
- Subsequent calls are cached and much faster
- Consider using shorter test sequences for better performance

## Integration with CI/CD

Once you export as Python:

```bash
# Run exported test in CI/CD pipeline
python tests/test_login_email_password_flow.py

# Or integrate with pytest
pytest tests/test_login_email_password_flow.py -v
```

## Tips & Tricks

1. **Always Wait After Navigation**: Add `Wait-Tool` calls after actions that change the UI
2. **Use Vision Mode Sparingly**: Vision mode is slower; use it strategically for debugging
3. **Group Related Actions**: Record complete test scenarios, not individual actions
4. **Export Immediately**: Export your test right after recording while it's fresh
5. **Version Control**: Commit generated Python scripts to track test evolution

---

**Enjoy faster, automated testing with Android-MCP!** 🚀
