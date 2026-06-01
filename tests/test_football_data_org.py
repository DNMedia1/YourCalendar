from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from football_data_org import (
    events_by_team,
    football_data_match_to_event,
    football_data_team_feed_id,
    FootballDataTeam,
)
from yourcalendar_model import EventCategory, SourceQuality


class FootballDataOrgTest(unittest.TestCase):
    def test_match_maps_to_normalized_calendar_event(self) -> None:
        event = football_data_match_to_event(
            {
                "id": 42,
                "utcDate": "2026-08-21T18:30:00Z",
                "status": "SCHEDULED",
                "matchday": 1,
                "homeTeam": {"id": 1, "name": "Home FC"},
                "awayTeam": {"id": 2, "name": "Away FC"},
                "competition": {"name": "Bundesliga"},
                "venue": "Teststadion",
            }
        )

        self.assertEqual(event.uid, "football-data-42@yourcalendar.local")
        self.assertEqual(event.title, "Home FC vs Away FC")
        self.assertEqual(event.starts_at, datetime(2026, 8, 21, 20, 30, tzinfo=ZoneInfo("Europe/Berlin")))
        self.assertEqual(event.category, EventCategory.SPORTS)
        self.assertEqual(event.source_quality, SourceQuality.PAID_PROVIDER)
        self.assertIn("football-data.org", event.description)

    def test_events_are_grouped_for_home_and_away_team_calendars(self) -> None:
        teams = [
            FootballDataTeam(1, "Home FC", "Home", "HOM"),
            FootballDataTeam(2, "Away FC", "Away", "AWA"),
        ]
        grouped = events_by_team(
            teams,
            [
                {
                    "id": 42,
                    "utcDate": "2026-08-21T18:30:00Z",
                    "status": "SCHEDULED",
                    "homeTeam": {"id": 1, "name": "Home FC"},
                    "awayTeam": {"id": 2, "name": "Away FC"},
                }
            ],
        )

        self.assertEqual(len(grouped[1]), 1)
        self.assertEqual(len(grouped[2]), 1)
        self.assertEqual(football_data_team_feed_id(1, "Home FC"), "football-data-bl1-1-home-fc")


if __name__ == "__main__":
    unittest.main()
