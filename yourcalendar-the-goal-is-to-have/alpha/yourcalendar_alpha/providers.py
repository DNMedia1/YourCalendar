from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from .ics import CalendarEvent
from .mapping import CalendarEntry


class ProviderError(RuntimeError):
    pass


class CalendarProvider:
    name = ""

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        raise NotImplementedError


class TheSportsDBProvider(CalendarProvider):
    name = "TheSportsDB"

    def __init__(
        self,
        base_url: str,
        free_api_key: str,
        default_duration_minutes: int,
        opener=urlopen,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.free_api_key = free_api_key
        self.default_duration_minutes = default_duration_minutes
        self.opener = opener

    def _api_key(self, entry: CalendarEntry) -> str:
        if not entry.api_key_provider:
            return self.free_api_key
        return os.environ.get(entry.api_key_provider, self.free_api_key)

    def _get_json(self, entry: CalendarEntry, endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.base_url}/{self._api_key(entry)}/{endpoint}?{urlencode(params)}"
        with self.opener(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        if not entry.ics_id.isdigit():
            raise ProviderError("TheSportsDB entries use ICSId as numeric idTeam in this alpha")
        payloads = [
            self._get_json(entry, "eventsnext.php", {"id": entry.ics_id}),
            self._get_json(entry, "eventslast.php", {"id": entry.ics_id}),
        ]
        events_by_uid: dict[str, CalendarEvent] = {}
        for payload in payloads:
            for raw_event in payload.get("events") or []:
                event = self._map_event(entry, raw_event)
                if event:
                    events_by_uid[event.uid] = event
        return list(events_by_uid.values())

    def _map_event(self, entry: CalendarEntry, raw_event: dict[str, Any]) -> CalendarEvent | None:
        event_id = str(raw_event.get("idEvent") or "").strip()
        date_value = str(raw_event.get("dateEvent") or "").strip()
        time_value = str(raw_event.get("strTime") or raw_event.get("strTimestamp") or "").strip()
        if not event_id or not date_value:
            return None

        starts_at = _parse_event_datetime(date_value, time_value)
        ends_at = starts_at + timedelta(minutes=self.default_duration_minutes)
        home = str(raw_event.get("strHomeTeam") or "").strip()
        away = str(raw_event.get("strAwayTeam") or "").strip()
        title = str(raw_event.get("strEvent") or "").strip() or " vs ".join([part for part in [home, away] if part])
        venue = str(raw_event.get("strVenue") or "").strip()
        city = str(raw_event.get("strCity") or "").strip()
        location = ", ".join([part for part in [venue, city] if part])
        league = str(raw_event.get("strLeague") or entry.competition).strip()
        status = str(raw_event.get("strStatus") or "").strip()
        score = _score_text(raw_event)
        description_parts = [
            f"Wettbewerb: {league}",
            f"Provider: {self.name}",
            f"Provider Event ID: {event_id}",
        ]
        if status:
            description_parts.append(f"Status: {status}")
        if score:
            description_parts.append(score)
        source_hash = hashlib.sha256(
            json.dumps(raw_event, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return CalendarEvent(
            uid=f"thesportsdb-{event_id}@yourcalendar-alpha",
            title=title,
            starts_at=starts_at,
            ends_at=ends_at,
            location=location,
            description="\\n".join(description_parts),
            source_hash=source_hash,
        )


def _parse_event_datetime(date_value: str, time_value: str) -> datetime:
    clean_time = time_value.replace("Z", "").strip() or "00:00:00"
    if "T" in clean_time:
        value = clean_time.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    if len(clean_time) == 5:
        clean_time = f"{clean_time}:00"
    try:
        return datetime.fromisoformat(f"{date_value}T{clean_time}").replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.fromisoformat(f"{date_value}T00:00:00").replace(tzinfo=timezone.utc)


def _score_text(raw_event: dict[str, Any]) -> str:
    home_score = raw_event.get("intHomeScore")
    away_score = raw_event.get("intAwayScore")
    if home_score in (None, "") or away_score in (None, ""):
        return ""
    return f"Ergebnis: {home_score}:{away_score}"


def build_provider_registry(settings: dict[str, Any]) -> dict[str, CalendarProvider]:
    defaults = settings.get("provider_defaults", {})
    sportsdb = defaults.get("TheSportsDB", {})
    return {
        "TheSportsDB": TheSportsDBProvider(
            base_url=sportsdb.get("base_url", "https://www.thesportsdb.com/api/v1/json"),
            free_api_key=str(sportsdb.get("free_api_key", "123")),
            default_duration_minutes=int(settings.get("default_event_duration_minutes", 120)),
        )
    }
