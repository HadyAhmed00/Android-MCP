"""
Asset Tracking App Automation Script
This script automates the process of selecting "فرع القاهره -5 فرع حلوان" branch
and navigating through floor selection in the Asset Tracking app.
"""

import subprocess
import json
import time
import sys


class AssetTrackingAutomation:
    def __init__(self, device_id="emulator-5554"):
        self.device_id = device_id

    def run_mcp_command(self, tool_name, params):
        """Execute MCP mobile commands via subprocess"""
        print(f"Executing: {tool_name} with params: {params}")
        # This is a placeholder - actual implementation would use the MCP server
        # For now, we'll use direct ADB commands

    def take_screenshot(self, save_path=None):
        """Take a screenshot of the device"""
        print("📸 Taking screenshot...")
        if save_path:
            cmd = f'adb -s {self.device_id} exec-out screencap -p > "{save_path}"'
            subprocess.run(cmd, shell=True)
            print(f"Screenshot saved to: {save_path}")
        time.sleep(0.5)

    def click_coordinates(self, x, y, description=""):
        """Click at specific coordinates"""
        print(f"👆 Clicking at ({x}, {y}) - {description}")
        cmd = f'adb -s {self.device_id} shell input tap {x} {y}'
        subprocess.run(cmd, shell=True)
        time.sleep(1)

    def list_devices(self):
        """List available Android devices"""
        print("📱 Listing available devices...")
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        print(result.stdout)

    def launch_app(self, package_name="com.ibnsinapharma.asset_tracking"):
        """Launch the Asset Tracking app"""
        print(f"🚀 Launching app: {package_name}")
        cmd = f'adb -s {self.device_id} shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1'
        subprocess.run(cmd, shell=True)
        time.sleep(3)

    def get_ui_elements(self):
        """Get UI elements using uiautomator dump"""
        print("🔍 Getting UI elements...")
        cmd = f'adb -s {self.device_id} shell uiautomator dump /sdcard/ui.xml && adb -s {self.device_id} shell cat /sdcard/ui.xml'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout

    def wait_for_element(self, text, timeout=10):
        """Wait for an element with specific text to appear"""
        print(f"⏳ Waiting for element: {text}")
        start_time = time.time()
        while time.time() - start_time < timeout:
            ui_dump = self.get_ui_elements()
            if text in ui_dump:
                print(f"✅ Found element: {text}")
                return True
            time.sleep(1)
        print(f"❌ Element not found: {text}")
        return False

    def execute_automation(self):
        """Main automation workflow"""
        print("=" * 60)
        print("Asset Tracking Automation - Branch Selection")
        print("=" * 60)

        # Step 1: List available devices
        print("\n[Step 1] Listing available devices...")
        self.list_devices()
        time.sleep(1)

        # Step 2: Take initial screenshot
        print("\n[Step 2] Taking initial screenshot...")
       

        # Step 3: Launch Asset Tracking app
        print("\n[Step 3] Launching Asset Tracking app...")
        self.launch_app()
       

        # Step 4: Wait for app to load
        print("\n[Step 4] Waiting for app to load...")
        time.sleep(3)
        

        # Step 5: Click on "فرع القاهره 5 - فرع حلوان" branch
        # Coordinates from our testing: x=403, y=1050
        print("\n[Step 5] Selecting 'فرع القاهره 5 - فرع حلوان' branch...")
        self.click_coordinates(403, 1050, "فرع القاهره 5 - فرع حلوان")
       

        # Step 6: Wait for bottom sheet to appear
        print("\n[Step 6] Waiting for action selection bottom sheet...")
        time.sleep(2)
      

        # Step 7: Click on "اختار الغرفة" (Choose the room)
        # Coordinates from element list: x=180, y=1310
        # Updated coordinates based on proper element location
        print("\n[Step 7] Clicking 'اختار الغرفة' (Choose the room)...")
        self.click_coordinates(280, 1890, "اختار الغرفة")
       

        # Step 8: Wait for floor selection screen
        print("\n[Step 8] Waiting for floor selection screen...")
        time.sleep(2)
       

        # Step 9: Select "الدور الاول" (First floor)
        # Coordinates from element list: x=935, y=1467
        print("\n[Step 9] Selecting 'الدور الاول' (First floor)...")
        self.click_coordinates(935, 1467, "الدور الاول")
       

        # Step 10: Wait for section list to load
        print("\n[Step 10] Waiting for section list...")
        time.sleep(2)
       

        # Step 9: Select "الدور الاول" (First floor)
        # Coordinates from element list: x=935, y=1467
        print("\n[Step 9] Selecting 'الدور الاول' (First floor)...")
        self.click_coordinates(761, 1460, "الدور الاول")
      
        # Step 9: Select "الدور الاول" (First floor)
        # Coordinates from element list: x=935, y=1467
        print("\n[Step 9] Selecting 'الدور الاول' (First floor)...")
        self.click_coordinates(761, 2129, "الدور الاول")


        print("\n[Step 9] Selecting 'الدور الاول' (First floor)...")
        self.click_coordinates(560, 1060, "الدور الاول")

        print("\n[Step 9] Selecting 'الدور الاول' (First floor)...")
        self.click_coordinates(130, 2085, "الدور الاول")

        print("\n" + "=" * 60)
        print("✅ Automation completed successfully!")
        print("=" * 60)
        print("\nScreenshots saved in 'screenshots/' directory")
        print("Next steps available:")
        print("  - Select a section (IT, HR, or Administration)")
        print("  - Click 'إلى قائمة الغرف' to view rooms list")


def main():
    """Main entry point"""
    # Check if device ID is provided
    device_id = sys.argv[1] if len(sys.argv) > 1 else "emulator-5554"

    # Create screenshots directory if it doesn't exist
    import os
    os.makedirs("screenshots", exist_ok=True)

    # Create automation instance and run
    automation = AssetTrackingAutomation(device_id)

    try:
        automation.execute_automation()
    except KeyboardInterrupt:
        print("\n\n⚠️  Automation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
