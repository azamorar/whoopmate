"""Punto de entrada del servidor MCP (transporte stdio)."""

from __future__ import annotations

from fastmcp import FastMCP

from .client import WhoopClient
from .tools import register_all

mcp = FastMCP(
    name="whoop",
    instructions=(
        "Servidor MCP para la API de WHOOP. Expone datos de la cuenta del "
        "usuario: perfil, medidas corporales, ciclos (strain diario), "
        "recuperaciones (recovery/HRV), sueno y entrenamientos. "
        "Las fechas aceptan formato 'YYYY-MM-DD' o ISO 8601. Las colecciones "
        "se paginan con `next_token` (max 25 registros por pagina)."
    ),
)

_client = WhoopClient()
register_all(mcp, _client)


def main() -> None:
    # stdio es el transporte por defecto de FastMCP.
    mcp.run()


if __name__ == "__main__":
    main()
