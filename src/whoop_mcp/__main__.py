"""Lets the server run via `python -m whoop_mcp`.

Needed because console entry points use a shebang line that breaks when the
project path contains spaces (e.g. inside iCloud Drive).
"""

from .server import main

if __name__ == "__main__":
    main()
