from __future__ import annotations

from ..domain.calendar_entry import CalendarEntry
from ..domain.calendar_event import CalendarEvent


class CalendarProvider:
    name = ""

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        raise NotImplementedError
