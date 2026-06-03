from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from yourcalendar_alpha.ics import CalendarEvent
from yourcalendar_alpha.mapping import CalendarEntry
from yourcalendar_alpha.providers import TheSportsDBProvider
from yourcalendar_alpha.sync import sync_all


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class StaticProvider:
    def __init__(self, events: list[CalendarEvent]) -> None:
        self.events = events

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        return self.events


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

            first = sync_all(settings, {"TheSportsDB": StaticProvider(events)})
            second = sync_all(settings, {"TheSportsDB": StaticProvider(events)})

            ics_path = root / "public" / "ics" / "42.ics"
            self.assertTrue(ics_path.exists())
            self.assertIn("BEGIN:VCALENDAR", ics_path.read_text(encoding="utf-8"))
            self.assertEqual(first[0].created, 1)
            self.assertEqual(second[0].created, 0)
            self.assertEqual(second[0].updated, 0)


if __name__ == "__main__":
    unittest.main()
