from urllib.request import urlopen

from ..domain.calendar_entry import CalendarEntry
from ..domain.calendar_event import CalendarEvent
from .base import CalendarProvider
from .thesportsdb_client import TheSportsDBClient
from .thesportsdb_team_event_fetcher import TheSportsDBTeamEventFetcher


class TheSportsDBProvider(CalendarProvider):
    name = "TheSportsDB"

    def __init__(
        self,
        base_url: str,
        free_api_key: str,
        default_duration_minutes: int,
        opener=urlopen,
    ) -> None:
        client = TheSportsDBClient(base_url=base_url, free_api_key=free_api_key, opener=opener)
        self.team_event_fetcher = TheSportsDBTeamEventFetcher(
            client=client,
            provider_name=self.name,
            default_duration_minutes=default_duration_minutes,
        )

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        return self.team_event_fetcher.fetch_events(entry)
