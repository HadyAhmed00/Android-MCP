"""
Auto-generated test script: search_football_on_google
Generated: 2025-12-06T09:45:52.595047
Total actions: 8
"""

import uiautomator2 as u2
import time

def run_test(device=None):
    """Run the recorded test sequence."""
    if device is None:
        device = u2.connect()
    

    # Action 1: Click at (741, 1862)
    device.click(741, 1862)
    time.sleep(16.9)

    # Action 2: Wait 2 seconds
    time.sleep(2)
    time.sleep(37.0)

    # Action 3: Click at (471, 766)
    device.click(471, 766)
    time.sleep(23.1)

    # Action 4: Wait 1 seconds
    time.sleep(1)
    time.sleep(46.9)

    # Action 5: Type "Football"
    device.send_keys("Football")
    time.sleep(28.3)

    # Action 6: Wait 1 seconds
    time.sleep(1)
    time.sleep(31.1)

    # Action 7: Press ENTER button
    device.press("ENTER")
    time.sleep(22.9)

    # Action 8: Wait 3 seconds
    time.sleep(3)

if __name__ == "__main__":
    run_test()