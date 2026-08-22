"""
Adapter layer to integrate MCP Helper Content Provider with existing Android-MCP code.
This module provides compatibility layer that converts MCP Helper responses to the
expected Tree and Mobile state formats.
"""

from dataclasses import dataclass
from typing import List

from android_mcp.mcp_helper import A11yFullNode, A11yTreeNode, MCPHelperClient
from android_mcp.tree.views import BoundingBox, CenterCord, ElementNode, TreeState, classify_element


@dataclass
class MCPHelperTreeAdapter:
    """Adapter to convert MCP Helper tree responses to existing TreeState format"""

    mcp_client: MCPHelperClient

    def get_tree_state(self) -> TreeState:
        """Get state using MCP Helper Content Provider

        Converts the simplified a11y_tree response to TreeState format.
        Much faster than UIAutomator dump as it's in-process.

        Returns:
            TreeState with interactive elements
        """
        try:
            # Get filtered accessibility tree from MCP Helper
            tree_nodes = self.mcp_client.get_a11y_tree()
            interactive_elements = self._flatten_nodes_to_elements(tree_nodes)
            return TreeState(interactive_elements=interactive_elements)
        except Exception as e:
            raise RuntimeError(f"Failed to get tree state from MCP Helper: {e}")

    def get_tree_state_full(self) -> TreeState:
        """Get full state using MCP Helper with complete node properties

        Converts the full a11y_tree_full response to TreeState format.
        Provides more detailed information about each element.

        Returns:
            TreeState with fully detailed elements
        """
        try:
            # Get full accessibility tree from MCP Helper
            root = self.mcp_client.get_a11y_tree_full(include_small=True)
            interactive_elements = self._flatten_full_nodes_to_elements([root])
            return TreeState(interactive_elements=interactive_elements)
        except Exception as e:
            raise RuntimeError(f"Failed to get full tree state from MCP Helper: {e}")

    @staticmethod
    def _flatten_nodes_to_elements(nodes: List[A11yTreeNode]) -> List[ElementNode]:
        """Recursively flatten A11yTreeNode hierarchy to ElementNode list

        Args:
            nodes: List of accessibility tree nodes

        Returns:
            Flattened list of ElementNode objects
        """
        elements = []
        for node in nodes:
            # Create ElementNode from A11yTreeNode
            bounds = node.get_bounds()
            center = node.get_center_coords()

            element = ElementNode(
                name=node.text or node.className,
                coordinates=CenterCord(x=center[0], y=center[1]),
                bounding_box=BoundingBox(
                    x1=bounds.x1,
                    y1=bounds.y1,
                    x2=bounds.x2,
                    y2=bounds.y2
                ),
                element_type=classify_element(node.className),
                element_class=node.className,
            )
            elements.append(element)

            # Recursively process children
            if node.children:
                elements.extend(
                    MCPHelperTreeAdapter._flatten_nodes_to_elements(node.children)
                )

        return elements

    @staticmethod
    def _flatten_full_nodes_to_elements(nodes: List[A11yFullNode]) -> List[ElementNode]:
        """Recursively flatten A11yFullNode hierarchy to ElementNode list

        Args:
            nodes: List of full accessibility nodes

        Returns:
            Flattened list of ElementNode objects
        """
        elements = []
        for node in nodes:
            # Only include interactive elements
            if not (node.isClickable or node.isLongClickable or node.isFocusable):
                # Still process children even if parent isn't interactive
                if node.children:
                    elements.extend(
                        MCPHelperTreeAdapter._flatten_full_nodes_to_elements(node.children)
                    )
                continue

            # Skip non-visible or disabled elements
            if not (node.isVisibleToUser and node.isEnabled):
                if node.children:
                    elements.extend(
                        MCPHelperTreeAdapter._flatten_full_nodes_to_elements(node.children)
                    )
                continue

            bounds = node.boundsInScreen
            center = node.get_center_coords()

            # Use contentDescription or text as name, fallback to className
            name = (
                node.contentDescription
                or node.text
                or node.className.split(".")[-1]
            )

            element = ElementNode(
                name=name,
                coordinates=CenterCord(x=center[0], y=center[1]),
                bounding_box=BoundingBox(
                    x1=bounds["left"],
                    y1=bounds["top"],
                    x2=bounds["right"],
                    y2=bounds["bottom"]
                ),
                element_type=classify_element(node.className),
                element_class=node.className,
            )
            elements.append(element)

            # Recursively process children
            if node.children:
                elements.extend(
                    MCPHelperTreeAdapter._flatten_full_nodes_to_elements(node.children)
                )

        return elements


class MCPHelperMobileAdapter:
    """Adapter to integrate MCP Helper with Mobile class for state retrieval

    This adapter allows the existing Mobile.get_state() method to use
    the faster Content Provider approach instead of UIAutomator dump.
    """

    def __init__(self, mcp_client: MCPHelperClient):
        """Initialize adapter with MCP Helper client

        Args:
            mcp_client: MCPHelperClient instance for communication
        """
        self.mcp_client = mcp_client
        self.tree_adapter = MCPHelperTreeAdapter(mcp_client)

    def get_state_tree(self) -> TreeState:
        """Get device state tree using MCP Helper

        Returns:
            TreeState with interactive elements from device
        """
        return self.tree_adapter.get_tree_state()

    def get_state_tree_full(self) -> TreeState:
        """Get full device state tree using MCP Helper with complete properties

        Returns:
            TreeState with fully detailed interactive elements
        """
        return self.tree_adapter.get_tree_state_full()

    def get_phone_state(self) -> dict:
        """Get phone state (current app, keyboard visibility, etc.)

        Returns:
            Dict with packageName, activityName, keyboardVisible, etc.
        """
        phone_state = self.mcp_client.get_phone_state()
        return {
            "packageName": phone_state.packageName,
            "activityName": phone_state.activityName,
            "keyboardVisible": phone_state.keyboardVisible,
            "isEditable": phone_state.isEditable,
            "focusedElement": phone_state.focusedElement
        }

    def get_installed_apps(self) -> List[dict]:
        """Get list of installed apps

        Returns:
            List of dicts with app info
        """
        apps = self.mcp_client.get_packages()
        return [
            {
                "packageName": app.packageName,
                "label": app.label,
                "versionName": app.versionName,
                "versionCode": app.versionCode,
                "isSystemApp": app.isSystemApp
            }
            for app in apps
        ]
