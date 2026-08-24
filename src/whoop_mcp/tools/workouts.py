"""Workout tools (strain, heart rate zones, distance...)."""

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
        """Lists the user's workouts, most recent first. Includes sport,
        strain, average/max heart rate, kilojoules, distance, and time spent
        in each heart rate zone.

        Args:
            limit: Records per page (max 25).
            start: Start date, 'YYYY-MM-DD' or ISO 8601.
            end: End date, 'YYYY-MM-DD' or ISO 8601.
            next_token: Pagination token returned by a previous call.
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
        """Gets a specific workout by its ID (UUID)."""
        return client.get(f"/v2/activity/workout/{workout_id}")
