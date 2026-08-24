"""Interactive OAuth2 authorization flow (browser + local callback).

Shared logic used by the `auth_cli.py` script and by the `whoop_login` MCP
tool: opens the user's browser, starts a local HTTP server that waits for
WHOOP's callback with a bounded timeout, and exchanges the code for tokens.

Must not call `print()` or write to stdout: this also runs inside MCP tool
calls, and stdout is reserved for the stdio transport's JSON-RPC messages.
"""

from __future__ import annotations

import secrets
import threading
import webbrowser
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .auth import AuthError, TokenManager, build_authorize_url
from .config import Settings

_SUCCESS_HTML = """<!doctype html>
<html><body style="font-family: sans-serif; text-align: center; padding-top: 4rem;">
<h1>&#9989; Authorization complete</h1>
<p>You can close this tab now.</p>
</body></html>"""

_ERROR_HTML = """<!doctype html>
<html><body style="font-family: sans-serif; text-align: center; padding-top: 4rem;">
<h1>&#10060; Authorization error</h1>
<p>{message}</p>
</body></html>"""


class _CallbackHandler(BaseHTTPRequestHandler):
    """Captures a single request to the redirect URI and extracts code/state."""

    result: dict[str, str] = {}
    expected_path: str = "/callback"

    def do_GET(self) -> None:  # noqa: N802 (name required by BaseHTTPRequestHandler)
        parsed = urlparse(self.path)
        if parsed.path != self.expected_path:
            self.send_response(404)
            self.end_headers()
            return

        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        _CallbackHandler.result = query

        if "code" in query:
            body = _SUCCESS_HTML
            status = 200
        else:
            body = _ERROR_HTML.format(
                message=query.get("error_description", query.get("error", "unknown"))
            )
            status = 400

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

        # Shut down the server from another thread so this response isn't blocked.
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *args: object) -> None:
        pass  # silence the per-request log


def _wait_for_callback(host: str, port: int, path: str, timeout: float) -> dict[str, str]:
    """Waits for the callback up to `timeout` seconds; returns {} if nothing arrives."""
    _CallbackHandler.expected_path = path
    _CallbackHandler.result = {}

    try:
        server = HTTPServer((host, port), _CallbackHandler)
    except OSError as exc:
        raise AuthError(
            f"Could not start the local callback server on {host}:{port} ({exc}). "
            "Is another process using that port? Change WHOOP_REDIRECT_URI to a "
            "free port (and update the redirect URI registered in the WHOOP "
            "Developer Dashboard)."
        ) from exc

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    server_thread.join(timeout)
    if server_thread.is_alive():
        server.shutdown()
        server_thread.join()
    server.server_close()
    return _CallbackHandler.result


def run_authorization_flow(
    settings: Settings,
    token_manager: TokenManager,
    *,
    timeout: float = 120,
    open_browser: bool = True,
    on_authorize_url: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Runs the full flow: browser -> callback -> code exchange.

    Returns {"tokens": ..., "authorize_url": ...} on success. Raises
    AuthError with an actionable message otherwise (timeout, WHOOP error,
    invalid state, port in use).
    """
    redirect = urlparse(settings.redirect_uri)
    if redirect.hostname not in ("localhost", "127.0.0.1"):
        raise AuthError(
            "WHOOP_REDIRECT_URI must point to localhost for this local flow, "
            f"but it's: {settings.redirect_uri}"
        )

    state = secrets.token_urlsafe(16)
    authorize_url = build_authorize_url(settings, state)

    if on_authorize_url is not None:
        on_authorize_url(authorize_url)

    if open_browser:
        try:
            webbrowser.open(authorize_url)
        except webbrowser.Error:
            pass  # no browser available (headless environment): keep waiting anyway

    result = _wait_for_callback(
        redirect.hostname, redirect.port or 80, redirect.path or "/callback", timeout=timeout
    )

    if "code" not in result:
        if not result:
            raise AuthError(
                f"No response from WHOOP after {timeout:.0f}s. If the browser "
                f"didn't open, visit this URL manually to authorize: {authorize_url}"
            )
        raise AuthError(
            "Authorization failed: "
            f"{result.get('error_description') or result.get('error') or 'no code'}"
        )

    if result.get("state") != state:
        raise AuthError("The 'state' parameter doesn't match (possible CSRF). Authorization aborted.")

    tokens = token_manager.exchange_code(result["code"])
    return {"tokens": tokens, "authorize_url": authorize_url}
