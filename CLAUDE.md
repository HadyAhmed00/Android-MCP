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

### Tests

There is no test framework, linter, or CI config in this repo. The `test_*.py` files at the
repo root (`test_login_flow.py`, `test_filter_tasks.py`) are **generated artifacts** produced by
`Export-Test-Script`, not a hand-written suite. They are self-contained ADB scripts — do not
add pytest fixtures or conftest to them, and regenerate rather than hand-edit:

```bash
# Run a generated test directly (device id is an optional positional arg)
python test_login_flow.py
python test_login_flow.py emulator-5554
```

`pytest`-format exports define a `TestX` class plus a `run_test()` entry point, so they work
both under `pytest test_x.py` and as a plain script.

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

**Entry point:** `main.py` — Creates a `FastMCP` server, defines all MCP tools (17 at last count; `grep -c "@mcp.tool" main.py` to confirm), and wires up device interaction via direct ADB shell commands. `Mobile` and `TestRecorder` are module-level singletons instantiated here. **Note:** stderr is suppressed at import time to prevent library warnings from breaking the MCP protocol. To debug import issues, uncomment the `sys.stderr = _original_stderr` line in `main.py`.

Device selection precedence in `main.py`: `--device` > `--emulator` (→ `emulator-5554`) > `None` (uiautomator2 auto-detect). `adb_shell()` injects `-s <device_id>` when one is set; all device commands go through it with a 10s timeout.

**Two device interaction backends with automatic fallback:**

1. **MCP Helper (preferred):** `src/mcp_helper.py` (`MCPHelperClient`) communicates with the DroidRun Portal Android app (`io.github.hadyahmed00.portal`) via ADB content provider queries. Faster than UIAutomator. `src/mcp_helper_adapter.py` has two adapters: `MCPHelperTreeAdapter` (low-level, converts nodes to `TreeState`) and `MCPHelperMobileAdapter` (high-level, used by `Mobile`).

2. **UIAutomator2 fallback:** `src/tree/__init__.py` (`Tree` class) uses `uiautomator2` to dump and parse Android XML hierarchy. Falls back here after 3 consecutive MCP Helper failures (`_mcp_max_consecutive_errors`); a single failure only logs a warning and retries.

**`src/mobile/__init__.py` (`Mobile` class):** Central device manager. Handles lazy connection, backend selection, screen-size lookup, and screenshot capture via ADB `screencap`. It keeps **two separate 0.5s state caches** — `_state_cache` for the MCP Helper path and `_uia_state_cache` for the UIAutomator path — so switching backends does not serve stale trees.

**Data flow for state retrieval:**
`main.py:state_tool` → `Mobile.get_state()` → tries `MCPHelperMobileAdapter.get_state_tree()` → falls back to `Tree.get_state()` → returns `MobileState(tree_state, screenshot, device_context)`

**`src/tree/`:** Parses UI hierarchy into `ElementNode` objects with center coordinates and bounding boxes. `config.py` defines `INTERACTIVE_CLASSES` for element filtering. `views.py` holds data classes (`TreeState`, `ElementNode`, `CenterCord`, `BoundingBox`). `TreeState.to_string()` outputs one line per element: `Label: <index> Name: <name> Coordinates: (<x>,<y>)`.

**`src/mobile/views.py`:** `DeviceContext` (current app/activity, keyboard visibility, screen size) is prepended to every `State-Tool` response, ahead of an `--- Interactive Elements (N elements) ---` header.

**Label indices are positional and volatile:** `Click-By-Label(label)` re-reads state and indexes `tree_state.interactive_elements[label]`. Indices are only valid against the most recent `State-Tool` output; they shift whenever the screen changes.

**`src/recorder.py` (`TestRecorder`):** Records actions during tool execution and exports as Python (ADB-based or uiautomator2-based), pytest, JSON, or human-readable format. `export_as_python` defaults to `use_adb=True`, emitting a self-contained script with an inline `DeviceController` class and no external dependencies. `export_as_pytest` additionally runs `_compute_assertions()` over the recorded actions to emit assertions (e.g. expected foreground app/activity after a step). Each recorded action carries screen context (`screen_app`, `screen_activity`) captured live via `_get_screen_context()` (a `dumpsys activity activities` parse), not from the state cache.

**Azure DevOps bug reporting:** Two tools exist — `Report-Bug-To-Azure` (safe: generates an `az boards` CLI command string for manual execution) and `Report-Bug-To-Azure-Direct` (experimental: executes the command directly, may hang). Both map to these custom board fields: `Custom.DescriptionorSteps` (steps + description), `Microsoft.VSTS.TCM.ReproSteps` (actual result), `Microsoft.VSTS.TCM.SystemInfo` (expected result).

## Key Conventions

- Device interaction tools in `main.py` use direct ADB commands (`adb shell input tap/swipe/keyevent`) rather than uiautomator2, to avoid accessibility service conflicts. `Press-Tool` accepts: `home`, `back`, `menu`, `power`, `volume_up`, `volume_down`, `enter`, `delete` (or any raw keycode string).
- All tool functions record actions via `recorder.record_action()` for test recording support. A new tool that touches the device must call it, or exported scripts will silently miss the step.
- `Mobile` class uses lazy initialization — device connection and MCP Helper init happen on first use, not at construction.
- `MCPHelperClient` also supports write operations via ADB content `insert` (keyboard input, overlay config) in addition to `query` for state reads.
- Do not build the project unless explicitly told to do so.

## Docs

`docx/` holds design/troubleshooting notes (MCP Helper integration and fixes, timeout fixes, real-device setup, test recording guide) plus `CONTRIBUTING.md`. Consult it before changing MCP Helper behavior. `README.md` is user-facing but **stale** — it documents 14 tools and omits `Click-By-Label` and the `pytest` export format; update it alongside tool changes.
