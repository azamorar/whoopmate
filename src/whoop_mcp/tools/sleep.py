"""Tools de sueno (fases, eficiencia, deuda de sueno...)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import WhoopClient


def register(mcp: FastMCP, client: WhoopClient) -> None:
    @mcp.tool
    def get_sleeps(
        limit: int = 10,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict[str, Any]:
        """Lista las sesiones de sueno del usuario, de la mas reciente a la mas
        antigua. Incluye fases del sueno, eficiencia, sleep performance y si fue
        una siesta.

        Args:
            limit: Numero de registros por pagina (max 25).
            start: Fecha inicio, 'YYYY-MM-DD' o ISO 8601.
            end: Fecha fin, 'YYYY-MM-DD' o ISO 8601.
            next_token: Token de paginacion devuelto por una llamada anterior.
        """
        return client.get_collection(
            "/v2/activity/sleep", limit=limit, start=start, end=end, next_token=next_token
        )

    @mcp.tool
    def get_sleep_by_id(sleep_id: str) -> dict[str, Any]:
        """Obtiene una sesion de sueno concreta por su ID (UUID)."""
        return client.get(f"/v2/activity/sleep/{sleep_id}")
