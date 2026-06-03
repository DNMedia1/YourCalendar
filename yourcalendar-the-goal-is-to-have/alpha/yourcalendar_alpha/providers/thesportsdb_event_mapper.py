from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

from ..domain.calendar_entry import CalendarEntry
from ..domain.calendar_event import CalendarEvent
from .thesportsdb_datetime import parse_thesportsdb_datetime


def map_thesportsdb_event(
    entry: CalendarEntry,
    raw_event: dict[str, Any],
    provider_name: str,
    default_duration_minutes: int,
) -> CalendarEvent | None:
    event_id = str(raw_event.get("idEvent") or "").strip()
    date_value = str(raw_event.get("dateEvent") or "").strip()
    time_value = str(raw_event.get("strTime") or raw_event.get("strTimestamp") or "").strip()
    if not event_id or not date_value:
        return None

    starts_at = parse_thesportsdb_datetime(date_value, time_value)
    ends_at = starts_at + timedelta(minutes=default_duration_minutes)
    source_hash = hashlib.sha256(
        json.dumps(raw_event, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return CalendarEvent(
        uid=f"thesportsdb-{event_id}@yourcalendar-alpha",
        title=build_event_title(raw_event),
        starts_at=starts_at,
        ends_at=ends_at,
        location=build_event_location(raw_event),
        description=build_event_description(entry, raw_event, provider_name, event_id),
        source_hash=source_hash,
    )


def build_event_title(raw_event: dict[str, Any]) -> str:
    home_team = str(raw_event.get("strHomeTeam") or "").strip()
    away_team = str(raw_event.get("strAwayTeam") or "").strip()
    fallback_title = " vs ".join([part for part in [home_team, away_team] if part])
    return str(raw_event.get("strEvent") or "").strip() or fallback_title


def build_event_location(raw_event: dict[str, Any]) -> str:
    venue = str(raw_event.get("strVenue") or "").strip()
    city = str(raw_event.get("strCity") or "").strip()
    return ", ".join([part for part in [venue, city] if part])


def build_event_description(
    entry: CalendarEntry,
    raw_event: dict[str, Any],
    provider_name: str,
    event_id: str,
) -> str:
    league = str(raw_event.get("strLeague") or entry.competition).strip()
    status = str(raw_event.get("strStatus") or "").strip()
    score = build_score_text(raw_event)
    description_parts = [
        f"Wettbewerb: {league}",
        f"Provider: {provider_name}",
        f"Provider Event ID: {event_id}",
    ]
    if status:
        description_parts.append(f"Status: {status}")
    if score:
        description_parts.append(score)
    return "\\n".join(description_parts)


def build_score_text(raw_event: dict[str, Any]) -> str:
    home_score = raw_event.get("intHomeScore")
    away_score = raw_event.get("intAwayScore")
    if home_score in (None, "") or away_score in (None, ""):
        return ""
    return f"Ergebnis: {home_score}:{away_score}"
