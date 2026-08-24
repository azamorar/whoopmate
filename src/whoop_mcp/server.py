"""MCP server entry point (stdio transport)."""

from __future__ import annotations

from fastmcp import FastMCP

from .client import WhoopClient
from .tools import register_all

mcp = FastMCP(
    name="whoop",
    instructions=(
        "MCP server for the WHOOP API. Exposes the user's account data: "
        "profile, body measurements, cycles (daily strain), recovery "
        "(recovery/HRV), sleep, and workouts. Dates accept 'YYYY-MM-DD' or "
        "ISO 8601 format. Collections are paginated with `next_token` "
        "(max 25 records per page).\n\n"
        "Authentication: if a tool fails with an authentication error (or "
        "this is the first time this server is used), call the "
        "`whoop_login` tool to authorize access to the user's WHOOP account "
        "(it opens their browser), then retry the original call. Use "
        "`whoop_auth_status` to check the status with no side effects "
        "before deciding whether authentication is needed."
    ),
)

_client = WhoopClient()
register_all(mcp, _client)


def main() -> None:
    # stdio is FastMCP's default transport.
    mcp.run()


if __name__ == "__main__":
    main()
