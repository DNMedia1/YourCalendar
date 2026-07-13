from __future__ import annotations

from http.server import ThreadingHTTPServer
from typing import Any

from .calendar.placeholder_ics import ensure_placeholder_ics_files
from .config.settings import load_settings
from .web.http_handler import CalendarHttpRequestHandler


def create_calendar_server(settings: dict[str, Any]) -> ThreadingHTTPServer:
    # Keep server setup in one place so CLI startup and tests use the same preflight.
    # Missing ICS files are repaired here to keep the website browsable after new
    # mappings are added. Raising an explicit exception would also be valid when
    # faster feedback is preferred over automatic placeholder generation.
    ensure_placeholder_ics_files(settings)
    handler = CalendarHttpRequestHandler
    handler.settings = settings
    host = str(settings.get("host", "127.0.0.1"))
    port = int(settings.get("port", 8080))
    return ThreadingHTTPServer((host, port), handler)


def main() -> int:
    settings = load_settings()
    server = create_calendar_server(settings)
    host, port = server.server_address
    print(f"Serving YourCalendar Alpha at http://{host}:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
