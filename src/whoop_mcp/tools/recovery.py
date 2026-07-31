"""Tools de recuperacion (recovery score, HRV, RHR...)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import WhoopClient


def register(mcp: FastMCP, client: WhoopClient) -> None:
    @mcp.tool
    def get_recoveries(
        limit: int = 10,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict[str, Any]:
        """Lista las recuperaciones del usuario, de la mas reciente a la mas
        antigua. Incluye recovery score (0-100), HRV, frecuencia cardiaca en
        reposo, SpO2 y temperatura de la piel.

        Args:
            limit: Numero de registros por pagina (max 25).
            start: Fecha inicio, 'YYYY-MM-DD' o ISO 8601.
            end: Fecha fin, 'YYYY-MM-DD' o ISO 8601.
            next_token: Token de paginacion devuelto por una llamada anterior.
        """
        return client.get_collection(
            "/v2/recovery", limit=limit, start=start, end=end, next_token=next_token
        )

    @mcp.tool
    def get_latest_recovery() -> dict[str, Any]:
        """Obtiene la recuperacion mas reciente del usuario (la de hoy, si ya
        esta calculada)."""
        data = client.get_collection("/v2/recovery", limit=1)
        records = data.get("records", [])
        if not records:
            return {"message": "No hay recuperaciones registradas."}
        return records[0]

    @mcp.tool
    def get_cycle_recovery(cycle_id: int) -> dict[str, Any]:
        """Obtiene la recuperacion asociada a un ciclo fisiologico concreto."""
        return client.get(f"/v2/cycle/{cycle_id}/recovery")
