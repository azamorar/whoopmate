"""Cliente HTTP sincrono para la API v2 de WHOOP."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from .auth import AuthError, TokenManager
from .config import API_BASE_URL, Settings, get_settings


class WhoopAPIError(RuntimeError):
    """Error devuelto por la API de WHOOP."""


def to_iso_datetime(value: str | None, *, end_of_day: bool = False) -> str | None:
    """Acepta 'YYYY-MM-DD' o un datetime ISO 8601 y devuelve ISO 8601 completo (UTC).

    WHOOP exige timestamps completos en los parametros start/end.
    """
    if not value:
        return None
    value = value.strip()
    try:
        if len(value) == 10:  # solo fecha
            dt = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if end_of_day:
                dt = dt.replace(hour=23, minute=59, second=59)
        else:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise WhoopAPIError(
            f"Fecha invalida: {value!r}. Usa 'YYYY-MM-DD' o ISO 8601 completo."
        ) from exc
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class WhoopClient:
    """Envoltorio de requests con autenticacion y reintento tras 401."""

    def __init__(self) -> None:
        self._settings: Settings | None = None
        self._token_manager: TokenManager | None = None
        self._session = requests.Session()

    def _ensure_ready(self) -> TokenManager:
        # Inicializacion perezosa: asi el servidor arranca aunque falte el .env
        # y el error de configuracion se muestra al invocar una tool.
        if self._token_manager is None:
            self._settings = get_settings()
            self._token_manager = TokenManager(self._settings)
        return self._token_manager

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        manager = self._ensure_ready()
        token = manager.get_access_token()

        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        url = f"{API_BASE_URL}{path}"

        response = self._session.get(
            url, params=clean_params, headers=self._auth_header(token), timeout=30
        )
        if response.status_code == 401:
            # Token revocado o caducado antes de tiempo: refresca y reintenta una vez.
            token = manager.force_refresh()
            response = self._session.get(
                url, params=clean_params, headers=self._auth_header(token), timeout=30
            )

        if response.status_code == 404:
            raise WhoopAPIError(f"Recurso no encontrado: {path}")
        if response.status_code == 429:
            raise WhoopAPIError(
                "Limite de peticiones de la API de WHOOP alcanzado (429). "
                "Espera un momento antes de reintentar."
            )
        if response.status_code >= 400:
            raise WhoopAPIError(
                f"WHOOP devolvio {response.status_code} en {path}: {response.text}"
            )
        return response.json()

    def get_collection(
        self,
        path: str,
        *,
        limit: int = 10,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict[str, Any]:
        """GET sobre un endpoint de coleccion con paginacion estandar de WHOOP.

        La API limita `limit` a 25 por pagina; `next_token` permite seguir paginando.
        """
        return self.get(
            path,
            params={
                "limit": max(1, min(limit, 25)),
                "start": to_iso_datetime(start),
                "end": to_iso_datetime(end, end_of_day=True),
                "nextToken": next_token,
            },
        )

    @staticmethod
    def _auth_header(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}


__all__ = ["WhoopClient", "WhoopAPIError", "AuthError", "to_iso_datetime"]
