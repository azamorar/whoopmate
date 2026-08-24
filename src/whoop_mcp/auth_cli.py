"""Authorization CLI: `poetry run python -m whoop_mcp.auth_cli`.

Still works for manually pre-authorizing from the terminal (for example
before first use, or in a setup with no AI agent in front of it), but it's
no longer the only path: the MCP server exposes the `whoop_login` tool,
which runs this same flow on the agent's own request when it detects it's
needed.
"""

from __future__ import annotations

import sys
from urllib.parse import urlparse

from .auth import AuthError, TokenManager
from .config import ConfigError, get_settings
from .oauth_flow import run_authorization_flow

_CLI_TIMEOUT_SECONDS = 300  # 5 min: a human in a terminal can take longer than an agent


def main() -> None:
    try:
        settings = get_settings()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    redirect = urlparse(settings.redirect_uri)
    if redirect.hostname not in ("localhost", "127.0.0.1"):
        print(
            "WHOOP_REDIRECT_URI must point to localhost for this local flow, "
            f"but it's: {settings.redirect_uri}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Opening your browser to authorize access to WHOOP...")
    print(f"Waiting for the callback at {settings.redirect_uri} (up to {_CLI_TIMEOUT_SECONDS}s)...\n")

    manager = TokenManager(settings)
    try:
        run_authorization_flow(
            settings,
            manager,
            timeout=_CLI_TIMEOUT_SECONDS,
            on_authorize_url=lambda url: print(
                f"If the browser didn't open on its own, visit:\n\n  {url}\n"
            ),
        )
    except AuthError as exc:
        print(f"Authorization failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nTokens saved to {settings.token_file}")
    print("Done: the MCP server can now access your WHOOP account.")


if __name__ == "__main__":
    main()
