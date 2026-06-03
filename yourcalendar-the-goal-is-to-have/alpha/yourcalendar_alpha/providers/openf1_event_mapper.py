from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

from ..domain.calendar_event import CalendarEvent
from .openf1_datetime import parse_openf1_datetime


def map_openf1_session(
    raw_session: dict[str, Any],
    provider_name: str,
    default_duration_minutes: int,
) -> CalendarEvent | None:
    session_key = str(raw_session.get("session_key") or "").strip()
    meeting_key = str(raw_session.get("meeting_key") or "").strip()
    date_start = str(raw_session.get("date_start") or "").strip()
    if not session_key or not meeting_key or not date_start:
        return None

    starts_at = parse_openf1_datetime(date_start)
    if starts_at is None:
        return None
    ends_at = parse_openf1_datetime(str(raw_session.get("date_end") or ""))
    if ends_at is None or ends_at <= starts_at:
        ends_at = starts_at + timedelta(minutes=default_duration_minutes)

    source_hash = hashlib.sha256(
        json.dumps(raw_session, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return CalendarEvent(
        uid=f"openf1-{meeting_key}-{session_key}@yourcalendar-alpha",
        title=build_session_title(raw_session),
        starts_at=starts_at,
        ends_at=ends_at,
        location=build_session_location(raw_session),
        description=build_session_description(raw_session, provider_name),
        source_hash=source_hash,
    )


def build_session_title(raw_session: dict[str, Any]) -> str:
    meeting_name = str(raw_session.get("meeting_name") or "").strip()
    session_name = str(raw_session.get("session_name") or "").strip()
    return " - ".join([part for part in [meeting_name, session_name] if part]) or "Formel 1"


def build_session_location(raw_session: dict[str, Any]) -> str:
    circuit = str(raw_session.get("circuit_short_name") or "").strip()
    location = str(raw_session.get("location") or "").strip()
    country = str(raw_session.get("country_name") or "").strip()
    return ", ".join([part for part in [circuit, location, country] if part])


def build_session_description(raw_session: dict[str, Any], provider_name: str) -> str:
    description_parts = [
        "Wettbewerb: Motorsport/Formel 1",
        f"Provider: {provider_name}",
        f"OpenF1 Meeting Key: {raw_session.get('meeting_key')}",
        f"OpenF1 Session Key: {raw_session.get('session_key')}",
    ]
    session_type = str(raw_session.get("session_type") or "").strip()
    if session_type:
        description_parts.append(f"Session-Typ: {session_type}")
    official_name = str(raw_session.get("meeting_official_name") or "").strip()
    if official_name:
        description_parts.append(official_name)
    return "\\n".join(description_parts)
