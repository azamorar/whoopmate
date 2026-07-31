"""Configuracion del servidor: credenciales OAuth y rutas."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Carga .env desde el directorio del proyecto (raiz del repo) y desde el cwd.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv()  # .env del cwd, si existe (no sobreescribe variables ya definidas)

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
API_BASE_URL = "https://api.prod.whoop.com/developer"

# Scopes necesarios para las tools basicas. "offline" habilita el refresh token.
SCOPES = (
    "read:profile read:body_measurement read:cycles "
    "read:recovery read:sleep read:workout offline"
)

DEFAULT_TOKEN_FILE = Path.home() / ".whoop-mcp" / "tokens.json"


class ConfigError(RuntimeError):
    """Error de configuracion (variables de entorno ausentes, etc.)."""


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
            "Faltan WHOOP_CLIENT_ID y/o WHOOP_CLIENT_SECRET. "
            "Copia .env.example a .env y rellena las credenciales de tu app "
            "del Developer Dashboard de WHOOP (https://developer.whoop.com)."
        )

    return Settings(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=os.environ.get(
            "WHOOP_REDIRECT_URI", "http://localhost:8765/callback"
        ),
        token_file=Path(
            os.environ.get("WHOOP_TOKEN_FILE", str(DEFAULT_TOKEN_FILE))
        ).expanduser(),
    )
