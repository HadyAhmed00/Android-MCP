"""Backwards-compatible entry point.

Kept so existing MCP client configs pointing at `/path/to/Android-MCP/main.py`
keep working. New installs should use the `android-mcp` console script.
"""

from android_mcp.server import main

if __name__ == '__main__':
    main()
