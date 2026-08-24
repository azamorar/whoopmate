"""Synchronous HTTP client for the WHOOP API v2."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from .auth import AuthError, TokenManager
from .config import API_BASE_URL, Settings, get_settings


class WhoopAPIError(RuntimeError):
    """Error returned by the WHOOP API."""


def to_iso_datetime(value: str | None, *, end_of_day: bool = False) -> str | None:
    """Accepts 'YYYY-MM-DD' or an ISO 8601 datetime and returns full ISO 8601 (UTC).

    WHOOP requires full timestamps in the start/end parameters.
    """
    if not value:
        return None
    value = value.strip()
    try:
        if len(value) == 10:  # date only
            dt = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if end_of_day:
                dt = dt.replace(hour=23, minute=59, second=59)
        else:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise WhoopAPIError(
            f"Invalid date: {value!r}. Use 'YYYY-MM-DD' or full ISO 8601."
        ) from exc
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class WhoopClient:
    """Wraps requests with authentication and a retry after 401."""

    def __init__(self) -> None:
        self._settings: Settings | None = None
        self._token_manager: TokenManager | None = None
        self._session = requests.Session()

    def _ensure_ready(self) -> TokenManager:
        # Lazy initialization: this lets the server boot even without .env,
        # surfacing the config error only when a tool gets called.
        if self._token_manager is None:
            self._settings = get_settings()
            self._token_manager = TokenManager(self._settings)
        return self._token_manager

    def get_token_manager(self) -> TokenManager:
        """Exposes the TokenManager for the auth tools (whoop_login, whoop_auth_status)."""
        return self._ensure_ready()

    @property
    def settings(self) -> Settings:
        self._ensure_ready()
        assert self._settings is not None
        return self._settings

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        manager = self._ensure_ready()
        token = manager.get_access_token()

        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        url = f"{API_BASE_URL}{path}"

        response = self._session.get(
            url, params=clean_params, headers=self._auth_header(token), timeout=30
        )
        if response.status_code == 401:
            # Token revoked or expired early: refresh and retry once.
            token = manager.force_refresh()
            response = self._session.get(
                url, params=clean_params, headers=self._auth_header(token), timeout=30
            )

        if response.status_code == 404:
            raise WhoopAPIError(f"Resource not found: {path}")
        if response.status_code == 429:
            raise WhoopAPIError(
                "WHOOP API rate limit reached (429). Wait a moment before retrying."
            )
        if response.status_code >= 400:
            raise WhoopAPIError(
                f"WHOOP returned {response.status_code} from {path}: {response.text}"
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
        """GET on a collection endpoint using WHOOP's standard pagination.

        The API caps `limit` at 25 per page; `next_token` continues paging.
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
