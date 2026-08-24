"""Recovery tools (recovery score, HRV, RHR...)."""

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
        """Lists the user's recoveries, most recent first. Includes recovery
        score (0-100), HRV, resting heart rate, SpO2, and skin temperature.

        Args:
            limit: Records per page (max 25).
            start: Start date, 'YYYY-MM-DD' or ISO 8601.
            end: End date, 'YYYY-MM-DD' or ISO 8601.
            next_token: Pagination token returned by a previous call.
        """
        return client.get_collection(
            "/v2/recovery", limit=limit, start=start, end=end, next_token=next_token
        )

    @mcp.tool
    def get_latest_recovery() -> dict[str, Any]:
        """Gets the user's most recent recovery (today's, if already
        calculated)."""
        data = client.get_collection("/v2/recovery", limit=1)
        records = data.get("records", [])
        if not records:
            return {"message": "No recoveries recorded yet."}
        return records[0]

    @mcp.tool
    def get_cycle_recovery(cycle_id: int) -> dict[str, Any]:
        """Gets the recovery associated with a specific physiological cycle."""
        return client.get(f"/v2/cycle/{cycle_id}/recovery")
