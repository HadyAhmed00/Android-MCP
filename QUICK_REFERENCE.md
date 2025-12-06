# Android-MCP Quick Reference Card

## 🚀 Test Recording Workflow

```
1. Start-Recording-Tool
   ↓
2. [Perform your test actions]
   ├─ Click-Tool
   ├─ Type-Tool
   ├─ Swipe-Tool
   ├─ Wait-Tool
   ├─ Press-Tool
   └─ etc.
   ↓
3. Stop-Recording-Tool
   ↓
4. Export-Test-Script (format: "python", test_name: "your_test_name")
   ↓
5. python test_your_test_name.py [RUN AGAIN ANYTIME]
```

## 📋 All Available Tools

### Core Tools (Interaction)
| Tool | Parameters | Purpose |
|------|-----------|---------|
| **State-Tool** | `use_vision: bool` | Get UI state (with optional screenshot) |
| **Click-Tool** | `x: int, y: int` | Click at coordinates |
| **Long-Click-Tool** | `x: int, y: int` | Long press at coordinates |
| **Swipe-Tool** | `x1, y1, x2, y2: int` | Swipe between coordinates |
| **Type-Tool** | `text: str, x: int, y: int, clear: bool` | Type text |
| **Drag-Tool** | `x1, y1, x2, y2: int` | Drag and drop |
| **Press-Tool** | `button: str` | Press device button (back, home, power, etc) |
| **Notification-Tool** | *none* | Open notification bar |
| **Wait-Tool** | `duration: int` | Wait for X seconds |

### Recording Tools (Test Management)
| Tool | Parameters | Purpose |
|------|-----------|---------|
| **Start-Recording-Tool** | *none* | Begin recording actions |
| **Stop-Recording-Tool** | *none* | End recording session |
| **Export-Test-Script** | `format, filename, test_name` | Export recorded test |
| **Clear-Recording-Tool** | *none* | Clear all recorded actions |
| **Get-Recording-Stats-Tool** | *none* | View recording statistics |

## 🎯 Export Formats

### Python (Recommended)
```
Export-Test-Script
├─ format: "python"
├─ filename: "test_login" (optional)
└─ test_name: "login_with_email" (optional)

Result: test_login_with_email.py
Usage: python test_login_with_email.py
```

### JSON
```
Export-Test-Script
├─ format: "json"
└─ filename: "test_data" (optional)

Result: test_data.json
Contains: All action data in structured format
```

### Readable
```
Export-Test-Script
├─ format: "readable"
└─ filename: "test_steps" (optional)

Result: test_steps.txt
Contains: Human-readable test steps
```

## ⚡ Performance Tips

| Action | Expected Time |
|--------|--------------|
| First State-Tool call | ~500-800ms |
| State-Tool (cached) | ~150-200ms |
| Click/Type/Swipe | ~50-100ms each |
| Vision State-Tool | ~900-1100ms |

**Cache Behavior:**
- Caches for 0.5 seconds automatically
- Each action preserves cache
- Invalidates on device state change

## 📝 Example: Complete Login Test

```
1. Start-Recording-Tool

2. State-Tool (use_vision: true)
   → See all UI elements numbered

3. Click-Tool (x: 540, y: 250)
   → Click email field (element 0)

4. Type-Tool (text: "user@test.com", x: 540, y: 250)
   → Enter email

5. Click-Tool (x: 540, y: 350)
   → Click password field

6. Type-Tool (text: "password", x: 540, y: 350)
   → Enter password

7. Click-Tool (x: 540, y: 450)
   → Click login button

8. Wait-Tool (duration: 2)
   → Wait for navigation

9. Stop-Recording-Tool

10. Export-Test-Script (format: "python", test_name: "login_flow")

11. python test_login_flow.py
    → Run test anytime!
```

## 🔧 Configuration

### Adjust Cache Duration
Edit `src/mobile/__init__.py`:
```python
self._cache_ttl = 0.5  # in seconds (0.1-1.0 recommended)
```

## 📊 Recording Statistics Example

```
Get-Recording-Stats-Tool Response:

Recording Statistics:
- Total actions: 8
- Duration: 12.45 seconds
- Recording status: Inactive

Action breakdown:
  - click: 4
  - type: 2
  - wait: 1
  - swipe: 1
```

## 🎨 Generated Python Script Structure

```python
"""
Auto-generated test script: my_test_name
Generated: 2025-12-06T12:30:45.123456
Total actions: 5
"""

import uiautomator2 as u2
import time

def run_test(device=None):
    """Run the recorded test sequence."""
    if device is None:
        device = u2.connect()

    # Action 1: Comment with action details
    device.action_method(params)

    # Action 2: ...
    device.action_method(params)

    # ... more actions ...

if __name__ == "__main__":
    run_test()
```

## 🚨 Common Issues & Solutions

| Problem | Solution |
|---------|----------|
| Export fails | Ensure Start-Recording-Tool was called |
| Script won't run | Check uiautomator2 installed: `pip install uiautomator2` |
| Device not responding | Verify device is connected: `adb devices` |
| Slow state calls | First call is slow (parsing), subsequent calls are cached |
| Can't find element | Use State-Tool with vision to see all elements |

## 📚 Related Documentation

- **Detailed Guide**: See `TEST_RECORDING_GUIDE.md`
- **Optimization Details**: See `OPTIMIZATION_SUMMARY.md`
- **Main README**: See `README.md`

## 🎓 Best Practices

✅ **DO:**
- Record complete test scenarios (not single actions)
- Export tests with descriptive names
- Add Wait-Tool after navigation changes
- Use vision mode sparingly (slower)
- Version control generated Python scripts

❌ **DON'T:**
- Record extremely long sequences (>100 actions)
- Use vision mode for every state check
- Ignore cache warnings (first call will be slow)
- Export without meaningful test names
- Modify generated Python scripts manually

## 🔗 Typical Workflow Duration

| Step | Time |
|------|------|
| Record test | ~2-5 minutes |
| Export to Python | <1 second |
| First run | ~30-60 seconds |
| Subsequent runs | ~20-30 seconds |

---

**Ready to record?** Start with `Start-Recording-Tool` now! 🎬
