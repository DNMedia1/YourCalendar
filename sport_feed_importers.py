from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from football_data_org import (
    FOOTBALL_DATA_TOKEN_ENV,
    events_by_team as football_data_events_by_team,
    fetch_bundesliga_matches,
    fetch_bundesliga_teams,
)
from sport_feed_registry import LEAGUE_IMPORT_CONFIGS, LeagueImportConfig, SPORT_FEED_MANIFEST_VERSION
from yourcalendar_model import CalendarEvent, EventCategory, SourceQuality
from yourcalendar_poc import DEFAULT_TIMEZONE, POCError


THESPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json"
THESPORTSDB_KEY_ENV = "THESPORTSDB_API_KEY"
JOLPICA_F1_BASE = "https://api.jolpi.ca/ergast/f1"


@dataclass(frozen=True)
class ImportedSportCalendar:
    feed_id: str
    name: str
    group_id: str
    subgroup_id: str
    sport_id: str
    sport_name: str
    league_name: str
    provider: str
    provider_key: str
    calendar_mode: str
    source_quality: str
    events: tuple[CalendarEvent, ...]
    source_warning: str | None = None

    def manifest_entry(self, generated_at: str) -> dict:
        return {
            "feedId": self.feed_id,
            "feedPath": f"/feeds/{self.feed_id}.ics",
            "name": self.name,
            "groupId": self.group_id,
            "subgroupId": self.subgroup_id,
            "sportId": self.sport_id,
            "sportName": self.sport_name,
            "leagueName": self.league_name,
            "provider": self.provider,
            "providerKey": self.provider_key,
            "calendarMode": self.calendar_mode,
            "sourceQuality": self.source_quality,
            "eventCount": len(self.events),
            "updatedAt": generated_at,
            "sourceWarning": self.source_warning,
        }


def stable_slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in slug.split("-") if part) or "calendar"


def fetch_json(url: str, headers: dict[str, str] | None = None, timeout_seconds: int = 20) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "YourCalendar-POC/0.1",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except Exception as exc:
        raise POCError(f"Could not fetch {url}: {exc}") from exc


def current_season(config: LeagueImportConfig, now: datetime | None = None) -> str:
    current = now or datetime.now(ZoneInfo(DEFAULT_TIMEZONE))
    if config.season_format == "football-year-range":
        start = current.year if current.month >= 7 else current.year - 1
        return f"{start}-{start + 1}"
    return str(current.year)


def import_sport_calendars(now: datetime | None = None) -> tuple[list[ImportedSportCalendar], list[dict]]:
    calendars: list[ImportedSportCalendar] = []
    errors: list[dict] = []
    for config in LEAGUE_IMPORT_CONFIGS:
        if not config.enabled:
            errors.append({"configId": config.config_id, "status": "skipped", "message": "Provider is not enabled for automatic imports."})
            continue
        try:
            if config.provider_key == "football-data":
                calendars.extend(import_football_data(config))
            elif config.provider_key == "thesportsdb":
                calendars.extend(import_thesportsdb(config, current_season(config, now)))
            elif config.provider_key == "jolpica-f1":
                calendars.append(import_jolpica_f1(config, now))
            else:
                errors.append({"configId": config.config_id, "status": "skipped", "message": "No importer is configured for this provider."})
        except Exception as exc:
            errors.append({"configId": config.config_id, "status": "error", "message": str(exc)})
    return calendars, errors


def sport_manifest_payload(calendars: list[ImportedSportCalendar], errors: list[dict], generated_at: str) -> dict:
    return {
        "version": SPORT_FEED_MANIFEST_VERSION,
        "generatedAt": generated_at,
        "calendars": [calendar.manifest_entry(generated_at) for calendar in calendars],
        "errors": errors,
    }


