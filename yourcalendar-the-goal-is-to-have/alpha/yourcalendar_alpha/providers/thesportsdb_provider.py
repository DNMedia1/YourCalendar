from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from ..domain.calendar_entry import CalendarEntry
from ..domain.calendar_event import CalendarEvent
from .base import CalendarProvider
from .errors import ProviderError
from .thesportsdb_event_mapper import map_thesportsdb_event


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

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        if not entry.ics_id.isdigit():
            raise ProviderError("TheSportsDB entries use ICSId as numeric idTeam in this alpha")

        payloads = [
            self.fetch_json(entry, "eventsnext.php", {"id": entry.ics_id}),
            self.fetch_json(entry, "eventslast.php", {"id": entry.ics_id}),
        ]
        events_by_uid: dict[str, CalendarEvent] = {}
        for payload in payloads:
            for raw_event in payload.get("events") or []:
                event = map_thesportsdb_event(entry, raw_event, self.name, self.default_duration_minutes)
                if event:
                    events_by_uid[event.uid] = event
        return list(events_by_uid.values())

    def fetch_json(self, entry: CalendarEntry, endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.base_url}/{self.api_key_for(entry)}/{endpoint}?{urlencode(params)}"
        with self.opener(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def api_key_for(self, entry: CalendarEntry) -> str:
        if not entry.api_key_provider:
            return self.free_api_key
        return os.environ.get(entry.api_key_provider, self.free_api_key)
