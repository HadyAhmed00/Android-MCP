"""
MCP Helper Content Provider Integration
Provides fast, efficient access to Android device state via Content Provider
instead of the slower UIAutomator XML dump mechanism.
"""

import json
import subprocess
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from enum import Enum


class ContentProviderEndpoint(Enum):
    """Available MCP Helper Content Provider endpoints"""
    PING = "ping"
    VERSION = "version"
    A11Y_TREE = "a11y_tree"
    A11Y_TREE_FULL = "a11y_tree_full"
    PHONE_STATE = "phone_state"
    STATE = "state"
    STATE_FULL = "state_full"
    PACKAGES = "packages"
    KEYBOARD_INPUT = "keyboard/input"
    KEYBOARD_CLEAR = "keyboard/clear"
    KEYBOARD_KEY = "keyboard/key"
    OVERLAY_OFFSET = "overlay_offset"
    OVERLAY_VISIBLE = "overlay_visible"
    SOCKET_PORT = "socket_port"


@dataclass
class Bounds:
    """Represents bounds as "x1, y1, x2, y2" string"""
    x1: int
    y1: int
    x2: int
    y2: int

    @classmethod
    def from_string(cls, bounds_str: str) -> "Bounds":
        """Parse bounds from "x1, y1, x2, y2" format"""
        coords = [int(x.strip()) for x in bounds_str.split(",")]
        return cls(coords[0], coords[1], coords[2], coords[3])

    def to_dict(self) -> Dict[str, int]:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass
class BoundsInScreen:
    """Represents bounds in screen coordinates"""
    left: int
    top: int
    right: int
    bottom: int

    def to_dict(self) -> Dict[str, int]:
        return {"left": self.left, "top": self.top, "right": self.right, "bottom": self.bottom}


