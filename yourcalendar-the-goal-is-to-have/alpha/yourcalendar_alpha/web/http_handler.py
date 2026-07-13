from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .page_renderer import render_home_page, render_static_page
from ..config.settings import resolve_path


STATIC_ASSET_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


class CalendarHttpRequestHandler(BaseHTTPRequestHandler):
    settings: dict[str, Any] = {}

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API.
        parsed_path = urlparse(self.path).path
        if parsed_path == "/":
            self._send_html(render_home_page(self.settings))
            return
        static_page = render_static_page(parsed_path, self.settings)
        if static_page is not None:
            self._send_html(static_page)
            return
        if parsed_path.startswith("/ics/"):
            self._send_ics_file(parsed_path)
            return
        if parsed_path.startswith("/static/"):
            self._send_static_asset(parsed_path)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def _send_html(self, body: str) -> None:
        self._send_bytes(body.encode("utf-8"), "text/html; charset=utf-8")

    def _send_ics_file(self, request_path: str) -> None:
        ics_name = Path(request_path).name
        ics_path = resolve_path(self.settings, self.settings["ics_output_dir"]) / ics_name
        if not ics_path.exists() or ics_path.suffix.lower() != ".ics":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._send_bytes(ics_path.read_bytes(), "text/calendar; charset=utf-8", filename=ics_name)

    def _send_static_asset(self, request_path: str) -> None:
        asset_name = Path(request_path).name
        asset_path = Path(__file__).resolve().parent / "static" / asset_name
        content_type = STATIC_ASSET_TYPES.get(asset_path.suffix.lower())
        if not content_type or not asset_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._send_bytes(asset_path.read_bytes(), content_type)

    def _send_bytes(self, payload: bytes, content_type: str, filename: str | None = None) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        if filename:
            self.send_header("Content-Disposition", f'inline; filename="{filename}"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")
