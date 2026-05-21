#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import platform
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

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
    render_ics,
    write_ics,
)


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
OUTPUT_PATH = ROOT / DEFAULT_OUTPUT
FEED_CACHE_DIR = ROOT / "output" / "feeds"
CALENDAR_NAME = "YourCalendar German Football"
SAMPLE_CALENDAR_NAME = "YourCalendar Sample Football"
CURRENT_FEED_ID = "current"
FEED_PARAM_KEYS = ("sample", "leagues", "team", "favorites", "includePast", "season")


@dataclass(frozen=True)
class PublishedCalendar:
    feed_id: str
    name: str
    description: str
    params: dict[str, str]
    sample: bool = False


PUBLISHED_CALENDARS = {
    "football-germany": PublishedCalendar(
        feed_id="football-germany",
        name=CALENDAR_NAME,
        description="Bundesliga, 2. Bundesliga, 3. Liga und DFB-Pokal aus OpenLigaDB.",
        params={
            "sample": "false",
            "leagues": "bl1,bl2,bl3,dfb",
            "includePast": "false",
        },
    ),
    "sample-ksc": PublishedCalendar(
        feed_id="sample-ksc",
        name=SAMPLE_CALENDAR_NAME,
        description="Sample-Feed mit klar markierten Testspielen.",
        params={
            "sample": "true",
            "leagues": "bl1,bl2,bl3",
            "includePast": "true",
        },
        sample=True,
    ),
}


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
        "sourceQuality": event.source_quality,
        "category": event.category,
        "allDay": event.all_day,
        "qualityNotes": list(event.quality_notes),
        "description": event.description,
        "status": event.status,
    }


def selected_leagues(params: dict[str, list[str]]) -> list[str]:
    raw = params.get("leagues", ["bl1,bl2,bl3"])[0]
    leagues = [item.strip() for item in raw.split(",") if item.strip()]
    return [league for league in leagues if league in OPENLIGADB_LEAGUES]


def normalize_feed_params(params: dict[str, list[str]]) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for key in FEED_PARAM_KEYS:
        values = [value for value in params.get(key, []) if value != ""]
        if values:
            normalized[key] = values
    if "sample" not in normalized:
        normalized["sample"] = ["false"]
    if "leagues" not in normalized:
        normalized["leagues"] = ["bl1,bl2,bl3"]
    if "includePast" not in normalized:
        normalized["includePast"] = ["false"]
    return normalized


def params_from_calendar(calendar: PublishedCalendar) -> dict[str, list[str]]:
    return {key: [value] for key, value in calendar.params.items()}


def calendar_name_for_params(params: dict[str, list[str]]) -> str:
    return SAMPLE_CALENDAR_NAME if params.get("sample", ["false"])[0] == "true" else CALENDAR_NAME


def feed_path_for_params(params: dict[str, list[str]]) -> str:
    normalized = normalize_feed_params(params)
    query_items = [(key, normalized[key][0]) for key in FEED_PARAM_KEYS if key in normalized]
    query = urlencode(query_items)
    return f"/feeds/{CURRENT_FEED_ID}.ics?{query}" if query else f"/feeds/{CURRENT_FEED_ID}.ics"


def published_feed_path(feed_id: str) -> str:
    if feed_id not in PUBLISHED_CALENDARS:
        raise KeyError(feed_id)
    return f"/feeds/{feed_id}.ics"


def feed_filename(feed_id: str) -> str:
    safe_id = "".join(char for char in feed_id if char.isalnum() or char in ("-", "_"))
    return f"yourcalendar-{safe_id or CURRENT_FEED_ID}.ics"


def cached_feed_path(feed_id: str) -> Path:
    return FEED_CACHE_DIR / feed_filename(feed_id)


def load_cached_feed(feed_id: str, query: str = "") -> str | None:
    if query or feed_id not in PUBLISHED_CALENDARS:
        return None
    path = cached_feed_path(feed_id)
    if not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def resolve_feed(feed_id: str, query: str) -> tuple[str, dict[str, list[str]], bool]:
    if feed_id == CURRENT_FEED_ID:
        params = normalize_feed_params(parse_qs(query))
        return calendar_name_for_params(params), params, params.get("sample", ["false"])[0] == "true"

    calendar = PUBLISHED_CALENDARS[feed_id]
    return calendar.name, params_from_calendar(calendar), calendar.sample


