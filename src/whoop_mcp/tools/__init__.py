"""Registration of all the server's tools."""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import WhoopClient
from . import auth, cycles, profile, recovery, sleep, workouts


def register_all(mcp: FastMCP, client: WhoopClient) -> None:
    auth.register(mcp, client)
    profile.register(mcp, client)
    cycles.register(mcp, client)
    recovery.register(mcp, client)
    sleep.register(mcp, client)
    workouts.register(mcp, client)
