"""CLI de autorizacion: `poetry run python -m whoop_mcp.auth_cli`.

Abre el navegador con la pantalla de login de WHOOP, captura el callback en un
servidor HTTP local y guarda los tokens en disco para que el servidor MCP los use.
"""

from __future__ import annotations

import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from .auth import TokenManager, build_authorize_url
from .config import ConfigError, get_settings

_SUCCESS_HTML = """<!doctype html>
<html><body style="font-family: sans-serif; text-align: center; padding-top: 4rem;">
<h1>&#9989; Autorizacion completada</h1>
<p>Ya puedes cerrar esta pestana y volver a la terminal.</p>
</body></html>"""

_ERROR_HTML = """<!doctype html>
<html><body style="font-family: sans-serif; text-align: center; padding-top: 4rem;">
<h1>&#10060; Error en la autorizacion</h1>
<p>{message}</p>
</body></html>"""


class _CallbackHandler(BaseHTTPRequestHandler):
    """Captura una unica peticion al redirect URI y extrae code/state."""

    result: dict[str, str] = {}
    expected_path: str = "/callback"

    def do_GET(self) -> None:  # noqa: N802 (nombre requerido por BaseHTTPRequestHandler)
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
                message=query.get("error_description", query.get("error", "desconocido"))
            )
            status = 400

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

        # Apaga el servidor desde otro hilo para no bloquear esta respuesta.
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *args: object) -> None:
        pass  # silencia el log por peticion


def _wait_for_callback(host: str, port: int, path: str) -> dict[str, str]:
    _CallbackHandler.expected_path = path
    _CallbackHandler.result = {}
    server = HTTPServer((host, port), _CallbackHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return _CallbackHandler.result


def main() -> None:
    try:
        settings = get_settings()
    except ConfigError as exc:
        print(f"Error de configuracion: {exc}", file=sys.stderr)
        sys.exit(1)

    redirect = urlparse(settings.redirect_uri)
    if redirect.hostname not in ("localhost", "127.0.0.1"):
        print(
            "WHOOP_REDIRECT_URI debe apuntar a localhost para este flujo local, "
            f"pero es: {settings.redirect_uri}",
            file=sys.stderr,
        )
        sys.exit(1)

    state = secrets.token_urlsafe(16)
    url = build_authorize_url(settings, state)

    print("Abriendo el navegador para autorizar el acceso a WHOOP...")
    print(f"Si no se abre automaticamente, visita:\n\n  {url}\n")
    webbrowser.open(url)

    print(f"Esperando el callback en {settings.redirect_uri} ...")
    result = _wait_for_callback(
        redirect.hostname, redirect.port or 80, redirect.path or "/callback"
    )

    if "code" not in result:
        print(
            f"Autorizacion fallida: {result.get('error_description') or result.get('error') or 'sin codigo'}",
            file=sys.stderr,
        )
        sys.exit(1)

    if result.get("state") != state:
        print("El parametro 'state' no coincide (posible CSRF). Abortando.", file=sys.stderr)
        sys.exit(1)

    manager = TokenManager(settings)
    manager.exchange_code(result["code"])

    print(f"\nTokens guardados en {settings.token_file}")
    print("Listo: el servidor MCP ya puede acceder a tu cuenta de WHOOP.")


if __name__ == "__main__":
    main()
