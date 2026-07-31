"""Permite lanzar el servidor con `python -m whoop_mcp`.

Necesario porque los entry points de consola usan un shebang que se rompe
cuando la ruta del proyecto contiene espacios (p. ej. dentro de iCloud Drive).
"""

from .server import main

if __name__ == "__main__":
    main()
