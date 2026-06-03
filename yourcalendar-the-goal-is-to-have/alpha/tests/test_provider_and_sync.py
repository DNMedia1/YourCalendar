from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from fake_response import FakeResponse
from static_provider import StaticProvider
from yourcalendar_alpha.domain.calendar_entry import CalendarEntry
from yourcalendar_alpha.domain.calendar_event import CalendarEvent
from yourcalendar_alpha.providers.thesportsdb_provider import TheSportsDBProvider
from yourcalendar_alpha.sync.service import sync_all_calendars


class ProviderAndSyncTests(unittest.TestCase):
    def test_thesportsdb_maps_events_to_calendar_events(self) -> None:
        payload = {
            "events": [
                {
                    "idEvent": "9001",
                    "dateEvent": "2026-08-15",
                    "strTime": "13:30:00",
                    "strEvent": "FC Bayern Muenchen vs Borussia Dortmund",
                    "strHomeTeam": "FC Bayern Muenchen",
                    "strAwayTeam": "Borussia Dortmund",
                    "strVenue": "Allianz Arena",
                    "strCity": "Muenchen",
                    "strLeague": "Bundesliga",
                }
            ]
        }
        calls: list[str] = []

        def opener(url: str, timeout: int = 30) -> FakeResponse:
            calls.append(url)
            return FakeResponse(payload)

        provider = TheSportsDBProvider(
            base_url="https://example.test/api",
            free_api_key="123",
            default_duration_minutes=120,
            opener=opener,
        )
        entry = CalendarEntry("Fussball/DE/1. Bundesliga/Team", "DE", "Sport", "1. Bundesliga", "TheSportsDB", "", "133664", None, 1)

        events = provider.fetch_events(entry)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].uid, "thesportsdb-9001@yourcalendar-alpha")
        self.assertEqual(events[0].location, "Allianz Arena, Muenchen")
        self.assertEqual(len(calls), 2)
        self.assertTrue(any("eventsnext.php?id=133664" in call for call in calls))
        self.assertTrue(any("eventslast.php?id=133664" in call for call in calls))

    def test_thesportsdb_maps_nfl_team_events_with_same_provider_contract(self) -> None:
        payload = {
            "events": [
                {
                    "idEvent": "nfl-9001",
                    "dateEvent": "2026-09-10",
                    "strTime": "20:20:00",
                    "strEvent": "Kansas City Chiefs vs Las Vegas Raiders",
                    "strHomeTeam": "Kansas City Chiefs",
                    "strAwayTeam": "Las Vegas Raiders",
                    "strVenue": "GEHA Field at Arrowhead Stadium",
                    "strCity": "Kansas City",
                    "strLeague": "NFL",
                }
            ]
        }
        calls: list[str] = []

        def opener(url: str, timeout: int = 30) -> FakeResponse:
            calls.append(url)
            return FakeResponse(payload)

        provider = TheSportsDBProvider(
            base_url="https://example.test/api",
            free_api_key="123",
            default_duration_minutes=180,
            opener=opener,
        )
        entry = CalendarEntry("Football/NFL/Kansas City Chiefs", "United States", "Sport", "Football/NFL", "TheSportsDB", "", "134931", None, 16)

        events = provider.fetch_events(entry)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].title, "Kansas City Chiefs vs Las Vegas Raiders")
        self.assertEqual(events[0].location, "GEHA Field at Arrowhead Stadium, Kansas City")
        self.assertTrue(any("eventsnext.php?id=134931" in call for call in calls))
        self.assertTrue(any("eventslast.php?id=134931" in call for call in calls))

    def test_sync_writes_ics_and_reports_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            data_dir.mkdir()
            (data_dir / "mapping.csv").write_text(
                "Kalendername,Land,Kategorie,Wettbewerb,API-Provider,API-Key-Provider,ICSId,LogoBytes,SubGroupOrder\n"
                "Fussball/Deutschland/1. Bundesliga/Test Team,Deutschland,Sport,1. Bundesliga,TheSportsDB,,42,,1\n",
                encoding="utf-8",
            )
            settings = {
                "_root_dir": str(root),
                "mapping_file": "data/mapping.csv",
                "ics_output_dir": "public/ics",
            }
            events = [
                CalendarEvent(
                    uid="event-1",
                    title="Test Team vs Other",
                    starts_at=datetime(2026, 8, 1, 13, 30, tzinfo=timezone.utc),
                    ends_at=datetime(2026, 8, 1, 15, 30, tzinfo=timezone.utc),
                    location="Stadion",
                    description="Provider Event ID: 1",
                    source_hash="a",
                )
            ]

            first = sync_all_calendars(settings, {"TheSportsDB": StaticProvider(events)})
            second = sync_all_calendars(settings, {"TheSportsDB": StaticProvider(events)})

            ics_path = root / "public" / "ics" / "42.ics"
            self.assertTrue(ics_path.exists())
            self.assertIn("BEGIN:VCALENDAR", ics_path.read_text(encoding="utf-8"))
            self.assertEqual(first[0].created, 1)
            self.assertEqual(second[0].created, 0)
            self.assertEqual(second[0].updated, 0)


if __name__ == "__main__":
    unittest.main()