def render_feed(feed_id: str, query: str = "") -> tuple[str, bool]:
    calendar_name, params, is_sample = resolve_feed(feed_id, query)
    return render_ics(load_events(params), calendar_name), is_sample


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


SOURCES_PATH = ROOT / "sources.json"


def build_source(data: dict) -> tuple[dict | None, str | None]:
    for field in ("name", "url"):
        if not str(data.get(field, "")).strip():
            return None, f"Missing required field: {field}"
    return {
        "id": str(uuid.uuid4()),
        "name": str(data["name"]).strip(),
        "url": str(data["url"]).strip(),
        "category": str(data.get("category", "")).strip(),
        "license": str(data.get("license", "")).strip(),
        "status": str(data.get("status", "draft")).strip() or "draft",
        "lastImport": None,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }, None


class YourCalendarHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/sources":
            self.handle_sources_get()
            return
        if parsed.path.startswith("/api/sources/"):
            source_id = parsed.path.removeprefix("/api/sources/")
            self.handle_sources_get_one(source_id)
            return
        if parsed.path == "/api/events":
            self.handle_events(parsed.query)
            return
        if parsed.path == "/api/leagues":
            self.handle_leagues(parsed.query)
            return
        if parsed.path == "/api/calendars":
            self.handle_calendars()
            return
        if parsed.path == "/api/open-apple":
            self.handle_open_apple(parsed.query)
            return
        if parsed.path.startswith("/feeds/") and parsed.path.endswith(".ics"):
            self.handle_feed(parsed)
            return
        if parsed.path == "/download/football.ics":
            self.handle_legacy_download(parsed.query)
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/sources":
            self.handle_sources_post()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not supported")

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/sources/"):
            source_id = parsed.path.removeprefix("/api/sources/")
            self.handle_sources_patch(source_id)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not supported")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/sources/"):
            source_id = parsed.path.removeprefix("/api/sources/")
            self.handle_sources_delete(source_id)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not supported")

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/feeds/") and parsed.path.endswith(".ics"):
            self.handle_feed(parsed, send_body=False)
            return
        super().do_HEAD()

    def log_message(self, format: str, *args) -> None:
        return

    def handle_events(self, query: str) -> None:
        params = parse_qs(query)
        try:
            normalized_params = normalize_feed_params(params)
            events = load_events(params)
            use_sample = normalized_params.get("sample", ["false"])[0] == "true"
            feed_url = feed_path_for_params(normalized_params)
            self.send_json(
                {
                    "ok": True,
                    "mode": "sample" if use_sample else "live",
                    "count": len(events),
                    "events": [event_to_dict(event) for event in events],
                    "feedUrl": feed_url,
                    "subscribeUrl": self.absolute_url(feed_url),
                    "downloadUrl": feed_url,
                    "sampleFeedUrl": published_feed_path("sample-ksc"),
                    "publishedFeedUrl": published_feed_path("football-germany"),
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

    def handle_calendars(self) -> None:
        calendars = [
            {
                "id": calendar.feed_id,
                "name": calendar.name,
                "description": calendar.description,
                "sample": calendar.sample,
                "feedUrl": published_feed_path(calendar.feed_id),
                "subscribeUrl": self.absolute_url(published_feed_path(calendar.feed_id)),
            }
            for calendar in PUBLISHED_CALENDARS.values()
        ]
        self.send_json({"ok": True, "calendars": calendars})

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

    def handle_open_apple(self, query: str) -> None:
        if platform.system() != "Darwin":
            self.send_json(
                {"ok": False, "error": "Apple Calendar import is only available on macOS."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            params = normalize_feed_params(parse_qs(query))
            write_ics(load_events(params), OUTPUT_PATH, calendar_name_for_params(params))
            subprocess.run(["open", str(OUTPUT_PATH)], check=True)
            self.send_json({"ok": True, "message": "Apple Calendar was opened."})
        except (POCError, ValueError) as exc:
            self.send_json(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_GATEWAY,
            )
        except subprocess.CalledProcessError as exc:
            self.send_json(
                {"ok": False, "error": f"Could not open Apple Calendar: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_feed(self, parsed, send_body: bool = True) -> None:
        feed_id = parsed.path.removeprefix("/feeds/").removesuffix(".ics")
        try:
            self.serve_feed(feed_id, parsed.query, disposition="inline", send_body=send_body)
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown calendar feed.")
        except (POCError, ValueError) as exc:
            self.send_error(HTTPStatus.BAD_GATEWAY, str(exc))

    def handle_legacy_download(self, query: str) -> None:
        try:
            self.serve_feed(CURRENT_FEED_ID, query, disposition="attachment")
        except (POCError, ValueError) as exc:
            self.send_error(HTTPStatus.BAD_GATEWAY, str(exc))

    def handle_open_apple(self, query: str) -> None:
        if platform.system() != "Darwin":
            self.send_json(
                {"ok": False, "error": "Apple Calendar import is only available on macOS."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            params = normalize_feed_params(parse_qs(query))
            write_ics(load_events(params), OUTPUT_PATH, calendar_name_for_params(params))
            subprocess.run(["open", str(OUTPUT_PATH)], check=True)
            self.send_json({"ok": True, "message": "Apple Calendar was opened."})
        except (POCError, ValueError) as exc:
            self.send_json(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_GATEWAY,
            )
        except subprocess.CalledProcessError as exc:
            self.send_json(
                {"ok": False, "error": f"Could not open Apple Calendar: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_sources_get(self) -> None:
        sources = load_sources()
        self.send_json({"ok": True, "sources": sources})

    def handle_sources_get_one(self, source_id: str) -> None:
        sources = load_sources()
        for source in sources:
            if source["id"] == source_id:
                self.send_json({"ok": True, "source": source})
                return
        self.send_error(HTTPStatus.NOT_FOUND, "Source not found")

    def handle_sources_post(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
            return
        source, error = build_source(data)
        if error:
            self.send_json({"ok": False, "error": error}, status=HTTPStatus.BAD_REQUEST)
            return
        sources = load_sources()
        sources.append(source)
        save_sources(sources)
        self.send_json({"ok": True, "source": source}, status=HTTPStatus.CREATED)

    def handle_sources_patch(self, source_id: str) -> None:
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
            return
        sources = load_sources()
        for source in sources:
            if source["id"] == source_id:
                # Update allowed fields
                if "name" in data:
                    source["name"] = data["name"]
                if "url" in data:
                    source["url"] = data["url"]
                if "category" in data:
                    source["category"] = data["category"]
                if "license" in data:
                    source["license"] = data["license"]
                if "status" in data:
                    source["status"] = data["status"]
                if "lastImport" in data:
                    source["lastImport"] = data["lastImport"]
                source["updatedAt"] = datetime.now(timezone.utc).isoformat()
                save_sources(sources)
                self.send_json({"ok": True, "source": source})
                return
        self.send_error(HTTPStatus.NOT_FOUND, "Source not found")

    def handle_sources_delete(self, source_id: str) -> None:
        sources = load_sources()
        new_sources = [s for s in sources if s["id"] != source_id]
        if len(new_sources) == len(sources):
            self.send_error(HTTPStatus.NOT_FOUND, "Source not found")
            return
        save_sources(new_sources)
        self.send_json({"ok": True, "message": "Source deleted"})

    def serve_feed(self, feed_id: str, query: str, disposition: str, send_body: bool = True) -> None:
        content = load_cached_feed(feed_id, query)
        if content is None:
            content, is_sample = render_feed(feed_id, query)
        else:
            is_sample = PUBLISHED_CALENDARS[feed_id].sample
        content_bytes = content.encode("utf-8")
        if is_sample and "[SAMPLE]" not in content:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Sample feed is not clearly marked.")
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/calendar; charset=utf-8")
        self.send_header("Content-Disposition", f'{disposition}; filename="{feed_filename(feed_id)}"')
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(content_bytes)))
        self.end_headers()
        if send_body:
            self.wfile.write(content_bytes)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def absolute_url(self, path: str) -> str:
        public_base = os.environ.get("YOURCALENDAR_PUBLIC_BASE_URL", "").rstrip("/")
        if public_base:
            return f"{public_base}{path}"
        forwarded_proto = self.headers.get("X-Forwarded-Proto")
        scheme = forwarded_proto.split(",")[0].strip() if forwarded_proto else "http"
        host = self.headers.get("Host", "127.0.0.1:8765")
        return f"{scheme}://{host}{path}"


def load_sources() -> list:
    if not SOURCES_PATH.exists():
        return []
    try:
        data = json.loads(SOURCES_PATH.read_text())
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def save_sources(sources: list) -> None:
    SOURCES_PATH.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n")


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