def import_football_data(config: LeagueImportConfig) -> list[ImportedSportCalendar]:
    if not os.getenv(FOOTBALL_DATA_TOKEN_ENV, "").strip():
        raise POCError(f"{FOOTBALL_DATA_TOKEN_ENV} is not configured.")
    teams = fetch_bundesliga_teams()
    matches = fetch_bundesliga_matches()
    grouped_events = football_data_events_by_team(teams, matches)
    calendars = []
    for team in teams:
        feed_id = f"sport-{config.subgroup_id}-{stable_slug(config.league_name)}-{team.team_id}-{stable_slug(team.name)}"
        events = tuple(grouped_events.get(team.team_id, []))
        calendars.append(
            ImportedSportCalendar(
                feed_id=feed_id,
                name=f"{team.short_name} {config.league_name}",
                group_id=config.group_id,
                subgroup_id=config.subgroup_id,
                sport_id=config.sport_id,
                sport_name=config.sport_name,
                league_name=config.league_name,
                provider=config.provider,
                provider_key=config.provider_key,
                calendar_mode="team",
                source_quality=config.source_quality,
                events=events,
                source_warning="football-data.org requires FOOTBALL_DATA_API_KEY and provider attribution.",
            )
        )
    return calendars


def thesportsdb_key() -> str:
    return os.getenv(THESPORTSDB_KEY_ENV, "123").strip() or "123"


def thesportsdb_url(endpoint: str, params: dict[str, str]) -> str:
    return f"{THESPORTSDB_BASE}/{thesportsdb_key()}/{endpoint}?{urllib.parse.urlencode(params)}"


def import_thesportsdb(config: LeagueImportConfig, season: str) -> list[ImportedSportCalendar]:
    league = find_thesportsdb_league(config.league_name)
    league_id = str(league.get("idLeague") or config.league_id or "").strip()
    if not league_id:
        raise POCError(f"TheSportsDB league id could not be resolved for {config.league_name}.")
    events = fetch_thesportsdb_events_for_league(league_id, season, config)
    if config.calendar_mode == "team":
        teams = fetch_thesportsdb_teams(config.league_name)
        return thesportsdb_team_calendars(config, teams, events)
    feed_id = f"sport-{config.subgroup_id}-{stable_slug(config.league_name)}"
    return [
        ImportedSportCalendar(
            feed_id=feed_id,
            name=f"{config.league_name} Kalender",
            group_id=config.group_id,
            subgroup_id=config.subgroup_id,
            sport_id=config.sport_id,
            sport_name=config.sport_name,
            league_name=config.league_name,
            provider=config.provider,
            provider_key=config.provider_key,
            calendar_mode="competition",
            source_quality=config.source_quality,
            events=tuple(events),
            source_warning="TheSportsDB is community data; coverage can be incomplete.",
        )
    ]


def find_thesportsdb_league(league_name: str) -> dict:
    payload = fetch_json(thesportsdb_url("all_leagues.php", {}))
    target = league_name.casefold()
    for league in payload.get("leagues") or []:
        name = str(league.get("strLeague") or "").casefold()
        alternate = str(league.get("strLeagueAlternate") or "").casefold()
        if name == target or target in alternate:
            return league
    raise POCError(f"TheSportsDB league not found: {league_name}")


def fetch_thesportsdb_teams(league_name: str) -> list[dict]:
    payload = fetch_json(thesportsdb_url("search_all_teams.php", {"l": league_name}))
    teams = payload.get("teams") or []
    return teams if isinstance(teams, list) else []


def fetch_thesportsdb_events_for_league(league_id: str, season: str, config: LeagueImportConfig) -> list[CalendarEvent]:
    payload = fetch_json(thesportsdb_url("eventsseason.php", {"id": league_id, "s": season}))
    raw_events = payload.get("events") or []
    return sorted(
        [
            thesportsdb_event_to_calendar_event(raw_event, config)
            for raw_event in raw_events
            if raw_event.get("dateEvent")
        ],
        key=lambda event: event.starts_at,
    )


def thesportsdb_team_calendars(config: LeagueImportConfig, teams: list[dict], events: list[CalendarEvent]) -> list[ImportedSportCalendar]:
    calendars = []
    for team in teams:
        team_id = str(team.get("idTeam") or "").strip()
        team_name = str(team.get("strTeam") or "").strip()
        if not team_id or not team_name:
            continue
        team_events = tuple(event for event in events if team_name.casefold() in event.title.casefold())
        feed_id = f"sport-{config.subgroup_id}-{stable_slug(config.league_name)}-{team_id}-{stable_slug(team_name)}"
        calendars.append(
            ImportedSportCalendar(
                feed_id=feed_id,
                name=f"{team_name} {config.league_name}",
                group_id=config.group_id,
                subgroup_id=config.subgroup_id,
                sport_id=config.sport_id,
                sport_name=config.sport_name,
                league_name=config.league_name,
                provider=config.provider,
                provider_key=config.provider_key,
                calendar_mode="team",
                source_quality=config.source_quality,
                events=team_events,
                source_warning="TheSportsDB is community data; verify missing fixtures before production.",
            )
        )
    return calendars