@dataclass
class A11yTreeNode:
    """Simplified accessibility tree node (from a11y_tree endpoint)"""
    index: int
    resourceId: str
    className: str
    text: str
    bounds: str  # "x1, y1, x2, y2" format
    children: List["A11yTreeNode"]

    def get_bounds(self) -> Bounds:
        return Bounds.from_string(self.bounds)

    def get_center_coords(self) -> tuple[int, int]:
        bounds = self.get_bounds()
        return ((bounds.x1 + bounds.x2) // 2, (bounds.y1 + bounds.y2) // 2)


@dataclass
class A11yFullNode:
    """Full accessibility node info (from a11y_tree_full endpoint)"""
    resourceId: str
    className: str
    packageName: str
    text: str
    contentDescription: str
    isClickable: bool
    isLongClickable: bool
    isFocusable: bool
    isFocused: bool
    isEnabled: bool
    isVisibleToUser: bool
    isEditable: bool
    boundsInScreen: Dict[str, int]
    actionList: List[Dict[str, Any]]
    children: List["A11yFullNode"]

    def get_center_coords(self) -> tuple[int, int]:
        bounds = self.boundsInScreen
        return (
            (bounds["left"] + bounds["right"]) // 2,
            (bounds["top"] + bounds["bottom"]) // 2
        )


@dataclass
class PhoneState:
    """Current phone state"""
    packageName: str
    activityName: str
    keyboardVisible: bool
    isEditable: bool
    focusedElement: Dict[str, str]


@dataclass
class DeviceContext:
    """Device context information"""
    screen_bounds: Dict[str, int]
    filtering_params: Dict[str, Any]
    display_metrics: Dict[str, Any]


@dataclass
class AppInfo:
    """Installed app information"""
    packageName: str
    label: str
    versionName: str
    versionCode: int
    isSystemApp: bool


class MCPHelperClient:
    """Client for communicating with MCP Helper Content Provider"""

    PROVIDER_AUTHORITY = "com.HadyAhmed00.MCP_Helper"

    def __init__(self, device_id: Optional[str] = None):
        """Initialize MCP Helper client

        Args:
            device_id: ADB device ID (e.g., 'emulator-5554'). If None, uses default device.
        """
        self.device_id = device_id
        self._cache = {}

    def _build_uri(self, endpoint: str, filters: Optional[Dict[str, str]] = None) -> str:
        """Build content provider URI"""
        uri = f"content://{self.PROVIDER_AUTHORITY}/{endpoint}"
        if filters:
            params = "&".join(f"{k}={v}" for k, v in filters.items())
            uri += f"?{params}"
        return uri

    def _execute_query(self, uri: str) -> Dict[str, Any]:
        """Execute content query and return parsed JSON

        Args:
            uri: Content provider URI

        Returns:
            Parsed response dict with 'status' and 'data' fields
        """
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(["shell", "content", "query", "--uri", uri])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore')
            if result.returncode != 0:
                raise RuntimeError(f"ADB query failed: {result.stderr}")

            # Parse "Row: 0 result={...}" format
            output = (result.stdout or "").strip()
            if not output.startswith("Row: 0 result="):
                raise ValueError(f"Unexpected output format: {output}")

            json_str = output.replace("Row: 0 result=", "", 1)
            return json.loads(json_str)

        except subprocess.TimeoutExpired:
            raise TimeoutError("Content query timed out")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")

    def ping(self) -> bool:
        """Test connection to MCP Helper app"""
        uri = self._build_uri(ContentProviderEndpoint.PING.value)
        response = self._execute_query(uri)
        return response.get("status") == "success" and response.get("data") == "pong"

    def get_version(self) -> str:
        """Get MCP Helper app version"""
        uri = self._build_uri(ContentProviderEndpoint.VERSION.value)
        response = self._execute_query(uri)
        if response.get("status") != "success":
            raise RuntimeError("Failed to get version")
        return response.get("data", "unknown")

    def get_a11y_tree(self) -> List[A11yTreeNode]:
        """Get filtered accessibility tree with overlay indices

        Returns:
            List of A11yTreeNode objects representing the UI hierarchy
        """
        uri = self._build_uri(ContentProviderEndpoint.A11Y_TREE.value)
        response = self._execute_query(uri)
        if response.get("status") != "success":
            raise RuntimeError("Failed to get a11y_tree")

        data = json.loads(response.get("data", "[]"))
        return self._parse_a11y_tree_nodes(data)

    def get_a11y_tree_full(self, include_small: bool = True) -> A11yFullNode:
        """Get full accessibility tree with complete node properties

        Args:
            include_small: If False, filters out elements < 1% visibility

        Returns:
            Root A11yFullNode with complete hierarchy
        """
        endpoint = ContentProviderEndpoint.A11Y_TREE_FULL.value
        filters = {} if include_small else {"filter": "false"}
        uri = self._build_uri(endpoint, filters)
        response = self._execute_query(uri)
        if response.get("status") != "success":
            raise RuntimeError("Failed to get a11y_tree_full")

        data = json.loads(response.get("data", "{}"))
        return self._parse_a11y_full_node(data)

    def get_phone_state(self) -> PhoneState:
        """Get current phone state (app, activity, keyboard, etc.)

        Returns:
            PhoneState object with current state info
        """
        uri = self._build_uri(ContentProviderEndpoint.PHONE_STATE.value)
        response = self._execute_query(uri)
        if response.get("status") != "success":
            raise RuntimeError("Failed to get phone_state")

        data = json.loads(response.get("data", "{}"))
        return PhoneState(
            packageName=data.get("packageName", ""),
            activityName=data.get("activityName", ""),
            keyboardVisible=data.get("keyboardVisible", False),
            isEditable=data.get("isEditable", False),
            focusedElement=data.get("focusedElement", {})
        )

    def get_state(self, include_full_tree: bool = False) -> Dict[str, Any]:
        """Get combined state (tree + phone state)

        Args:
            include_full_tree: If True, returns full accessibility info; if False, returns simplified tree

        Returns:
            Dict with 'a11y_tree' and 'phone_state' keys
        """
        endpoint = ContentProviderEndpoint.STATE.value if not include_full_tree else ContentProviderEndpoint.STATE_FULL.value
        uri = self._build_uri(endpoint)
        response = self._execute_query(uri)
        if response.get("status") != "success":
            raise RuntimeError("Failed to get state")

        data = json.loads(response.get("data", "{}"))
        return data

    def get_packages(self) -> List[AppInfo]:
        """Get list of installed launchable apps

        Returns:
            List of AppInfo objects for installed apps
        """
        uri = self._build_uri(ContentProviderEndpoint.PACKAGES.value)
        response = self._execute_query(uri)
        if response.get("status") != "success":
            raise RuntimeError("Failed to get packages")

        packages_data = response.get("packages", [])
        return [
            AppInfo(
                packageName=pkg.get("packageName", ""),
                label=pkg.get("label", ""),
                versionName=pkg.get("versionName", ""),
                versionCode=pkg.get("versionCode", 0),
                isSystemApp=pkg.get("isSystemApp", False)
            )
            for pkg in packages_data
        ]

    def keyboard_input(self, text: str, clear: bool = True) -> bool:
        """Send text input to focused input field

        Args:
            text: Text to input (will be base64 encoded)
            clear: If True, clears field first

        Returns:
            True if successful
        """
        import base64
        base64_text = base64.b64encode(text.encode()).decode()
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend([
            "shell", "content", "insert",
            "--uri", f"content://{self.PROVIDER_AUTHORITY}/keyboard/input",
            "--bind", f"base64_text:s:{base64_text}"
        ])
        if not clear:
            cmd.extend(["--bind", "clear:b:false"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            raise TimeoutError("Keyboard input timed out")

    def keyboard_clear(self) -> bool:
        """Clear text in focused input field

        Returns:
            True if successful
        """
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend([
            "shell", "content", "insert",
            "--uri", f"content://{self.PROVIDER_AUTHORITY}/keyboard/clear"
        ])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            raise TimeoutError("Keyboard clear timed out")

    def keyboard_key(self, key_code: int) -> bool:
        """Send key event via keyboard

        Args:
            key_code: Android key code (e.g., 66=Enter, 67=Backspace, 4=Back)

        Returns:
            True if successful
        """
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend([
            "shell", "content", "insert",
            "--uri", f"content://{self.PROVIDER_AUTHORITY}/keyboard/key",
            "--bind", f"key_code:i:{key_code}"
        ])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            raise TimeoutError("Keyboard key event timed out")

    def set_overlay_offset(self, offset_pixels: int) -> bool:
        """Set overlay vertical offset

        Args:
            offset_pixels: Vertical offset in pixels

        Returns:
            True if successful
        """
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend([
            "shell", "content", "insert",
            "--uri", f"content://{self.PROVIDER_AUTHORITY}/overlay_offset",
            "--bind", f"offset:i:{offset_pixels}"
        ])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            raise TimeoutError("Overlay offset timed out")

    def set_overlay_visible(self, visible: bool) -> bool:
        """Toggle overlay visibility

        Args:
            visible: True to show, False to hide

        Returns:
            True if successful
        """
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend([
            "shell", "content", "insert",
            "--uri", f"content://{self.PROVIDER_AUTHORITY}/overlay_visible",
            "--bind", f"visible:b:{str(visible).lower()}"
        ])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            raise TimeoutError("Overlay visibility timed out")

    def set_socket_port(self, port: int) -> bool:
        """Configure REST API socket server port

        Args:
            port: Port number (default: 8080)

        Returns:
            True if successful
        """
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend([
            "shell", "content", "insert",
            "--uri", f"content://{self.PROVIDER_AUTHORITY}/socket_port",
            "--bind", f"port:i:{port}"
        ])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            raise TimeoutError("Socket port configuration timed out")

    @staticmethod
    def _parse_a11y_tree_nodes(data: List[Dict]) -> List[A11yTreeNode]:
        """Recursively parse accessibility tree nodes"""
        nodes = []
        for item in data:
            children = item.get("children", [])
            node = A11yTreeNode(
                index=item.get("index", 0),
                resourceId=item.get("resourceId", ""),
                className=item.get("className", ""),
                text=item.get("text", ""),
                bounds=item.get("bounds", "0, 0, 0, 0"),
                children=MCPHelperClient._parse_a11y_tree_nodes(children)
            )
            nodes.append(node)
        return nodes

    @staticmethod
    def _parse_a11y_full_node(data: Dict) -> A11yFullNode:
        """Recursively parse full accessibility node"""
        children_data = data.get("children", [])
        children = [
            MCPHelperClient._parse_a11y_full_node(child) for child in children_data
        ]

        return A11yFullNode(
            resourceId=data.get("resourceId", ""),
            className=data.get("className", ""),
            packageName=data.get("packageName", ""),
            text=data.get("text", ""),
            contentDescription=data.get("contentDescription", ""),
            isClickable=data.get("isClickable", False),
            isLongClickable=data.get("isLongClickable", False),
            isFocusable=data.get("isFocusable", False),
            isFocused=data.get("isFocused", False),
            isEnabled=data.get("isEnabled", False),
            isVisibleToUser=data.get("isVisibleToUser", False),
            isEditable=data.get("isEditable", False),
            boundsInScreen=data.get("boundsInScreen", {}),
            actionList=data.get("actionList", []),
            children=children
        )
