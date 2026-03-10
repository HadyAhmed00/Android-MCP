# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Android-MCP is a Python MCP (Model Context Protocol) server that bridges AI agents and Android devices. It exposes tools for UI interaction (click, swipe, type, drag), device state inspection via UI hierarchy parsing, annotated screenshot generation, test recording/export, and Azure DevOps bug reporting.

## Commands

```bash
# Run the MCP server (emulator)
python main.py --emulator

# Run the MCP server (physical device)
python main.py

# Run with a specific device ID
python main.py --device <device-id>

# Install dependencies
pip install -e .
```

Uses `uv` for dependency management (see `uv.lock`). Python 3.12+ required (`.python-version` specifies 3.13).

## Architecture

**Entry point:** `main.py` — Creates a `FastMCP` server, defines all MCP tools (16 total), and wires up device interaction via direct ADB shell commands. The `TestRecorder` is instantiated here for recording sessions.

**Two device interaction backends with automatic fallback:**

1. **MCP Helper (preferred):** `src/mcp_helper.py` (`MCPHelperClient`) communicates with the DroidRun Portal Android app (`com.droidrun.portal`) via ADB content provider queries. Faster than UIAutomator. `src/mcp_helper_adapter.py` converts MCP Helper responses to the internal `TreeState` format.

2. **UIAutomator2 fallback:** `src/tree/__init__.py` (`Tree` class) uses `uiautomator2` to dump and parse Android XML hierarchy. Falls back here after 3 consecutive MCP Helper failures.

**`src/mobile/__init__.py` (`Mobile` class):** Central device manager. Handles lazy connection, state caching (0.5s TTL), backend selection (MCP Helper → UIAutomator2 fallback), and screenshot capture via ADB `screencap`.

**Data flow for state retrieval:**
`main.py:state_tool` → `Mobile.get_state()` → tries `MCPHelperMobileAdapter.get_state_tree()` → falls back to `Tree.get_state()` → returns `MobileState(tree_state, screenshot)`

**`src/tree/`:** Parses UI hierarchy into `ElementNode` objects with center coordinates and bounding boxes. `config.py` defines `INTERACTIVE_CLASSES` for element filtering. `views.py` holds data classes (`TreeState`, `ElementNode`, `CenterCord`, `BoundingBox`).

**`src/recorder.py` (`TestRecorder`):** Records actions during tool execution and exports as Python (ADB-based or uiautomator2-based), JSON, or human-readable format.

## Key Conventions

- Device interaction tools in `main.py` use direct ADB commands (`adb shell input tap/swipe/keyevent`) rather than uiautomator2, to avoid accessibility service conflicts.
- All tool functions record actions via `recorder.record_action()` for test recording support.
- `Mobile` class uses lazy initialization — device connection and MCP Helper init happen on first use, not at construction.
- Do not build the project unless explicitly told to do so.
