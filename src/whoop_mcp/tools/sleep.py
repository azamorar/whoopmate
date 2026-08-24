"""Sleep tools (stages, efficiency, sleep debt...)."""

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
        """Lists the user's sleep sessions, most recent first. Includes sleep
        stages, efficiency, sleep performance, and whether it was a nap.

        Args:
            limit: Records per page (max 25).
            start: Start date, 'YYYY-MM-DD' or ISO 8601.
            end: End date, 'YYYY-MM-DD' or ISO 8601.
            next_token: Pagination token returned by a previous call.
        """
        return client.get_collection(
            "/v2/activity/sleep", limit=limit, start=start, end=end, next_token=next_token
        )

    @mcp.tool
    def get_sleep_by_id(sleep_id: str) -> dict[str, Any]:
        """Gets a specific sleep session by its ID (UUID)."""
        return client.get(f"/v2/activity/sleep/{sleep_id}")
