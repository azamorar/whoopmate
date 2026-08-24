"""Server configuration: OAuth credentials and paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project directory (repo root) and from the cwd.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv()  # .env in the cwd, if present (doesn't override already-set vars)

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
API_BASE_URL = "https://api.prod.whoop.com/developer"

# Scopes needed for the basic tools. "offline" enables the refresh token.
SCOPES = (
    "read:profile read:body_measurement read:cycles "
    "read:recovery read:sleep read:workout offline"
)

DEFAULT_TOKEN_FILE = Path.home() / ".whoop-mcp" / "tokens.json"


class ConfigError(RuntimeError):
    """Configuration error (missing environment variables, etc.)."""


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    redirect_uri: str
    token_file: Path


def get_settings() -> Settings:
    client_id = os.environ.get("WHOOP_CLIENT_ID", "").strip()
    client_secret = os.environ.get("WHOOP_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        raise ConfigError(
            "Missing WHOOP_CLIENT_ID and/or WHOOP_CLIENT_SECRET. "
            "Copy .env.example to .env and fill in the credentials from your "
            "app on the WHOOP Developer Dashboard (https://developer.whoop.com). "
            "This can't be fixed from a tool call: ask the user to fill in "
            "the project's .env file and restart the MCP server."
        )

    return Settings(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=os.environ.get(
            "WHOOP_REDIRECT_URI", "http://localhost:8007/callback"
        ),
        token_file=Path(
            os.environ.get("WHOOP_TOKEN_FILE", str(DEFAULT_TOKEN_FILE))
        ).expanduser(),
    )
