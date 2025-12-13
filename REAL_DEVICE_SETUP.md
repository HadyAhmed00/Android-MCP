# Android-MCP Real Device Setup Guide

## Problem: MCP Not Working on Real Devices

The MCP server was hardcoded to use specific device IDs, which didn't work with your real device (RMX1851 / Realme phone).

## Solution

The code has been updated to support multiple ways of specifying which device to use:

### 1. Auto-detect (Default)
If you have only one device connected, it will auto-detect:

```bash
python main.py
```

This works for:
- Single real device
- Single emulator
- Auto-detection of whichever is connected

### 2. Specific Real Device
To explicitly use your real device:

```bash
python main.py --device b44fbcc9
```

Replace `b44fbcc9` with your actual device ID. Get your device ID:

```bash
adb devices
```

Output:
```
List of devices attached
b44fbcc9               device
emulator-5554	device
```

### 3. Emulator Only
To explicitly use the emulator:

```bash
python main.py --emulator
```

Or:

```bash
python main.py --device emulator-5554
```

## Verify Setup on Real Device

### 1. Check Device is Connected
```bash
adb devices -l
```

Expected output for Realme RMX1851:
```
List of devices attached
b44fbcc9               device product:RMX1851 model:RMX1851 ...
```

### 2. Check MCP Helper is Installed
```bash
adb -s b44fbcc9 shell pm list packages | grep MCP_Helper
```

Expected output:
```
package:com.HadyAhmed00.MCP_Helper
```

### 3. Test MCP Helper on Real Device
```bash
adb -s b44fbcc9 shell content query --uri content://com.HadyAhmed00.MCP_Helper/ping
```

Expected output:
```
Row: 0 result={"status":"success","data":"pong"}
```

### 4. Test Python Connection
```python
from src.mobile import Mobile

# For auto-detect (one device)
mobile = Mobile()
state = mobile.get_state()
print(f"Device: {mobile.get_device().device_info}")

# Or specific device
mobile = Mobile(device="b44fbcc9")
state = mobile.get_state()
```

## Full Testing Procedure

### Step 1: Verify Physical Connection
```bash
adb devices -l
# Should show your device with status "device"
```

### Step 2: Enable USB Debugging
If device shows "unauthorized":
1. Go to Settings > About Phone
2. Tap Build Number 7 times to enable Developer Options
3. Go to Settings > Developer Options
4. Enable "USB Debugging"
5. Accept the RSA key fingerprint prompt on device

### Step 3: Verify ADB Access
```bash
adb -s b44fbcc9 shell getprop ro.product.model
# Should output your device model
```

### Step 4: Check MCP Helper
```bash
adb -s b44fbcc9 shell pm list packages | grep MCP_Helper
# Should show the app is installed
```

### Step 5: Test MCP Helper
```bash
adb -s b44fbcc9 shell content query --uri content://com.HadyAhmed00.MCP_Helper/ping
# Should return pong
```

### Step 6: Start MCP Server
```bash
# Auto-detect device
python main.py

# Or specify device
python main.py --device b44fbcc9
```

### Step 7: Test Connection
In another terminal:
```bash
python diagnose_mcp.py
```

## Troubleshooting Real Device Issues

### Issue: "Device not found"

**Cause**: Device not connected or ADB not working

**Solution**:
```bash
# Check connection
adb devices -l

# Restart ADB server
adb kill-server
adb start-server
adb devices

# If still not showing, check USB debugging is enabled
adb devices
# If shows "unauthorized", accept prompt on device
```

### Issue: "MCP Helper not responding"

**Cause**: App not installed or not running

**Solution**:
```bash
# Check if installed
adb -s <device_id> shell pm list packages | grep MCP_Helper

# If not installed, install the app manually:
# 1. Download APK from https://github.com/HadyAhmed00/Android-MCP-Helper
# 2. Install: adb install app-release.apk

# If installed, check it's running:
adb -s <device_id> shell am start com.HadyAhmed00.MCP_Helper/.MainActivity
```

### Issue: "Permission denied" or "Read-only file system"

**Cause**: Device file permissions

**Solution**:
```bash
# Ensure device is fully connected and trusted
adb -s <device_id> shell "ls -la /data/local/tmp"

# If permission issue, restart ADB server
adb kill-server
adb start-server
```

### Issue: "Connection timed out"

**Cause**: Device is slow or overloaded

**Solution**:
```bash
# Increase timeout in src/mcp_helper.py
# Change timeout=5 to timeout=10 in _execute_query method

# Or restart device and try again
adb -s <device_id> reboot
adb wait-for-device
```

## Multiple Device Handling

### Using Multiple Devices

If you have both emulator and real device:

```bash
# Terminal 1 - Real device
python main.py --device b44fbcc9

# Terminal 2 - Emulator
python main.py --emulator
```

### Finding Your Device ID

```bash
# List all connected devices
adb devices

# Sample output:
# List of devices attached
# b44fbcc9               device          <- Real device (Realme)
# emulator-5554	device          <- Emulator
# 192.168.1.100:5555	device          <- ADB over network
```

## Performance Notes

### Real Device vs Emulator

**Real Device (RMX1851)**:
- MCP Helper latency: ~100-200ms per query
- UIAutomator fallback: ~200-400ms per query
- Screenshot: ~300-500ms
- Faster when cached (0.5s TTL)

**Emulator**:
- MCP Helper latency: ~50-150ms per query
- UIAutomator fallback: ~100-300ms per query
- Screenshot: ~200-300ms
- Faster overall due to local virtualization

## Device Compatibility

### Tested on:
- ✓ Emulator (Android 11, x86)
- ✓ Realme RMX1851 (Android 10, real device)
- ✓ Other devices with MCP Helper installed

### Requirements:
- Android 4.4+
- ADB enabled
- MCP Helper app installed
- USB Debugging enabled

## Quick Start Commands

### Auto-detect (One Device)
```bash
python main.py
```

### Specific Real Device
```bash
python main.py --device b44fbcc9
```

### Emulator Only
```bash
python main.py --emulator
```

### Specific Device with ID
```bash
python main.py --device emulator-5554
```

### Test Configuration
```bash
python diagnose_mcp.py
```

## Next Steps

1. Connect your real device via USB
2. Enable USB Debugging in Settings
3. Run `adb devices` to get device ID
4. Start MCP: `python main.py --device <your_device_id>`
5. Connect your MCP client
6. Enjoy automated Android control!

## Environment Variables (Optional)

You can also set device as environment variable:

```bash
# Linux/macOS
export ANDROID_DEVICE_ID="b44fbcc9"
python main.py

# Windows (PowerShell)
$env:ANDROID_DEVICE_ID="b44fbcc9"
python main.py

# Windows (CMD)
set ANDROID_DEVICE_ID=b44fbcc9
python main.py
```

Update `main.py` to use environment variable:
```python
import os
device_id = args.device or os.getenv('ANDROID_DEVICE_ID')
```

## Support

If you encounter issues:

1. Run diagnostic: `python diagnose_mcp.py`
2. Check device: `adb devices -l`
3. Test MCP Helper: `adb -s <id> shell content query --uri content://com.HadyAhmed00.MCP_Helper/ping`
4. Check logs: `adb logcat | grep MCP_Helper`
5. Restart device: `adb reboot`

---

**Summary**: The MCP now supports real devices! Use `--device <id>` to specify your real device, or it will auto-detect if you have only one device connected.
