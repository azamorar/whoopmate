"""Authentication tools: let the agent itself start and check the OAuth2 login.

An MCP host gives the agent no shell access: it can't run
`whoop_mcp.auth_cli` on its own even if it "knows" it needs to. That's why
authentication is exposed as two more tools, and the rest of the tools
return errors that explicitly instruct calling `whoop_login` when needed
(see AuthError in auth.py).
"""

from __future__ import annotations

import time
from typing import Any

from fastmcp import FastMCP

from ..auth import AuthError
from ..client import WhoopClient
from ..oauth_flow import run_authorization_flow


def register(mcp: FastMCP, client: WhoopClient) -> None:
    @mcp.tool
    def whoop_auth_status() -> dict[str, Any]:
        """Checks whether there's an authorized WHOOP session, without opening
        the browser or making network requests. Useful for deciding whether
        to call `whoop_login` before using the rest of the tools (profile,
        recovery, sleep, workouts...).
        """
        manager = client.get_token_manager()
        tokens = manager.load_tokens()
        if tokens is None:
            return {"authenticated": False, "reason": "no_tokens"}

        access_token_valid = time.time() < tokens.get("expires_at", 0)
        has_refresh_token = bool(tokens.get("refresh_token"))

        return {
            "authenticated": access_token_valid or has_refresh_token,
            "access_token_valid": access_token_valid,
            "has_refresh_token": has_refresh_token,
            "token_file": str(client.settings.token_file),
        }

    @mcp.tool
    def whoop_login(force: bool = False, timeout_seconds: int = 120) -> dict[str, Any]:
        """Authorizes (or re-authorizes) access to the user's WHOOP account.

        Opens the user's browser to WHOOP's login screen and waits up to
        `timeout_seconds` seconds for authorization to complete. The
        resulting tokens are saved to disk, and the rest of the tools then
        work without asking for login again.

        Call this tool as soon as another tool fails with an authentication
        error, or proactively if you don't know whether the user is already
        authenticated (use `whoop_auth_status` to check first, with no side
        effects).

        Args:
            force: If True, forces a fresh login even if valid tokens
                already exist. Useful for switching WHOOP accounts, or if
                another tool suspects the token was revoked.
            timeout_seconds: How long to wait for the user to complete the
                browser login before giving up (120s by default).
        """
        manager = client.get_token_manager()

        if not force:
            try:
                manager.get_access_token()
                return {
                    "status": "already_authenticated",
                    "message": (
                        "There was already a valid WHOOP session; no need "
                        "to open the browser."
                    ),
                }
            except AuthError:
                pass  # not authenticated or invalid refresh token: proceed with full login

        settings = client.settings
        try:
            run_authorization_flow(settings, manager, timeout=timeout_seconds)
        except AuthError as exc:
            return {"status": "failed", "message": str(exc)}

        return {
            "status": "authenticated",
            "message": "Authorization complete. The rest of the WHOOP tools now work.",
        }
