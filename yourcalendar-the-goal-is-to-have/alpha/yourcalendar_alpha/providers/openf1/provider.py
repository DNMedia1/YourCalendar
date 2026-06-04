from __future__ import annotations

from datetime import datetime, timezone
from urllib.request import urlopen

from ...domain.calendar_entry import CalendarEntry
from ...domain.calendar_event import CalendarEvent
from ..base import CalendarProvider
from .client import OpenF1Client
from .event_mapper import map_openf1_session


class OpenF1Provider(CalendarProvider):
    name = "OpenF1"

    def __init__(
        self,
        base_url: str,
        default_duration_minutes: int,
        years: list[int] | None = None,
        opener=urlopen,
    ) -> None:
        self.client = OpenF1Client(base_url=base_url, opener=opener)
        self.default_duration_minutes = default_duration_minutes
        self.years = years or [datetime.now(timezone.utc).year]

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        if entry.ics_id != "formula-1":
            return []

        events_by_uid: dict[str, CalendarEvent] = {}
        for year in self.years:
            for raw_session in self.client.fetch_json("sessions", {"year": str(year)}):
                event = map_openf1_session(raw_session, self.name, self.default_duration_minutes)
                if event:
                    events_by_uid[event.uid] = event
        return list(events_by_uid.values())
