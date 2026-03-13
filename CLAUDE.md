# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Android-MCP is a Python MCP (Model Context Protocol) server that bridges AI agents and Android devices. It exposes tools for UI interaction (click, swipe, type, drag), device state inspection via UI hierarchy parsing, annotated screenshot generation, test recording/export, and Azure DevOps bug reporting.

## Requirements

- Python 3.12+ (`.python-version` specifies 3.13)
- ADB (Android Debug Bridge) installed and in PATH
- Android device or emulator connected via ADB

## Commands

```bash
# Run the MCP server (emulator — connects to emulator-5554)
python main.py --emulator

# Run the MCP server (physical device, auto-detect)
python main.py

# Run with a specific device ID
python main.py --device <device-id>

# Install dependencies (uv - preferred)
uv sync

# Install dependencies (pip)
pip install -e .
```

Uses `uv` for dependency management (see `uv.lock`).

## MCP Client Configuration

```json
{
  "mcpServers": {
    "android-mcp": {
      "command": "python",
      "args": ["/path/to/Android-MCP/main.py", "--emulator"]
    }
  }
}
```

## Architecture

**Entry point:** `main.py` — Creates a `FastMCP` server, defines all MCP tools (16 total), and wires up device interaction via direct ADB shell commands. The `TestRecorder` is instantiated here for recording sessions. **Note:** stderr is suppressed at import time to prevent library warnings from breaking the MCP protocol. To debug import issues, uncomment the `sys.stderr = _original_stderr` line in `main.py`.

**Two device interaction backends with automatic fallback:**

1. **MCP Helper (preferred):** `src/mcp_helper.py` (`MCPHelperClient`) communicates with the DroidRun Portal Android app (`com.droidrun.portal`) via ADB content provider queries. Faster than UIAutomator. `src/mcp_helper_adapter.py` has two adapters: `MCPHelperTreeAdapter` (low-level, converts nodes to `TreeState`) and `MCPHelperMobileAdapter` (high-level, used by `Mobile`).

2. **UIAutomator2 fallback:** `src/tree/__init__.py` (`Tree` class) uses `uiautomator2` to dump and parse Android XML hierarchy. Falls back here after 3 consecutive MCP Helper failures.

**`src/mobile/__init__.py` (`Mobile` class):** Central device manager. Handles lazy connection, state caching (0.5s TTL), backend selection (MCP Helper → UIAutomator2 fallback), and screenshot capture via ADB `screencap`.

**Data flow for state retrieval:**
`main.py:state_tool` → `Mobile.get_state()` → tries `MCPHelperMobileAdapter.get_state_tree()` → falls back to `Tree.get_state()` → returns `MobileState(tree_state, screenshot)`

**`src/tree/`:** Parses UI hierarchy into `ElementNode` objects with center coordinates and bounding boxes. `config.py` defines `INTERACTIVE_CLASSES` for element filtering. `views.py` holds data classes (`TreeState`, `ElementNode`, `CenterCord`, `BoundingBox`). `TreeState.to_string()` outputs one line per element: `Label: <index> Name: <name> Coordinates: (<x>,<y>)`.

**`src/recorder.py` (`TestRecorder`):** Records actions during tool execution and exports as Python (ADB-based or uiautomator2-based), JSON, or human-readable format. The `export_as_python` method defaults to `use_adb=True`, producing self-contained scripts with no external dependencies.

**Azure DevOps bug reporting:** Two tools exist — `Report-Bug-To-Azure` (safe: generates an `az boards` CLI command string for manual execution) and `Report-Bug-To-Azure-Direct` (experimental: executes the command directly, may hang). Both map to these custom board fields: `Custom.DescriptionorSteps` (steps + description), `Microsoft.VSTS.TCM.ReproSteps` (actual result), `Microsoft.VSTS.TCM.SystemInfo` (expected result).

## Key Conventions

- Device interaction tools in `main.py` use direct ADB commands (`adb shell input tap/swipe/keyevent`) rather than uiautomator2, to avoid accessibility service conflicts. `Press-Tool` accepts: `home`, `back`, `menu`, `power`, `volume_up`, `volume_down`, `enter`, `delete` (or any raw keycode string).
- All tool functions record actions via `recorder.record_action()` for test recording support.
- `Mobile` class uses lazy initialization — device connection and MCP Helper init happen on first use, not at construction.
- `MCPHelperClient` also supports write operations via ADB content `insert` (keyboard input, overlay config) in addition to `query` for state reads.
- Do not build the project unless explicitly told to do so.