def thesportsdb_event_to_calendar_event(raw_event: dict, config: LeagueImportConfig) -> CalendarEvent:
    tz = ZoneInfo(DEFAULT_TIMEZONE)
    date_value = str(raw_event.get("dateEvent") or "").strip()
    time_value = str(raw_event.get("strTime") or "12:00:00").replace("Z", "").replace("+00:00", "")
    if len(time_value) == 5:
        time_value = f"{time_value}:00"
    try:
        starts_at = datetime.fromisoformat(f"{date_value}T{time_value}").replace(tzinfo=timezone.utc).astimezone(tz)
    except ValueError:
        starts_at = datetime.fromisoformat(f"{date_value}T12:00:00").replace(tzinfo=tz)
    event_id = raw_event.get("idEvent") or f"{config.config_id}-{starts_at.isoformat()}"
    title = raw_event.get("strEvent") or f"{raw_event.get('strHomeTeam') or 'Home'} vs {raw_event.get('strAwayTeam') or 'Away'}"
    return CalendarEvent(
        uid=f"thesportsdb-{event_id}@yourcalendar.local",
        title=str(title),
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=2),
        source="TheSportsDB",
        category=EventCategory.SPORTS,
        location=raw_event.get("strVenue"),
        description=f"Generated by YourCalendar.\nSource: TheSportsDB.\nLeague: {config.league_name}.",
        source_quality=SourceQuality.COMMUNITY,
        external_id=str(event_id),
        quality_notes=("TheSportsDB is community data and may be incomplete.",),
    )


def import_jolpica_f1(config: LeagueImportConfig, now: datetime | None = None) -> ImportedSportCalendar:
    year = (now or datetime.now(ZoneInfo(DEFAULT_TIMEZONE))).year
    payload = fetch_json(f"{JOLPICA_F1_BASE}/{year}.json")
    races = ((payload.get("MRData") or {}).get("RaceTable") or {}).get("Races") or []
    events = tuple(jolpica_race_to_event(race, config) for race in races)
    return ImportedSportCalendar(
        feed_id="sport-formula-1-formula-1",
        name="Formel 1 Kalender",
        group_id=config.group_id,
        subgroup_id=config.subgroup_id,
        sport_id=config.sport_id,
        sport_name=config.sport_name,
        league_name=config.league_name,
        provider=config.provider,
        provider_key=config.provider_key,
        calendar_mode="competition",
        source_quality=config.source_quality,
        events=events,
        source_warning="Jolpica F1 is community data; verify session-level granularity before production.",
    )


def jolpica_race_to_event(race: dict, config: LeagueImportConfig) -> CalendarEvent:
    tz = ZoneInfo(DEFAULT_TIMEZONE)
    date_value = race.get("date")
    time_value = str(race.get("time") or "12:00:00Z").replace("Z", "+00:00")
    starts_at = datetime.fromisoformat(f"{date_value}T{time_value}").astimezone(tz)
    race_id = race.get("round") or stable_slug(str(race.get("raceName") or starts_at.date()))
    circuit = race.get("Circuit") or {}
    location = circuit.get("circuitName")
    return CalendarEvent(
        uid=f"jolpica-f1-{race_id}-{starts_at.date()}@yourcalendar.local",
        title=str(race.get("raceName") or "Formula 1 Grand Prix"),
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=2),
        source=config.provider,
        category=EventCategory.SPORTS,
        location=location,
        description=f"Generated by YourCalendar.\nSource: {config.provider}.\nRound: {race_id}.",
        source_quality=SourceQuality.COMMUNITY,
        external_id=str(race_id),
        quality_notes=("Race calendar only; practice and qualifying sessions need separate mapping.",),
    )
