"""Tools de perfil y medidas corporales."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import WhoopClient


def register(mcp: FastMCP, client: WhoopClient) -> None:
    @mcp.tool
    def get_profile() -> dict[str, Any]:
        """Obtiene el perfil basico del usuario de WHOOP (nombre, email, user_id)."""
        return client.get("/v2/user/profile/basic")

    @mcp.tool
    def get_body_measurements() -> dict[str, Any]:
        """Obtiene las medidas corporales del usuario: altura (m), peso (kg) y
        frecuencia cardiaca maxima."""
        return client.get("/v2/user/measurement/body")
