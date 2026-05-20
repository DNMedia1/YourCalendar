#!/usr/bin/env python3
from __future__ import annotations

import json
import platform
import subprocess
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from yourcalendar_poc import (
    DEFAULT_OUTPUT,
    DEFAULT_TIMEZONE,
    OPENLIGADB_BASE,
    OPENLIGADB_LEAGUES,
    POCError,
    build_sample_events,
    default_football_season,
    fetch_json_list,
    fetch_openligadb_multi_league_events,
    write_ics,
)


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
OUTPUT_PATH = ROOT / DEFAULT_OUTPUT
CALENDAR_NAME = "YourCalendar German Football"


def split_title(title: str) -> tuple[str, str]:
    if " vs " not in title:
        return title, ""
    home, away = title.split(" vs ", 1)
    return home, away


def league_from_uid(uid: str) -> str:
    parts = uid.split("-")
    if len(parts) >= 3 and parts[0] == "openligadb":
        return parts[1]
    return "sample"


def event_to_dict(event) -> dict:
    home, away = split_title(event.title)
    league = league_from_uid(event.uid)
    return {
        "uid": event.uid,
        "title": event.title,
        "homeTeam": home,
        "awayTeam": away,
        "league": league,
        "leagueName": OPENLIGADB_LEAGUES.get(league, "Sample"),
        "startsAt": event.starts_at.isoformat(),
        "endsAt": event.ends_at.isoformat(),
        "dateLabel": event.starts_at.strftime("%d.%m.%Y"),
        "timeLabel": event.starts_at.strftime("%H:%M %Z"),
        "location": event.location,
        "source": event.source,
        "description": event.description,
        "status": event.status,
    }


def selected_leagues(params: dict[str, list[str]]) -> list[str]:
    raw = params.get("leagues", ["bl1,bl2,bl3"])[0]
    leagues = [item.strip() for item in raw.split(",") if item.strip()]
    return [league for league in leagues if league in OPENLIGADB_LEAGUES]


def load_events(params: dict[str, list[str]]) -> list:
    use_sample = params.get("sample", ["false"])[0] == "true"
    if use_sample:
        return build_sample_events(DEFAULT_TIMEZONE)

    leagues = selected_leagues(params)
    include_past = params.get("includePast", ["false"])[0] == "true"
    season_raw = params.get("season", [""])[0]
    season = int(season_raw) if season_raw.isdigit() else default_football_season()
    events = fetch_openligadb_multi_league_events(
        leagues=leagues,
        season=season,
        upcoming_only=not include_past,
        tz_name=DEFAULT_TIMEZONE,
    )

    team_query = params.get("team", [""])[0].strip().casefold()
    favorites = [
        item.strip().casefold()
        for item in params.get("favorites", [""])[0].split(",")
        if item.strip()
    ]
    if team_query:
        events = [
            event
            for event in events
            if team_query in event.title.casefold()
        ]
    if favorites:
        events = [
            event
            for event in events
            if any(favorite in event.title.casefold() for favorite in favorites)
        ]
    return events


class YourCalendarHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/events":
            self.handle_events(parsed.query)
            return
        if parsed.path == "/api/leagues":
            self.handle_leagues(parsed.query)
            return
        if parsed.path == "/api/open-apple":
            self.handle_open_apple()
            return
        if parsed.path == "/download/football.ics":
            self.serve_ics()
            return
        super().do_GET()

    def log_message(self, format: str, *args) -> None:
        return

    def handle_events(self, query: str) -> None:
        params = parse_qs(query)
        try:
            events = load_events(params)
            write_ics(events, OUTPUT_PATH, CALENDAR_NAME)
            use_sample = params.get("sample", ["false"])[0] == "true"
            self.send_json(
                {
                    "ok": True,
                    "mode": "sample" if use_sample else "live",
                    "count": len(events),
                    "events": [event_to_dict(event) for event in events],
                    "icsPath": str(OUTPUT_PATH),
                    "downloadUrl": "/download/football.ics",
                    "sourceNote": source_note(use_sample, len(events)),
                }
            )
        except (POCError, ValueError) as exc:
            self.send_json(
                {
                    "ok": False,
                    "error": str(exc),
                    "events": [],
                    "sourceNote": "Die Quelle konnte gerade nicht gelesen werden.",
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

    def handle_leagues(self, query: str) -> None:
        params = parse_qs(query)
        season_raw = params.get("season", [""])[0]
        season = int(season_raw) if season_raw.isdigit() else default_football_season()
        leagues = []
        for shortcut, name in OPENLIGADB_LEAGUES.items():
            teams = []
            try:
                raw_teams = fetch_json_list(f"{OPENLIGADB_BASE}/getavailableteams/{shortcut}/{season}")
                teams = sorted(
                    {
                        team.get("teamName")
                        for team in raw_teams
                        if team.get("teamName")
                    }
                )
            except POCError:
                teams = []
            leagues.append({"id": shortcut, "name": name, "teams": teams})
        self.send_json({"ok": True, "season": season, "leagues": leagues})

    def handle_open_apple(self) -> None:
        if platform.system() != "Darwin":
            self.send_json(
                {"ok": False, "error": "Apple Calendar import is only available on macOS."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        if not OUTPUT_PATH.exists():
            self.send_json(
                {"ok": False, "error": "No ICS file exists yet. Generate events first."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            subprocess.run(["open", str(OUTPUT_PATH)], check=True)
            self.send_json({"ok": True, "message": "Apple Calendar was opened."})
        except subprocess.CalledProcessError as exc:
            self.send_json(
                {"ok": False, "error": f"Could not open Apple Calendar: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def serve_ics(self) -> None:
        if not OUTPUT_PATH.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "No calendar file generated yet.")
            return
        content = OUTPUT_PATH.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/calendar; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="yourcalendar-football.ics"')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def source_note(use_sample: bool, count: int) -> str:
    if use_sample:
        return "Sample-Modus: Diese Termine sind Testdaten und keine echten Spiele."
    if count == 0:
        return (
            "OpenLigaDB liefert für diese Filter aktuell keine kommenden Termine. "
            "Saisonende, Liga-Auswahl oder Filter können der Grund sein."
        )
    return (
        "OpenLigaDB: freie Spielplan-/Ergebnisdaten für den POC. "
        "Für garantierte Realtime-Daten braucht es später einen Provider mit SLA."
    )


def main() -> None:
    host = "127.0.0.1"
    port = 8765
    server = ThreadingHTTPServer((host, port), YourCalendarHandler)
    print(f"YourCalendar UI: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
