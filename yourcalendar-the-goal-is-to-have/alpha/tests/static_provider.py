from __future__ import annotations

from yourcalendar_alpha.domain.calendar_entry import CalendarEntry
from yourcalendar_alpha.domain.calendar_event import CalendarEvent


class StaticProvider:
    def __init__(self, events: list[CalendarEvent]) -> None:
        self.events = events

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        return self.events
