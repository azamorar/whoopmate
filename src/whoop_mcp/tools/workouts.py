"""Tools de entrenamientos (strain, zonas de FC, distancia...)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import WhoopClient


def register(mcp: FastMCP, client: WhoopClient) -> None:
    @mcp.tool
    def get_workouts(
        limit: int = 10,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict[str, Any]:
        """Lista los entrenamientos del usuario, del mas reciente al mas antiguo.
        Incluye deporte, strain, frecuencia cardiaca media/maxima, kilojulios,
        distancia y tiempo en cada zona de frecuencia cardiaca.

        Args:
            limit: Numero de registros por pagina (max 25).
            start: Fecha inicio, 'YYYY-MM-DD' o ISO 8601.
            end: Fecha fin, 'YYYY-MM-DD' o ISO 8601.
            next_token: Token de paginacion devuelto por una llamada anterior.
        """
        return client.get_collection(
            "/v2/activity/workout",
            limit=limit,
            start=start,
            end=end,
            next_token=next_token,
        )

    @mcp.tool
    def get_workout_by_id(workout_id: str) -> dict[str, Any]:
        """Obtiene un entrenamiento concreto por su ID (UUID)."""
        return client.get(f"/v2/activity/workout/{workout_id}")
