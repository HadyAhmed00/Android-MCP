from src.mobile.views import MobileState
from src.tree import Tree
import uiautomator2 as u2
from io import BytesIO
from PIL import Image
import time

class Mobile:
    def __init__(self,device:str=None):
        try:
            self.device = u2.connect(device)
            self.device.info
            self._state_cache = None
            self._cache_timestamp = 0
            self._cache_ttl = 0.5  # Cache valid for 0.5 seconds
        except u2.ConnectError as e:
            raise ConnectionError(f"Failed to connect to device {device}: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error connecting to device {device}: {e}")

    def get_device(self):
        return self.device

    def get_state(self,use_vision=False):
        try:
            # Check if cache is still valid
            current_time = time.time()
            if self._state_cache and (current_time - self._cache_timestamp) < self._cache_ttl:
                tree_state = self._state_cache
            else:
                # Parse fresh state
                tree = Tree(self)
                tree_state = tree.get_state()
                self._state_cache = tree_state
                self._cache_timestamp = current_time

            if use_vision:
                nodes=tree_state.interactive_elements
                tree = Tree(self)  # Need fresh tree for screenshot
                annotated_screenshot=tree.annotated_screenshot(nodes=nodes,scale=1.0)
                screenshot=self.screenshot_in_bytes(annotated_screenshot)
            else:
                screenshot=None
            return MobileState(tree_state=tree_state,screenshot=screenshot)
        except Exception as e:
            raise RuntimeError(f"Failed to get device state: {e}")
    
    def get_screenshot(self,scale:float=0.7)->Image.Image:
        try:
            screenshot=self.device.screenshot()
            if screenshot is None:
                raise ValueError("Screenshot capture returned None.")
            size=(screenshot.width*scale, screenshot.height*scale)
            screenshot.thumbnail(size=size, resample=Image.Resampling.LANCZOS)
            return screenshot
        except Exception as e:
            raise RuntimeError(f"Failed to get screenshot: {e}")
    
    def screenshot_in_bytes(self,screenshot:Image.Image)->bytes:
        try:
            if screenshot is None:
                raise ValueError("Screenshot is None")
            io=BytesIO()
            screenshot.save(io,format='PNG')
            bytes=io.getvalue()
            if len(bytes) == 0:
                raise ValueError("Screenshot conversion resulted in empty bytes.")
            return bytes
        except Exception as e:
            raise RuntimeError(f"Failed to convert screenshot to bytes: {e}")

    