from __future__ import annotations

import os
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from yourcalendar_model import CalendarEvent, EventCategory, EventStatus, SourceQuality
from yourcalendar_poc import DEFAULT_TIMEZONE, POCError


FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"
FOOTBALL_DATA_TOKEN_ENV = "FOOTBALL_DATA_API_KEY"
FOOTBALL_DATA_PROVIDER_LABEL = "football-data.org"
DEFAULT_COMPETITION = "BL1"


@dataclass(frozen=True)
class FootballDataTeam:
    team_id: int
    name: str
    short_name: str
    tla: str
    venue: str | None = None

    @property
    def feed_id(self) -> str:
        return football_data_team_feed_id(self.team_id, self.name)


def football_data_token() -> str:
    return os.getenv(FOOTBALL_DATA_TOKEN_ENV, "").strip()


def football_data_team_feed_id(team_id: int | str, name: str) -> str:
    return f"football-data-bl1-{team_id}-{stable_slug(name)}"


def stable_slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in slug.split("-") if part) or "team"


def football_data_get(path: str, query: dict[str, str] | None = None, token: str | None = None) -> dict:
    api_token = (token if token is not None else football_data_token()).strip()
    if not api_token:
        raise POCError(f"{FOOTBALL_DATA_TOKEN_ENV} is required for football-data.org imports.")
    encoded_query = f"?{urllib.parse.urlencode(query)}" if query else ""
    separator = "" if path.startswith("/") else "/"
    url = f"{FOOTBALL_DATA_BASE}{separator}{path}{encoded_query}"
    return fetch_json_with_headers(url, {"X-Auth-Token": api_token})


def fetch_json_with_headers(url: str, headers: dict[str, str]) -> dict:
    # Reuse the same error handling style as yourcalendar_poc.fetch_json while
    # adding provider auth headers.
    import json
    import urllib.error
    import urllib.request

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "YourCalendar-POC/0.1",
            **headers,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except urllib.error.HTTPError as exc:
        raise POCError(f"HTTP {exc.code} while fetching {url}") from exc
    except urllib.error.URLError as exc:
        raise POCError(f"Network error while fetching {url}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise POCError(f"Response was not valid JSON: {url}") from exc


def fetch_bundesliga_teams(token: str | None = None) -> list[FootballDataTeam]:
    payload = football_data_get(f"/competitions/{DEFAULT_COMPETITION}/teams", token=token)
    teams = payload.get("teams") or []
    normalized: list[FootballDataTeam] = []
    for team in teams:
        team_id = team.get("id")
        name = str(team.get("name") or team.get("shortName") or "").strip()
        if not team_id or not name:
            continue
        normalized.append(
            FootballDataTeam(
                team_id=int(team_id),
                name=name,
                short_name=str(team.get("shortName") or name).strip(),
                tla=str(team.get("tla") or "").strip(),
                venue=str(team.get("venue") or "").strip() or None,
            )
        )
    return sorted(normalized, key=lambda team: team.name.casefold())


def fetch_bundesliga_matches(token: str | None = None, status: str = "SCHEDULED") -> list[dict]:
    payload = football_data_get(
        f"/competitions/{DEFAULT_COMPETITION}/matches",
        {"status": status},
        token=token,
    )
    matches = payload.get("matches") or []
    return matches if isinstance(matches, list) else []


def fetch_football_data_team_events(
    team_id: int,
    competition: str = DEFAULT_COMPETITION,
    status: str = "SCHEDULED",
    tz_name: str = DEFAULT_TIMEZONE,
    token: str | None = None,
) -> list[CalendarEvent]:
    payload = football_data_get(
        f"/teams/{team_id}/matches",
        {"competitions": competition, "status": status},
        token=token,
    )
    matches = payload.get("matches") or []
    return sorted(
        [football_data_match_to_event(match, tz_name) for match in matches],
        key=lambda event: event.starts_at,
    )


def events_by_team(teams: list[FootballDataTeam], matches: list[dict], tz_name: str = DEFAULT_TIMEZONE) -> dict[int, list[CalendarEvent]]:
    grouped = {team.team_id: [] for team in teams}
    for match in matches:
        event = football_data_match_to_event(match, tz_name)
        for side in ("homeTeam", "awayTeam"):
            team_id = (match.get(side) or {}).get("id")
            if team_id in grouped:
                grouped[team_id].append(event)
    return {
        team_id: sorted(events, key=lambda event: event.starts_at)
        for team_id, events in grouped.items()
    }


def football_data_match_to_event(match: dict, tz_name: str = DEFAULT_TIMEZONE) -> CalendarEvent:
    tz = ZoneInfo(tz_name)
    starts_at = parse_utc_date(match.get("utcDate"), tz)
    home = match.get("homeTeam") or {}
    away = match.get("awayTeam") or {}
    home_name = str(home.get("name") or "Home").strip()
    away_name = str(away.get("name") or "Away").strip()
    match_id = match.get("id") or f"{home.get('id', 'home')}-{away.get('id', 'away')}-{starts_at.isoformat()}"
    competition = match.get("competition") or {}
    status = map_match_status(str(match.get("status") or "SCHEDULED"))
    venue = str(match.get("venue") or "").strip() or None
    description = "\n".join(
        [
            "Generated by YourCalendar.",
            "Source: football-data.org.",
            f"Competition: {competition.get('name') or DEFAULT_COMPETITION}.",
            f"Matchday: {match.get('matchday') or 'unknown'}.",
            f"Status: {match.get('status') or 'unknown'}.",
        ]
    )
    return CalendarEvent(
        uid=f"football-data-{match_id}@yourcalendar.local",
        title=f"{home_name} vs {away_name}",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=2),
        source=FOOTBALL_DATA_PROVIDER_LABEL,
        category=EventCategory.SPORTS,
        location=venue,
        description=description,
        status=status,
        source_quality=SourceQuality.PAID_PROVIDER,
        external_id=str(match_id),
        quality_notes=(
            "football-data.org requires a configured API token.",
            "Provider terms and attribution must be kept visible for production use.",
        ),
    )


def parse_utc_date(value: str | None, tz: ZoneInfo) -> datetime:
    if not value:
        raise POCError("football-data.org match is missing utcDate.")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(tz)


def map_match_status(status: str) -> EventStatus:
    normalized = status.strip().upper()
    if normalized in {"CANCELLED", "AWARDED"}:
        return EventStatus.CANCELLED
    if normalized in {"POSTPONED", "SUSPENDED"}:
        return EventStatus.POSTPONED
    if normalized in {"TIMED", "SCHEDULED", "IN_PLAY", "PAUSED", "FINISHED"}:
        return EventStatus.CONFIRMED
    return EventStatus.UNKNOWN
