"""El PDF de una versión: Playwright `page.pdf` (con `outline` y `tagged`) sobre el Edge
instalado, servido por `http://127.0.0.1` (`architecture.md` §14.2; Playwright y Chromium
descartan o bloquean `file://`, `verification.md` §8 H3, §9.2-3).
"""

from __future__ import annotations

import contextlib
import sys
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright


def _channel() -> str | None:
    """`msedge` en este portátil Windows; en CI Linux, el Chromium que trae Playwright."""
    return "msedge" if sys.platform == "win32" else None


class _HtmlHandler(BaseHTTPRequestHandler):
    html_body: bytes = b""

    def do_GET(self) -> None:
        body = self.html_body
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_: str, *args: object) -> None:
        del format_, args  # silencio: no ensucia la salida de pytest


@contextlib.contextmanager
def _serve(html: str) -> Iterator[str]:
    """Sirve `html` en un puerto efímero de 127.0.0.1 mientras dura el `with` (nunca `file://`)."""
    handler = type("_Handler", (_HtmlHandler,), {"html_body": html.encode("utf-8")})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        yield f"http://127.0.0.1:{port}/"
    finally:
        server.shutdown()
        thread.join()


def render_pdf(html: str) -> bytes:
    """El PDF de `html`, con marcadores (`outline`) y etiquetado (`tagged`) — mismo resultado
    para el mismo HTML (013-I5)."""
    with _serve(html) as url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=_channel())
        try:
            page = browser.new_page()
            page.goto(url)
            return page.pdf(tagged=True, outline=True)
        finally:
            browser.close()
