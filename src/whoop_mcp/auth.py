"""Gestion de tokens OAuth2: almacenamiento, intercambio de codigo y refresh."""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.parse import urlencode

import requests

from .config import AUTH_URL, SCOPES, TOKEN_URL, Settings

# Renovamos el access token con este margen antes de que caduque.
_EXPIRY_MARGIN_SECONDS = 60


class AuthError(RuntimeError):
    """Error de autenticacion contra WHOOP."""


class TokenManager:
    """Guarda los tokens en disco y renueva el access token cuando caduca."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # ------------------------------------------------------------------
    # Almacenamiento
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
        """Normaliza la respuesta del endpoint de token y la persiste."""
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
    # Flujo OAuth2
    # ------------------------------------------------------------------
    def exchange_code(self, code: str) -> dict[str, Any]:
        """Intercambia el authorization code por tokens (paso final del login)."""
        payload = self._request_token(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._settings.redirect_uri,
            }
        )
        return self.save_tokens(payload)

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Renueva el access token. WHOOP rota el refresh token: hay que guardarlo."""
        payload = self._request_token(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "offline",
            }
        )
        return self.save_tokens(payload)

    def get_access_token(self) -> str:
        """Devuelve un access token valido, renovandolo si esta caducado."""
        tokens = self.load_tokens()
        if tokens is None:
            raise AuthError(
                "No hay tokens guardados. Ejecuta primero `poetry run python -m whoop_mcp.auth_cli` "
                "para autorizar el acceso a tu cuenta de WHOOP."
            )

        if time.time() < tokens.get("expires_at", 0) - _EXPIRY_MARGIN_SECONDS:
            return tokens["access_token"]

        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise AuthError(
                "El access token ha caducado y no hay refresh token (falta el "
                "scope 'offline'). Vuelve a ejecutar `poetry run python -m whoop_mcp.auth_cli`."
            )

        refreshed = self.refresh(refresh_token)
        return refreshed["access_token"]

    def force_refresh(self) -> str:
        """Fuerza una renovacion (util tras recibir un 401 inesperado)."""
        tokens = self.load_tokens() or {}
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise AuthError(
                "Token invalido y sin refresh token disponible. "
                "Vuelve a ejecutar `poetry run python -m whoop_mcp.auth_cli`."
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
                f"WHOOP devolvio {response.status_code} en el endpoint de token: "
                f"{response.text}"
            )
        return response.json()


def build_authorize_url(settings: Settings, state: str) -> str:
    """URL de autorizacion para iniciar el flujo OAuth2 en el navegador."""
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
