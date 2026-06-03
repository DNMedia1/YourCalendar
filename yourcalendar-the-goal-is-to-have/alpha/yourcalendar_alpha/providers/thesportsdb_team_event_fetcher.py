from __future__ import annotations

from ..domain.calendar_entry import CalendarEntry
from ..domain.calendar_event import CalendarEvent
from .errors import ProviderError
from .thesportsdb_client import TheSportsDBClient
from .thesportsdb_event_mapper import map_thesportsdb_event


class TheSportsDBTeamEventFetcher:
    def __init__(
        self,
        client: TheSportsDBClient,
        provider_name: str,
        default_duration_minutes: int,
    ) -> None:
        self.client = client
        self.provider_name = provider_name
        self.default_duration_minutes = default_duration_minutes

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        if not entry.ics_id.isdigit():
            raise ProviderError("TheSportsDB entries use ICSId as numeric idTeam in this alpha")

        payloads = [
            self.client.fetch_json(entry, "eventsnext.php", {"id": entry.ics_id}),
            self.client.fetch_json(entry, "eventslast.php", {"id": entry.ics_id}),
        ]
        events_by_uid: dict[str, CalendarEvent] = {}
        for payload in payloads:
            for raw_event in payload.get("events") or []:
                event = map_thesportsdb_event(
                    entry,
                    raw_event,
                    self.provider_name,
                    self.default_duration_minutes,
                )
                if event:
                    events_by_uid[event.uid] = event
        return list(events_by_uid.values())
