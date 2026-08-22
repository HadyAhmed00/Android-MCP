from dataclasses import dataclass
from typing import Literal, Optional

from android_mcp.tree.views import TreeState


@dataclass
class App:
    name:str
    status:Literal['Maximized','Minimized']


@dataclass
class DeviceContext:
    current_app: str = ""
    current_activity: str = ""
    keyboard_visible: bool = False
    screen_width: int = 0
    screen_height: int = 0

    def to_string(self) -> str:
        lines = ["--- Device Context ---"]
        if self.current_app:
            lines.append(f"App: {self.current_app} | Activity: {self.current_activity}")
        lines.append(f"Screen: {self.screen_width}x{self.screen_height} | Keyboard: {'visible' if self.keyboard_visible else 'hidden'}")
        return '\n'.join(lines)


@dataclass
class MobileState:
    tree_state: TreeState
    screenshot: bytes | None
    device_context: Optional[DeviceContext] = None
