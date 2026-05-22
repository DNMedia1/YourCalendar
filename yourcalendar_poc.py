#!/usr/bin/env python3
"""
YourCalendar POC CLI.

Fetch upcoming Karlsruher SC events from a sports source, normalize them, and
publish them as an iCalendar file that Apple Calendar, Google Calendar, and
Outlook can import or subscribe to once hosted.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from yourcalendar_model import CalendarEvent, EventCategory, EventStatus, SourceQuality


DEFAULT_TEAM_QUERY = "Karlsruher SC"
DEFAULT_THESPORTSDB_TEAM_ID = "135293"
DEFAULT_TIMEZONE = "Europe/Berlin"
DEFAULT_OUTPUT = "output/ksc.ics"
THESPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json"
OPENLIGADB_BASE = "https://api.openligadb.de"
NAGER_DATE_BASE = "https://date.nager.at/api/v3"
OPENLIGADB_LEAGUES = {
    "bl1": "1. Bundesliga",
    "bl2": "2. Bundesliga",
    "bl3": "3. Liga",
    "dfb": "DFB-Pokal",
}
DEFAULT_HOLIDAY_COUNTRY = "DE"
DEFAULT_HOLIDAY_SUBDIVISION = ""


class POCError(RuntimeError):
    pass


def fetch_json(url: str, timeout_seconds: int = 20) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "YourCalendar-POC/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except urllib.error.HTTPError as exc:
        raise POCError(f"HTTP {exc.code} while fetching {url}") from exc
    except urllib.error.URLError as exc:
        raise POCError(f"Network error while fetching {url}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise POCError(f"Response was not valid JSON: {url}") from exc


def fetch_json_list(url: str, timeout_seconds: int = 20) -> list[dict]:
    payload = fetch_json(url, timeout_seconds)
    if isinstance(payload, list):
        return payload
    raise POCError(f"Response was not a JSON list: {url}")


def find_thesportsdb_team_id(api_key: str, team_query: str) -> str:
    encoded = urllib.parse.urlencode({"t": team_query})
    url = f"{THESPORTSDB_BASE}/{api_key}/searchteams.php?{encoded}"
    payload = fetch_json(url)
    teams = payload.get("teams") or []
    if not teams:
        raise POCError(f"No team found in TheSportsDB for query: {team_query}")

    normalized_query = team_query.casefold()
    exact = [
        team
        for team in teams
        if (team.get("strTeam") or "").casefold() == normalized_query
    ]
    if not exact:
        names = ", ".join(team.get("strTeam", "unknown") for team in teams[:5])
        raise POCError(
            "TheSportsDB search did not return an exact team match for "
            f"{team_query!r}. First matches: {names}. Use --thesportsdb-team-id."
        )

    selected = exact[0]
    team_id = selected.get("idTeam")
    if not team_id:
        raise POCError(f"TheSportsDB team result has no idTeam: {selected}")
    return team_id


def parse_thesportsdb_datetime(raw_event: dict, tz: ZoneInfo) -> datetime:
    date_value = raw_event.get("dateEvent")
    time_value = raw_event.get("strTime") or "15:30:00"
    if not date_value:
        raise POCError(f"Event has no dateEvent: {raw_event}")

    time_value = time_value.replace("+00:00", "").replace("Z", "")
    if len(time_value) == 5:
        time_value = f"{time_value}:00"

    try:
        naive = datetime.fromisoformat(f"{date_value}T{time_value}")
    except ValueError:
        naive = datetime.fromisoformat(f"{date_value}T15:30:00")

    # TheSportsDB often stores football event times as UTC-like values, but this
    # is not consistently documented for every league. We keep this visible in
    # the generated description so the POC can validate time quality.
    if naive.tzinfo is None:
        return naive.replace(tzinfo=timezone.utc).astimezone(tz)
    return naive.astimezone(tz)


def event_title(raw_event: dict) -> str:
    event_name = raw_event.get("strEvent")
    if event_name:
        return event_name

    home = raw_event.get("strHomeTeam") or "Home"
    away = raw_event.get("strAwayTeam") or "Away"
    return f"{home} vs {away}"


def fetch_thesportsdb_events(
    api_key: str,
    team_query: str,
    team_id: str | None,
    tz_name: str,
) -> list[CalendarEvent]:
    tz = ZoneInfo(tz_name)
    team_id = team_id or find_thesportsdb_team_id(api_key, team_query)
    url = f"{THESPORTSDB_BASE}/{api_key}/eventsnext.php?{urllib.parse.urlencode({'id': team_id})}"
    payload = fetch_json(url)
    raw_events = payload.get("events") or []

    events: list[CalendarEvent] = []
    for raw_event in raw_events:
        starts_at = parse_thesportsdb_datetime(raw_event, tz)
        ends_at = starts_at + timedelta(hours=2)
        event_id = raw_event.get("idEvent") or f"{team_id}-{starts_at.isoformat()}"
        source_url = raw_event.get("strWebsite")
        events.append(
            CalendarEvent(
                uid=f"thesportsdb-{event_id}@yourcalendar.local",
                title=event_title(raw_event),
                starts_at=starts_at,
                ends_at=ends_at,
                category=EventCategory.SPORTS,
                location=raw_event.get("strVenue"),
                source="TheSportsDB",
                source_quality=SourceQuality.COMMUNITY,
                source_url=source_url,
                description=build_description(raw_event, team_id),
                external_id=event_id,
                quality_notes=(
                    "Kickoff time requires production verification.",
                    "Free/demo schedule coverage may be incomplete.",
                ),
            )
        )

    return sorted(events, key=lambda event: event.starts_at)


def default_football_season(now: datetime | None = None) -> int:
    current = now or datetime.now(ZoneInfo(DEFAULT_TIMEZONE))
    return current.year if current.month >= 7 else current.year - 1


def parse_openligadb_datetime(value: str, tz: ZoneInfo) -> datetime:
    raw = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def openligadb_match_title(match: dict) -> str:
    team1 = (match.get("team1") or {}).get("teamName") or "Team 1"
    team2 = (match.get("team2") or {}).get("teamName") or "Team 2"
    return f"{team1} vs {team2}"


def openligadb_result_label(match: dict) -> str | None:
    results = match.get("matchResults") or []
    end_results = [result for result in results if result.get("resultTypeID") == 2]
    selected = end_results[0] if end_results else (results[-1] if results else None)
    if not selected:
        return None
    points1 = selected.get("pointsTeam1")
    points2 = selected.get("pointsTeam2")
    if points1 is None or points2 is None:
        return None
    return f"{points1}:{points2}"


def fetch_openligadb_events(
    league: str,
    season: int | None = None,
    upcoming_only: bool = True,
    tz_name: str = DEFAULT_TIMEZONE,
) -> list[CalendarEvent]:
    if league not in OPENLIGADB_LEAGUES:
        raise POCError(f"Unsupported OpenLigaDB league: {league}")

    season = season or default_football_season()
    tz = ZoneInfo(tz_name)
    url = f"{OPENLIGADB_BASE}/getmatchdata/{league}/{season}"
    raw_matches = fetch_json_list(url)
    now = datetime.now(tz)
    events: list[CalendarEvent] = []

    for match in raw_matches:
        starts_at = parse_openligadb_datetime(match["matchDateTime"], tz)
        if upcoming_only and starts_at < now:
            continue

        match_id = match.get("matchID") or f"{league}-{starts_at.isoformat()}"
        result = openligadb_result_label(match)
        description_parts = [
            "Generated by YourCalendar POC.",
            "Source: OpenLigaDB.",
            f"League: {OPENLIGADB_LEAGUES[league]}.",
            f"Season: {season}.",
            "Quality note: OpenLigaDB is suitable for a POC, but not a guaranteed official realtime SLA.",
        ]
        if result:
            description_parts.append(f"Result: {result}.")

        events.append(
            CalendarEvent(
                uid=f"openligadb-{league}-{match_id}@yourcalendar.local",
                title=openligadb_match_title(match),
                starts_at=starts_at,
                ends_at=starts_at + timedelta(hours=2),
                source="OpenLigaDB",
                category=EventCategory.SPORTS,
                description="\n".join(description_parts),
                status=EventStatus.CONFIRMED,
                source_quality=SourceQuality.COMMUNITY,
                external_id=str(match_id),
                quality_notes=(
                    "OpenLigaDB is suitable for the POC, but not a guaranteed official realtime SLA.",
                ),
            )
        )

    return sorted(events, key=lambda event: event.starts_at)


def fetch_openligadb_multi_league_events(
    leagues: list[str],
    season: int | None = None,
    upcoming_only: bool = True,
    tz_name: str = DEFAULT_TIMEZONE,
) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []
    for league in leagues:
        events.extend(fetch_openligadb_events(league, season, upcoming_only, tz_name))
    return sorted(events, key=lambda event: event.starts_at)


def stable_slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in slug.split("-") if part) or "event"


def holiday_applies_to_subdivision(holiday: dict, subdivision: str) -> bool:
    counties = holiday.get("counties")
    if not subdivision:
        return bool(holiday.get("global")) or not counties
    return bool(holiday.get("global")) or subdivision in (counties or [])


def nager_holiday_url(year: int, country_code: str) -> str:
    return f"{NAGER_DATE_BASE}/PublicHolidays/{year}/{country_code.upper()}"


def nager_holiday_to_event(
    holiday: dict,
    year: int,
    country_code: str,
    subdivision: str,
    tz_name: str,
) -> CalendarEvent:
    tz = ZoneInfo(tz_name)
    date_value = holiday.get("date")
    local_name = str(holiday.get("localName") or holiday.get("name") or "").strip()
    if not date_value or not local_name:
        raise POCError(f"Nager.Date holiday is missing date or name: {holiday}")

    starts_at = datetime.fromisoformat(date_value).replace(tzinfo=tz)
    ends_at = starts_at + timedelta(days=1)
    types = ", ".join(holiday.get("types") or [])
    counties = holiday.get("counties")
    region_note = subdivision or ("national" if holiday.get("global") else "regional")
    return CalendarEvent(
        uid=f"nager-{country_code.lower()}-{date_value}-{stable_slug(local_name)}@yourcalendar.local",
        title=local_name,
        starts_at=starts_at,
        ends_at=ends_at,
        source="Nager.Date",
        category=EventCategory.HOLIDAYS,
        source_quality=SourceQuality.COMMUNITY,
        source_url=nager_holiday_url(year, country_code),
        description="\n".join(
            [
                "Generated by YourCalendar POC.",
                "Source: Nager.Date public holiday API.",
                f"Country: {country_code.upper()}.",
                f"Region: {region_note}.",
                f"Types: {types or 'unknown'}.",
                f"Counties: {', '.join(counties) if counties else 'global'}.",
            ]
        ),
        external_id=f"{country_code.upper()}-{date_value}-{stable_slug(local_name)}",
        all_day=True,
        quality_notes=(
            "Nager.Date is not an official government source.",
            "Verify legal/commercial use and regional coverage before production.",
        ),
    )


def fetch_nager_holiday_events(
    year: int,
    country_code: str = DEFAULT_HOLIDAY_COUNTRY,
    subdivision: str = DEFAULT_HOLIDAY_SUBDIVISION,
    max_events: int | None = None,
    tz_name: str = DEFAULT_TIMEZONE,
    raw_holidays: list[dict] | None = None,
) -> list[CalendarEvent]:
    country_code = country_code.upper()
    subdivision = subdivision.strip()
    raw_holidays = (
        raw_holidays
        if raw_holidays is not None
        else fetch_json_list(nager_holiday_url(year, country_code))
    )
    events = [
        nager_holiday_to_event(holiday, year, country_code, subdivision, tz_name)
        for holiday in raw_holidays
        if holiday_applies_to_subdivision(holiday, subdivision)
    ]
    events = sorted(events, key=lambda event: event.starts_at)
    return events[:max_events] if max_events else events


def build_description(raw_event: dict, team_id: str) -> str:
    parts = [
        "Generated by YourCalendar POC.",
        "Source: TheSportsDB.",
        f"TheSportsDB team id: {team_id}.",
        "Time quality note: verify kickoff times before relying on this source in production.",
    ]
    league = raw_event.get("strLeague")
    if league:
        parts.append(f"League: {league}.")
    round_value = raw_event.get("intRound")
    if round_value:
        parts.append(f"Round: {round_value}.")
    return "\n".join(parts)


def escape_ics_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def fold_ics_line(line: str) -> str:
    # RFC 5545 line folding is byte-based. This conservative implementation
    # keeps lines short enough for ASCII and common UTF-8 text.
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line

    chunks: list[str] = []
    current = ""
    current_len = 0
    for char in line:
        char_len = len(char.encode("utf-8"))
        if current and current_len + char_len > 73:
            chunks.append(current)
            current = f" {char}"
            current_len = 1 + char_len
        else:
            current += char
            current_len += char_len
    chunks.append(current)
    return "\r\n".join(chunks)


def utc_stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def date_stamp(value: datetime) -> str:
    return value.date().strftime("%Y%m%d")


def render_ics(events: list[CalendarEvent], calendar_name: str) -> str:
    now = datetime.now(timezone.utc)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//YourCalendar//KSC POC//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_ics_text(calendar_name)}",
        "X-WR-TIMEZONE:Europe/Berlin",
    ]

    for event in events:
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{escape_ics_text(event.uid)}",
                f"DTSTAMP:{utc_stamp(now)}",
                f"SUMMARY:{escape_ics_text(event.title)}",
                f"STATUS:{event.ics_status}",
                f"CATEGORIES:{escape_ics_text(event.category)}",
            ]
        )
        if event.all_day:
            lines.append(f"DTSTART;VALUE=DATE:{date_stamp(event.starts_at)}")
            lines.append(f"DTEND;VALUE=DATE:{date_stamp(event.ends_at)}")
        else:
            lines.append(f"DTSTART:{utc_stamp(event.starts_at)}")
            lines.append(f"DTEND:{utc_stamp(event.ends_at)}")
        if event.location:
            lines.append(f"LOCATION:{escape_ics_text(event.location)}")
        description_parts = []
        if event.description:
            description_parts.append(event.description)
        if event.quality_notes:
            description_parts.append("Quality notes: " + " ".join(event.quality_notes))
        if description_parts:
            lines.append(f"DESCRIPTION:{escape_ics_text('\n'.join(description_parts))}")
        if event.source_url:
            lines.append(f"URL:{escape_ics_text(event.source_url)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(fold_ics_line(line) for line in lines) + "\r\n"


def write_ics(events: list[CalendarEvent], output_path: Path, calendar_name: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_ics(events, calendar_name), encoding="utf-8")


def build_sample_events(tz_name: str) -> list[CalendarEvent]:
    tz = ZoneInfo(tz_name)
    today = datetime.now(tz)
    first = (today + timedelta(days=7)).replace(hour=15, minute=30, second=0, microsecond=0)
    second = (today + timedelta(days=14)).replace(hour=18, minute=30, second=0, microsecond=0)
    return [
        CalendarEvent(
            uid=f"sample-ksc-home-{first.date()}@yourcalendar.local",
            title="[SAMPLE] Karlsruher SC vs Example FC",
            starts_at=first,
            ends_at=first + timedelta(hours=2),
            location="BBBank Wildpark",
            source="Sample",
            category=EventCategory.SAMPLE,
            source_quality=SourceQuality.SAMPLE,
            description="Sample event for testing calendar publishing. Not a real fixture.",
            quality_notes=("Sample event. Not a real fixture.",),
        ),
        CalendarEvent(
            uid=f"sample-ksc-away-{second.date()}@yourcalendar.local",
            title="[SAMPLE] Example United vs Karlsruher SC",
            starts_at=second,
            ends_at=second + timedelta(hours=2),
            location="Example Stadium",
            source="Sample",
            category=EventCategory.SAMPLE,
            source_quality=SourceQuality.SAMPLE,
            description="Sample event for testing calendar publishing. Not a real fixture.",
            quality_notes=("Sample event. Not a real fixture.",),
        ),
    ]


def print_events(events: list[CalendarEvent]) -> None:
    if not events:
        print("No upcoming events found.")
        return

    for event in events:
        starts = event.starts_at.strftime("%Y-%m-%d %H:%M %Z")
        location = f" | {event.location}" if event.location else ""
        print(f"- {starts} | {event.title}{location}")


def print_publish_help(output_path: Path) -> None:
    absolute = output_path.resolve()
    print("\nPublish options:")
    print(f"- Apple Calendar: open/import {absolute}")
    print("- Google Calendar: Settings -> Import & export -> Import the .ics file.")
    print("- Outlook: Add calendar -> Upload from file -> choose the .ics file.")
    print(
        "- Subscription mode: host this .ics file at an HTTPS URL, then subscribe "
        "to that URL in Google/Outlook/Apple so updates can refresh automatically."
    )


def publish_to_apple(output_path: Path) -> None:
    if platform.system() != "Darwin":
        raise POCError("--publish apple is only implemented for macOS in this POC.")
    subprocess.run(["open", str(output_path.resolve())], check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch upcoming KSC events and generate a calendar file."
    )
    parser.add_argument("--team", default=DEFAULT_TEAM_QUERY, help="Team search query.")
    parser.add_argument(
        "--source",
        choices=["openligadb", "thesportsdb", "nager-holidays"],
        default="openligadb",
        help="Event source to use.",
    )
    parser.add_argument(
        "--league",
        action="append",
        choices=sorted(OPENLIGADB_LEAGUES),
        help="OpenLigaDB league shortcut. Can be passed multiple times.",
    )
    parser.add_argument(
        "--season",
        type=int,
        default=None,
        help="Football season start year, for example 2025 for 2025/26.",
    )
    parser.add_argument(
        "--include-past",
        action="store_true",
        help="Include already played OpenLigaDB matches in the generated calendar.",
    )
    parser.add_argument(
        "--thesportsdb-key",
        default=os.getenv("THESPORTSDB_API_KEY", "123"),
        help="TheSportsDB API key. Defaults to demo key 123.",
    )
    parser.add_argument(
        "--thesportsdb-team-id",
        default=DEFAULT_THESPORTSDB_TEAM_ID,
        help="TheSportsDB team ID. Defaults to Karlsruher SC: 135293.",
    )
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE, help="Output timezone.")
    parser.add_argument(
        "--holiday-year",
        type=int,
        default=datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).year,
        help="Holiday calendar year for --source nager-holidays.",
    )
    parser.add_argument(
        "--holiday-country",
        default=DEFAULT_HOLIDAY_COUNTRY,
        help="ISO 3166-1 alpha-2 country code for --source nager-holidays.",
    )
    parser.add_argument(
        "--holiday-subdivision",
        default=DEFAULT_HOLIDAY_SUBDIVISION,
        help="Optional Nager.Date subdivision code, for example DE-BW.",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Optional maximum number of normalized events to write.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="ICS output path.")
    parser.add_argument(
        "--calendar-name",
        default="Karlsruher SC Fixtures",
        help="Calendar display name.",
    )
    parser.add_argument(
        "--publish",
        choices=["none", "apple"],
        default="none",
        help="Optional local publish action. Google/Outlook require import or hosted subscription.",
    )
    parser.add_argument(
        "--show-events",
        action="store_true",
        help="Print normalized events to stdout.",
    )
    parser.add_argument(
        "--sample-events",
        action="store_true",
        help="Use clearly marked sample events instead of fetching real source data.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_path = Path(args.output)

    try:
        if args.sample_events:
            events = build_sample_events(args.timezone)
        elif args.source == "openligadb":
            leagues = args.league or ["bl1", "bl2", "bl3", "dfb"]
            events = fetch_openligadb_multi_league_events(
                leagues=leagues,
                season=args.season,
                upcoming_only=not args.include_past,
                tz_name=args.timezone,
            )
        elif args.source == "thesportsdb":
            events = fetch_thesportsdb_events(
                args.thesportsdb_key,
                args.team,
                args.thesportsdb_team_id,
                args.timezone,
            )
        elif args.source == "nager-holidays":
            events = fetch_nager_holiday_events(
                year=args.holiday_year,
                country_code=args.holiday_country,
                subdivision=args.holiday_subdivision,
                max_events=args.max_events,
                tz_name=args.timezone,
            )
        else:
            raise POCError(f"Unsupported source: {args.source}")

        write_ics(events, output_path, args.calendar_name)
        print(f"Generated {len(events)} event(s): {output_path.resolve()}")
        if args.show_events:
            print_events(events)
        print_publish_help(output_path)

        if args.publish == "apple":
            publish_to_apple(output_path)

        return 0
    except POCError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Publish command failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
