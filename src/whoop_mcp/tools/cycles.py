"""Physiological cycle tools (WHOOP days, including daily strain)."""

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
        """Lists the user's physiological cycles (WHOOP's "day"), most recent
        first. Each cycle includes strain, kilojoules, and average/max heart
        rate.

        Args:
            limit: Records per page (max 25).
            start: Start date, 'YYYY-MM-DD' or ISO 8601.
            end: End date, 'YYYY-MM-DD' or ISO 8601.
            next_token: Pagination token returned by a previous call.
        """
        return client.get_collection(
            "/v2/cycle", limit=limit, start=start, end=end, next_token=next_token
        )

    @mcp.tool
    def get_cycle_by_id(cycle_id: int) -> dict[str, Any]:
        """Gets a specific physiological cycle by its ID."""
        return client.get(f"/v2/cycle/{cycle_id}")
