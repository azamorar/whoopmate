"""OAuth2 token management: storage, code exchange, and refresh."""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.parse import urlencode

import requests

from .config import AUTH_URL, SCOPES, TOKEN_URL, Settings

# Renew the access token this many seconds before it expires.
_EXPIRY_MARGIN_SECONDS = 60


class AuthError(RuntimeError):
    """Authentication error against WHOOP."""


class TokenManager:
    """Stores tokens on disk and renews the access token when it expires."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    def load_tokens(self) -> dict[str, Any] | None:
        path = self._settings.token_file
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return None

    def save_tokens(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalizes the token endpoint response and persists it."""
        tokens = {
            "access_token": payload["access_token"],
            "refresh_token": payload.get("refresh_token"),
            "scope": payload.get("scope"),
            "token_type": payload.get("token_type", "bearer"),
            "expires_at": time.time() + int(payload.get("expires_in", 3600)),
        }
        path = self._settings.token_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(tokens, indent=2))
        os.chmod(path, 0o600)
        return tokens

    # ------------------------------------------------------------------
    # OAuth2 flow
    # ------------------------------------------------------------------
    def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchanges the authorization code for tokens (final login step)."""
        payload = self._request_token(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._settings.redirect_uri,
            }
        )
        return self.save_tokens(payload)

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Renews the access token. WHOOP rotates the refresh token, so it must be saved."""
        payload = self._request_token(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "offline",
            }
        )
        return self.save_tokens(payload)

    def get_access_token(self) -> str:
        """Returns a valid access token, renewing it if expired."""
        tokens = self.load_tokens()
        if tokens is None:
            raise AuthError(
                "No authorized WHOOP session yet. Call the `whoop_login` tool "
                "to authorize access (it will open the user's browser), then "
                "retry this call."
            )

        if time.time() < tokens.get("expires_at", 0) - _EXPIRY_MARGIN_SECONDS:
            return tokens["access_token"]

        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise AuthError(
                "The access token expired and there's no refresh token "
                "(missing the 'offline' scope). Call the `whoop_login` tool "
                "with `force=true` to re-authenticate."
            )

        refreshed = self.refresh(refresh_token)
        return refreshed["access_token"]

    def force_refresh(self) -> str:
        """Forces a renewal (useful after an unexpected 401)."""
        tokens = self.load_tokens() or {}
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise AuthError(
                "Invalid token and no refresh token available. Call the "
                "`whoop_login` tool with `force=true` to re-authenticate."
            )
        refreshed = self.refresh(refresh_token)
        return refreshed["access_token"]

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------
    def _request_token(self, data: dict[str, str]) -> dict[str, Any]:
        data = {
            **data,
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret,
        }
        response = requests.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        if response.status_code != 200:
            raise AuthError(
                f"WHOOP returned {response.status_code} from the token endpoint: "
                f"{response.text}"
            )
        return response.json()


def build_authorize_url(settings: Settings, state: str) -> str:
    """Authorization URL to start the OAuth2 flow in the browser."""
    params = urlencode(
        {
            "response_type": "code",
            "client_id": settings.client_id,
            "redirect_uri": settings.redirect_uri,
            "scope": SCOPES,
            "state": state,
        }
    )
    return f"{AUTH_URL}?{params}"
