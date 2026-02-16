#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot MCP Helper and Android-MCP connection issues
"""

import sys
import time
import subprocess

def check_adb():
    """Check if ADB is available and device is connected"""
    print("=" * 60)
    print("1. Checking ADB and device connection")
    print("=" * 60)

    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
        print(result.stdout)

        if 'emulator-5554' in result.stdout or 'device' in result.stdout:
            print("[OK] Device is connected")
            return True
        else:
            print("[FAIL] No device found")
            return False
    except Exception as e:
        print(f"[ERROR] ADB check failed: {e}")
        return False


def check_mcp_helper():
    """Check if MCP Helper app is installed"""
    print("\n" + "=" * 60)
    print("2. Checking MCP Helper app installation")
    print("=" * 60)

    try:
        result = subprocess.run(
            ['adb', 'shell', 'pm', 'list', 'packages'],
            capture_output=True, text=True, timeout=5
        )

        if 'com.HadyAhmed00.MCP_Helper' in result.stdout:
            print("[OK] MCP Helper is installed")
            return True
        else:
            print("[FAIL] MCP Helper is NOT installed")
            print("Install it on your device and try again")
            return False
    except Exception as e:
        print(f"[ERROR] Check failed: {e}")
        return False


def test_mcp_helper_ping():
    """Test MCP Helper ping endpoint"""
    print("\n" + "=" * 60)
    print("3. Testing MCP Helper ping endpoint")
    print("=" * 60)

    try:
        print("Sending ping request...")
        result = subprocess.run(
            ['adb', 'shell', 'content', 'query', '--uri',
             'content://com.HadyAhmed00.MCP_Helper/ping'],
            capture_output=True, text=True, timeout=10
        )

        print(f"Response: {result.stdout}")

        if 'pong' in result.stdout:
            print("[OK] MCP Helper is responding")
            return True
        else:
            print("[FAIL] MCP Helper did not respond with pong")
            return False
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] MCP Helper query timed out after 10 seconds")
        print("This could mean:")
        print("  - MCP Helper app is not running")
        print("  - Device is slow or unresponsive")
        print("  - Content Provider is not properly registered")
        return False
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False


def test_python_import():
    """Test if MCP Helper Python client can be imported"""
    print("\n" + "=" * 60)
    print("4. Testing Python MCP Helper client import")
    print("=" * 60)

    try:
        from src.mcp_helper import MCPHelperClient
        print("[OK] MCPHelperClient imported successfully")
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False


def test_mcp_server_startup():
    """Test if MCP server can start without hanging"""
    print("\n" + "=" * 60)
    print("5. Testing MCP server startup (with timeout)")
    print("=" * 60)

    try:
        print("Starting main.py with 10 second timeout...")
        result = subprocess.run(
            [sys.executable, 'main.py', '--emulator'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("[OK] Server started and stopped cleanly")
            return True
        else:
            print(f"[WARN] Server exited with code {result.returncode}")
            print("Output:", result.stdout[:200])
            print("Errors:", result.stderr[:200])
            return False

    except subprocess.TimeoutExpired:
        print("[TIMEOUT] main.py did not respond within 10 seconds")
        print("This likely means MCP Helper initialization is blocking startup")
        print("\nSolution: The code has been updated to use lazy initialization")
        print("MCP Helper will only initialize when first needed, not at startup")
        return False
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("Android-MCP Diagnostic Tool")
    print("=" * 60)

    results = []

    # Run all checks
    results.append(("ADB & Device", check_adb()))
    results.append(("MCP Helper Installed", check_mcp_helper()))
    results.append(("MCP Helper Ping", test_mcp_helper_ping()))
    results.append(("Python Import", test_python_import()))
    results.append(("MCP Server Startup", test_mcp_server_startup()))

    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\nPassed: {passed_count}/{total_count}")

    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    if all(p for _, p in results):
        print("[OK] All checks passed! Your setup is working correctly.")
        print("\nTo use Android-MCP:")
        print("  python main.py --emulator")
    else:
        if not results[0][1]:
            print("[ACTION] Connect an Android device via ADB")
            print("  adb devices")

        if not results[1][1]:
            print("[ACTION] Install MCP Helper app on your device")
            print("  See: https://github.com/HadyAhmed00/Android-MCP-Helper")

        if not results[2][1]:
            print("[ACTION] Ensure MCP Helper app is running")
            print("  - Open Settings > Apps > MCP Helper")
            print("  - Make sure it has permission to run in background")
            print("  - Try restarting the device")

        if not results[3][1]:
            print("[ACTION] Reinstall Android-MCP dependencies")
            print("  pip install -r requirements.txt")

        if not results[4][1]:
            print("[INFO] MCP server startup issue detected")
            print("  The code has been updated to use lazy initialization")
            print("  This means MCP Helper won't block startup anymore")
            print("  Try running: python main.py --emulator")

    return 0 if all(p for _, p in results) else 1


if __name__ == "__main__":
    sys.exit(main())
