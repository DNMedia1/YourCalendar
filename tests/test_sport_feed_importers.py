from __future__ import annotations

import unittest
from unittest.mock import patch

from sport_feed_importers import import_thesportsdb, sport_manifest_payload
from sport_feed_registry import LEAGUE_IMPORT_CONFIGS, sport_taxonomy_payload


class SportFeedImporterTest(unittest.TestCase):
    def test_taxonomy_groups_requested_sports(self) -> None:
        taxonomy = sport_taxonomy_payload()
        subgroups = {
            subgroup["id"]
            for group in taxonomy["groups"]
            for subgroup in group["subgroups"]
        }

        self.assertIn("football", subgroups)
        self.assertIn("boxing", subgroups)
        self.assertIn("ice-hockey", subgroups)
        self.assertIn("baseball", subgroups)
        self.assertIn("basketball", subgroups)
        self.assertIn("american-football", subgroups)
        self.assertIn("formula-1", subgroups)
        self.assertIn("golf", subgroups)
        self.assertIn("tour-de-france", subgroups)
        self.assertIn("darts", subgroups)
        self.assertIn("chess", subgroups)
        self.assertIn("esports", subgroups)
        self.assertIn("ufc", subgroups)

    def test_thesportsdb_team_import_builds_team_calendars(self) -> None:
        config = next(config for config in LEAGUE_IMPORT_CONFIGS if config.config_id == "thesportsdb-nba")

        def fake_fetch(url, headers=None, timeout_seconds=20):
            if "all_leagues.php" in url:
                return {"leagues": [{"idLeague": "4387", "strLeague": "NBA"}]}
            if "search_all_teams.php" in url:
                return {
                    "teams": [
                        {"idTeam": "1", "strTeam": "Boston Celtics"},
                        {"idTeam": "2", "strTeam": "Denver Nuggets"},
                    ]
                }
            if "eventsseason.php" in url:
                return {
                    "events": [
                        {
                            "idEvent": "100",
                            "dateEvent": "2026-10-20",
                            "strTime": "23:00:00",
                            "strEvent": "Boston Celtics vs Denver Nuggets",
                            "strVenue": "Test Arena",
                        }
                    ]
                }
            raise AssertionError(url)

        with patch("sport_feed_importers.fetch_json", side_effect=fake_fetch):
            calendars = import_thesportsdb(config, "2026-2027")

        self.assertEqual({calendar.name for calendar in calendars}, {"Boston Celtics NBA", "Denver Nuggets NBA"})
        self.assertEqual([len(calendar.events) for calendar in calendars], [1, 1])
        self.assertTrue(all(calendar.feed_id.startswith("sport-basketball-nba-") for calendar in calendars))

    def test_manifest_payload_exposes_calendar_metadata(self) -> None:
        payload = sport_manifest_payload([], [{"configId": "manual-tour-de-france", "status": "skipped"}], "2026-06-02T01:00:00+00:00")

        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["generatedAt"], "2026-06-02T01:00:00+00:00")
        self.assertEqual(payload["errors"][0]["configId"], "manual-tour-de-france")


if __name__ == "__main__":
    unittest.main()
