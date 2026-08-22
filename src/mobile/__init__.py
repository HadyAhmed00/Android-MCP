from src.mobile.views import MobileState, DeviceContext
from src.tree import Tree
import uiautomator2 as u2
from io import BytesIO
from PIL import Image
import time
from typing import Optional
from src.mcp_helper import MCPHelperClient
from src.mcp_helper_adapter import MCPHelperMobileAdapter
import subprocess
import sys
import tempfile
import os

class Mobile:
    def __init__(self, device: str = None, use_mcp_helper: bool = True):
        self.device_id = device
        self.device = None
        self._state_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 0.5  # Cache valid for 0.5 seconds
        self._connection_attempted = False
        self.use_mcp_helper = use_mcp_helper
        self.mcp_adapter: Optional[MCPHelperMobileAdapter] = None
        self._mcp_initialized = False
        self._mcp_init_attempted = False
        self._mcp_error_count = 0  # Track consecutive MCP Helper errors
        self._mcp_max_consecutive_errors = 3  # Only disable after 3 consecutive errors
        self._screen_size: tuple[int, int] | None = None
        self._uia_state_cache = None  # Separate cache for UIAutomator path
        self._uia_cache_timestamp = 0
        self._last_device_context: Optional[DeviceContext] = None
    
    def _init_mcp_helper(self):
        """Lazy initialization of MCP Helper (only when first needed)"""
        if self._mcp_init_attempted or not self.use_mcp_helper:
            return

        self._mcp_init_attempted = True
        try:
            mcp_client = MCPHelperClient(device_id=self.device_id)
            # Use a shorter timeout for initial check
            if mcp_client.ping():
                self.mcp_adapter = MCPHelperMobileAdapter(mcp_client)
                self._mcp_initialized = True
            else:
                self.use_mcp_helper = False
        except Exception as e:
            self.use_mcp_helper = False

    def _ensure_connected(self):
        """Lazy connection - only connect when actually needed"""
        if self.device is not None:
            return
        
        if self._connection_attempted:
            raise ConnectionError(f"Device {self.device_id} is not connected. Please ensure an Android device or emulator is running and accessible via ADB.")
        
        self._connection_attempted = True
        try:
            self.device = u2.connect(self.device_id)
            self.device.info  # Verify connection works
        except u2.ConnectError as e:
            raise ConnectionError(f"Failed to connect to device {self.device_id}: {e}. Please ensure an Android device or emulator is running and accessible via ADB.")
        except Exception as e:
            raise RuntimeError(f"Unexpected error connecting to device {self.device_id}: {e}")

    def get_device(self):
        self._ensure_connected()
        return self.device

    def _get_screen_size(self) -> tuple[int, int]:
        """Get screen dimensions via ADB, cached after first call."""
        if self._screen_size is not None:
            return self._screen_size
        try:
            cmd = ["adb"]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            cmd.extend(["shell", "wm", "size"])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            # Parse "Physical size: 1080x1920"
            for line in result.stdout.strip().splitlines():
                if "size:" in line.lower():
                    size_str = line.split(":")[-1].strip()
                    w, h = size_str.split("x")
                    self._screen_size = (int(w), int(h))
                    return self._screen_size
        except Exception:
            pass
        self._screen_size = (0, 0)
        return self._screen_size

    def get_state(self, use_vision=False):
        try:
            # Lazy initialize MCP Helper on first use
            if self.use_mcp_helper and not self._mcp_initialized:
                self._init_mcp_helper()

            # Try MCP Helper first if available
            if self.use_mcp_helper and self.mcp_adapter:
                try:
                    # Check if cache is still valid
                    current_time = time.time()
                    if self._state_cache and (current_time - self._cache_timestamp) < self._cache_ttl:
                        tree_state = self._state_cache
                    else:
                        # Get state from MCP Helper (much faster than UIAutomator)
                        tree_state = self.mcp_adapter.get_state_tree()
                        self._state_cache = tree_state
                        self._cache_timestamp = current_time

                    # Success - reset error count
                    self._mcp_error_count = 0

                    # Build device context from MCP Helper phone state
                    try:
                        phone_state = self.mcp_adapter.get_phone_state()
                        sw, sh = self._get_screen_size()
                        device_context = DeviceContext(
                            current_app=phone_state.get("packageName", ""),
                            current_activity=phone_state.get("activityName", ""),
                            keyboard_visible=phone_state.get("keyboardVisible", False),
                            screen_width=sw,
                            screen_height=sh,
                        )
                    except Exception:
                        sw, sh = self._get_screen_size()
                        device_context = DeviceContext(screen_width=sw, screen_height=sh)

                    self._last_device_context = device_context

                    if use_vision:
                        # Do NOT call _ensure_connected() here — it starts uiautomator2's
                        # accessibility service which disconnects the DroidRun Portal.
                        # get_screenshot() uses ADB screencap directly, no u2 needed.
                        nodes = tree_state.interactive_elements
                        tree = Tree(self)
                        annotated_screenshot = tree.annotated_screenshot(nodes=nodes, scale=1.0)
                        screenshot = self.screenshot_in_bytes(annotated_screenshot)
                    else:
                        screenshot = None

                    return MobileState(tree_state=tree_state, screenshot=screenshot, device_context=device_context)
                except Exception as mcp_error:
                    # Increment error counter instead of permanently disabling
                    self._mcp_error_count += 1
                    error_msg = str(mcp_error)

                    if self._mcp_error_count >= self._mcp_max_consecutive_errors:
                        print(f"Warning: MCP Helper failed {self._mcp_error_count} times ({error_msg}). Switching to UIAutomator", file=sys.stderr)
                        self.use_mcp_helper = False
                    else:
                        print(f"Warning: MCP Helper temporary error ({self._mcp_error_count}/{self._mcp_max_consecutive_errors}): {error_msg}. Retrying...", file=sys.stderr)

            # Fallback to UIAutomator if MCP Helper unavailable
            self._ensure_connected()
            current_time = time.time()
            if self._uia_state_cache and (current_time - self._uia_cache_timestamp) < self._cache_ttl:
                tree_state = self._uia_state_cache
            else:
                tree = Tree(self)
                tree_state = tree.get_state()
                self._uia_state_cache = tree_state
                self._uia_cache_timestamp = current_time

            # Build device context with screen size and app/activity via ADB dumpsys
            sw, sh = self._get_screen_size()
            current_app = ""
            current_activity = ""
            try:
                cmd = ["adb"]
                if self.device_id:
                    cmd.extend(["-s", self.device_id])
                cmd.extend(["shell", "dumpsys activity activities"])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                for line in result.stdout.splitlines():
                    if "mCurrentFocus" in line or "mFocusedApp" in line:
                        # Parse "mCurrentFocus=Window{... pkg/activity}"
                        import re
                        match = re.search(r'(\S+)/(\S+)\}', line)
                        if match:
                            current_app = match.group(1)
                            current_activity = match.group(2)
                        break
            except Exception:
                pass
            device_context = DeviceContext(
                current_app=current_app,
                current_activity=current_activity,
                screen_width=sw,
                screen_height=sh,
            )
            self._last_device_context = device_context

            if use_vision:
                nodes = tree_state.interactive_elements
                tree = Tree(self)
                annotated_screenshot = tree.annotated_screenshot(nodes=nodes, scale=1.0)
                screenshot = self.screenshot_in_bytes(annotated_screenshot)
            else:
                screenshot = None

            return MobileState(tree_state=tree_state, screenshot=screenshot, device_context=device_context)
        except Exception as e:
            raise RuntimeError(f"Failed to get device state: {e}")
    
    def get_screenshot(self,scale:float=0.7)->Image.Image:
        try:
            # Use ADB screencap instead of uiautomator2 to avoid accessibility service conflict
            # Capture screenshot using ADB
            cmd = ["adb"]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            cmd.extend(["exec-out", "screencap", "-p"])

            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode != 0:
                raise RuntimeError(f"Screenshot capture failed: {result.stderr}")

            # Multi-display devices print a "[Warning] Multiple displays were found"
            # notice on stdout ahead of the PNG payload; drop anything before the
            # PNG magic bytes so PIL sees a clean stream.
            raw = result.stdout
            magic = bytes.fromhex("89504e470d0a1a0a")
            offset = raw.find(magic)
            if offset == -1:
                raise RuntimeError(f"Screenshot output is not a PNG: {raw[:200]!r}")
            raw = raw[offset:]

            # Load image directly from bytes (avoiding temp file issues on Windows)
            screenshot = Image.open(BytesIO(raw))
            if screenshot is None:
                raise ValueError("Screenshot capture returned None.")

            size = (int(screenshot.width * scale), int(screenshot.height * scale))
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

    