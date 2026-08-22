#!/usr/bin/env python3
"""
Test script for MCP Helper integration with Android-MCP
Validates that the Content Provider approach works correctly
"""

import sys
import os
import io

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from android_mcp.mcp_helper import MCPHelperClient
from android_mcp.mcp_helper_adapter import MCPHelperTreeAdapter, MCPHelperMobileAdapter
from android_mcp.mobile import Mobile


def test_mcp_helper_direct():
    """Test MCP Helper client directly"""
    print("\n" + "=" * 60)
    print("TEST 1: Direct MCP Helper Client")
    print("=" * 60)

    try:
        client = MCPHelperClient(device_id="emulator-5554")

        # Test ping
        print("\n[1] Testing ping...")
        if client.ping():
            print("[OK] Ping successful")
        else:
            print("[FAIL] Ping failed")
            return False

        # Test version
        print("\n[2] Getting version...")
        version = client.get_version()
        print(f"[OK] Version: {version}")

        # Test phone state
        print("\n[3] Getting phone state...")
        phone_state = client.get_phone_state()
        print(f"[OK] Current app: {phone_state.packageName}")
        print(f"     Activity: {phone_state.activityName}")
        print(f"     Keyboard visible: {phone_state.keyboardVisible}")

        # Test a11y_tree (simplified)
        print("\n[4] Getting accessibility tree (simplified)...")
        tree_nodes = client.get_a11y_tree()
        print(f"[OK] Root node has {len(tree_nodes)} children")
        if tree_nodes:
            first_node = tree_nodes[0]
            print(f"     First node: {first_node.className}")
            print(f"     Text: {first_node.text}")
            print(f"     Bounds: {first_node.bounds}")

        # Test a11y_tree_full
        print("\n[5] Getting accessibility tree (full)...")
        full_tree = client.get_a11y_tree_full(include_small=False)
        print(f"[OK] Root: {full_tree.className}")
        print(f"     Children: {len(full_tree.children)}")
        print(f"     Clickable: {full_tree.isClickable}")
        print(f"     Visible: {full_tree.isVisibleToUser}")

        # Test packages
        print("\n[6] Getting installed packages...")
        packages = client.get_packages()
        print(f"[OK] Found {len(packages)} packages")
        user_apps = [p for p in packages if not p.isSystemApp]
        print(f"     User apps: {len(user_apps)}")
        if user_apps:
            print(f"     First user app: {user_apps[0].label} (v{user_apps[0].versionName})")

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adapter():
    """Test MCP Helper adapter"""
    print("\n" + "=" * 60)
    print("TEST 2: MCP Helper Adapter")
    print("=" * 60)

    try:
        client = MCPHelperClient(device_id="emulator-5554")
        adapter = MCPHelperMobileAdapter(client)

        # Test tree conversion
        print("\n[1] Converting tree to TreeState...")
        tree_state = adapter.get_state_tree()
        print(f"[OK] Got TreeState with {len(tree_state.interactive_elements)} elements")

        # Display first few elements
        for i, elem in enumerate(tree_state.interactive_elements[:3]):
            print(f"\n  Element {i + 1}: {elem.name}")
            print(f"    Coords: ({elem.coordinates.x}, {elem.coordinates.y})")
            print(f"    Bounds: ({elem.bounding_box.x1}, {elem.bounding_box.y1}) to ({elem.bounding_box.x2}, {elem.bounding_box.y2})")

        # Test phone state
        print("\n[2] Getting phone state through adapter...")
        phone_state = adapter.get_phone_state()
        print(f"[OK] Phone state retrieved")
        print(f"  Package: {phone_state['packageName']}")
        print(f"  Keyboard: {phone_state['keyboardVisible']}")

        # Test apps list
        print("\n[3] Getting installed apps...")
        apps = adapter.get_installed_apps()
        user_apps = [a for a in apps if not a['isSystemApp']]
        print(f"[OK] Got {len(apps)} total packages ({len(user_apps)} user apps)")

        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mobile_integration():
    """Test Mobile class with MCP Helper integration"""
    print("\n" + "=" * 60)
    print("TEST 3: Mobile Class Integration")
    print("=" * 60)

    try:
        # Test with MCP Helper enabled (default)
        print("\n[1] Initializing Mobile with MCP Helper enabled...")
        mobile = Mobile(device="emulator-5554", use_mcp_helper=True)
        print(f"[OK] Mobile initialized")
        print(f"  MCP Helper enabled: {mobile.use_mcp_helper}")
        if mobile.mcp_adapter:
            print(f"  MCP Helper ready: Yes")
        else:
            print(f"  MCP Helper ready: No (will use fallback)")

        # Test get_state without vision
        print("\n[2] Getting device state (without vision)...")
        state = mobile.get_state(use_vision=False)
        print(f"[OK] Got state")
        print(f"  Interactive elements: {len(state.tree_state.interactive_elements)}")
        print(f"  Screenshot: {state.screenshot is not None}")

        # Test get_state with vision
        print("\n[3] Getting device state (with annotated screenshot)...")
        state_vision = mobile.get_state(use_vision=True)
        print(f"[OK] Got state with vision")
        print(f"  Interactive elements: {len(state_vision.tree_state.interactive_elements)}")
        print(f"  Screenshot: {state_vision.screenshot is not None}")
        if state_vision.screenshot:
            print(f"  Screenshot size: {len(state_vision.screenshot)} bytes")

        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """Compare performance: MCP Helper vs UIAutomator"""
    print("\n" + "=" * 60)
    print("TEST 4: Performance Comparison")
    print("=" * 60)

    import time

    try:
        # Test MCP Helper speed
        print("\n[1] Testing MCP Helper speed...")
        mobile_mcp = Mobile(device="emulator-5554", use_mcp_helper=True)

        start = time.time()
        for _ in range(3):
            mobile_mcp.get_state(use_vision=False)
        mcp_time = time.time() - start
        mcp_avg = mcp_time / 3

        print(f"[OK] MCP Helper: {mcp_time:.2f}s for 3 calls ({mcp_avg:.2f}s average)")

        # Test UIAutomator speed
        print("\n[2] Testing UIAutomator speed (fallback)...")
        mobile_ui = Mobile(device="emulator-5554", use_mcp_helper=False)

        start = time.time()
        for _ in range(3):
            mobile_ui.get_state(use_vision=False)
        ui_time = time.time() - start
        ui_avg = ui_time / 3

        print(f"[OK] UIAutomator: {ui_time:.2f}s for 3 calls ({ui_avg:.2f}s average)")

        # Calculate speedup
        if ui_avg > 0:
            speedup = ui_avg / mcp_avg
            print(f"\n📊 MCP Helper is {speedup:.1f}x faster than UIAutomator")

        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MCP Helper Integration Test Suite")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Direct MCP Helper", test_mcp_helper_direct()))
    results.append(("Adapter Layer", test_adapter()))
    results.append(("Mobile Integration", test_mobile_integration()))
    results.append(("Performance", test_performance()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n[OK] All tests passed!")
        return 0
    else:
        print("\n[FAIL] Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
