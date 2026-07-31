"""Registro de todas las tools del servidor."""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import WhoopClient
from . import cycles, profile, recovery, sleep, workouts


def register_all(mcp: FastMCP, client: WhoopClient) -> None:
    profile.register(mcp, client)
    cycles.register(mcp, client)
    recovery.register(mcp, client)
    sleep.register(mcp, client)
    workouts.register(mcp, client)
