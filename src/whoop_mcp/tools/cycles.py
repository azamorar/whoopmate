"""Tools de ciclos fisiologicos (dias WHOOP, incluyen el strain diario)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import WhoopClient


def register(mcp: FastMCP, client: WhoopClient) -> None:
    @mcp.tool
    def get_cycles(
        limit: int = 10,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict[str, Any]:
        """Lista los ciclos fisiologicos del usuario (el "dia" de WHOOP), del mas
        reciente al mas antiguo. Cada ciclo incluye el strain, kilojulios y
        frecuencia cardiaca media/maxima.

        Args:
            limit: Numero de registros por pagina (max 25).
            start: Fecha inicio, 'YYYY-MM-DD' o ISO 8601.
            end: Fecha fin, 'YYYY-MM-DD' o ISO 8601.
            next_token: Token de paginacion devuelto por una llamada anterior.
        """
        return client.get_collection(
            "/v2/cycle", limit=limit, start=start, end=end, next_token=next_token
        )

    @mcp.tool
    def get_cycle_by_id(cycle_id: int) -> dict[str, Any]:
        """Obtiene un ciclo fisiologico concreto por su ID."""
        return client.get(f"/v2/cycle/{cycle_id}")
