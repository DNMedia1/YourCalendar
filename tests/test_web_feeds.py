from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import web_app
from web_app import (
    CURRENT_FEED_ID,
    calendar_catalog,
    feed_filename,
    feed_path_for_params,
    load_cached_feed,
    normalize_feed_params,
    render_feed,
    resolve_feed,
    source_health_payload,
    sports_coverage_payload,
)
from yourcalendar_runs import SourceRunRecord, latest_runs_by_source, record_source_run
from yourcalendar_sources import source_monitor_payload, source_plan_payload


class WebFeedTest(unittest.TestCase):
    def test_current_feed_path_preserves_filter_params(self) -> None:
        params = {
            "sample": ["true"],
            "leagues": ["bl2"],
            "team": ["Karlsruhe"],
            "favorites": ["Karlsruher SC"],
            "includePast": ["true"],
        }

        path = feed_path_for_params(params)
        parsed = urlparse(path)

        self.assertEqual(parsed.path, f"/feeds/{CURRENT_FEED_ID}.ics")
        self.assertEqual(parse_qs(parsed.query), params)

    def test_normalize_feed_params_keeps_calendar_defaults(self) -> None:
        params = normalize_feed_params({})

        self.assertEqual(params["sample"], ["false"])
        self.assertEqual(params["leagues"], ["bl1,bl2,bl3"])
        self.assertEqual(params["includePast"], ["false"])

    def test_published_sample_feed_is_marked_as_sample(self) -> None:
        ics, is_sample = render_feed("sample-ksc")

        self.assertTrue(is_sample)
        self.assertIn("BEGIN:VCALENDAR", ics)
        self.assertIn("X-WR-CALNAME:YourCalendar Sample Football", ics)
        self.assertIn("[SAMPLE]", ics)
        self.assertIn("CATEGORIES:sample", ics)

    def test_published_holiday_feed_resolves_to_holiday_source(self) -> None:
        calendar_name, params, is_sample = resolve_feed("holidays-germany", "")

        self.assertEqual(calendar_name, "YourCalendar German Holidays")
        self.assertEqual(params["source"], ["holidays"])
        self.assertEqual(params["country"], ["DE"])
        self.assertFalse(is_sample)

    def test_current_sample_feed_uses_query_params(self) -> None:
        calendar_name, params, is_sample = resolve_feed(
            CURRENT_FEED_ID,
            "sample=true&leagues=bl1&includePast=true",
        )

        self.assertEqual(calendar_name, "YourCalendar Sample Football")
        self.assertEqual(params["sample"], ["true"])
        self.assertTrue(is_sample)

    def test_feed_filename_sanitizes_feed_id(self) -> None:
        self.assertEqual(feed_filename("../football"), "yourcalendar-football.ics")

    def test_calendar_catalog_groups_published_and_empty_categories(self) -> None:
        checked_at = datetime(2026, 5, 21, 10, 15, tzinfo=ZoneInfo("Europe/Berlin"))
        categories = calendar_catalog(lambda path: f"https://example.test{path}", checked_at)
        by_id = {category["id"]: category for category in categories}
        first_sports_calendar = by_id["sports"]["calendars"][0]

        self.assertIn("sports", by_id)
        self.assertIn("politics", by_id)
        self.assertIn("city", by_id)
        self.assertIn("culture", by_id)
        self.assertIn("holidays", by_id)
        self.assertGreaterEqual(by_id["sports"]["calendarCount"], 1)
        self.assertIn("combat", by_id)
        self.assertGreaterEqual(by_id["combat"]["calendarCount"], 1)
        self.assertEqual(by_id["politics"]["calendarCount"], 0)
        self.assertEqual(first_sports_calendar["sourceLabel"], "OpenLigaDB, Community-Daten")
        self.assertEqual(first_sports_calendar["quality"]["label"], "Community, kein SLA")
        self.assertEqual(first_sports_calendar["quality"]["updatedAt"], "2026-05-21T10:15:00+02:00")
        self.assertIn("kein garantierter Echtzeitprovider", first_sports_calendar["quality"]["reliabilityNote"])
        self.assertTrue(first_sports_calendar["subscribeUrl"].startswith("https://example.test/feeds/"))

        combat_calendar = by_id["combat"]["calendars"][0]
        self.assertFalse(combat_calendar["hasFeed"])
        self.assertIsNone(combat_calendar["feedUrl"])
        self.assertEqual(combat_calendar["quality"]["label"], "Provider nötig")
        self.assertIn("Kampfsportveranstaltungen", combat_calendar["quality"]["reliabilityNote"])

        championship_calendar = [
            calendar for calendar in by_id["sports"]["calendars"]
            if calendar["id"] == "world-europe-championships"
        ][0]
        self.assertFalse(championship_calendar["hasFeed"])
        self.assertIn("WM & EM", championship_calendar["name"])

    def test_sports_coverage_exposes_europe_combat_and_championships(self) -> None:
        coverage = sports_coverage_payload()

        self.assertGreaterEqual(len(coverage["europeSports"]), 20)
        self.assertGreaterEqual(len(coverage["globalCombatSports"]), 10)
        self.assertEqual(
            {item["id"] for item in coverage["championships"]},
            {"world-championships", "european-championships"},
        )
        self.assertIn("Fußball", {item["name"] for item in coverage["europeSports"]})
        self.assertIn("MMA", {item["name"] for item in coverage["globalCombatSports"]})

    def test_source_plan_exposes_provider_integration_tracks(self) -> None:
        source_plan = source_plan_payload()
        by_id = {item["id"]: item for item in source_plan["items"]}

        self.assertEqual(source_plan["total"], len(source_plan["items"]))
        self.assertEqual(source_plan["needsWork"], source_plan["total"] - source_plan["active"])
        self.assertIn("openligadb-football-poc", by_id)
        self.assertIn("europe-sports-provider", by_id)
        self.assertIn("global-combat-provider", by_id)
        self.assertIn("championship-detector", by_id)
        self.assertIn("football-germany", by_id["openligadb-football-poc"]["calendarIds"])
        self.assertIn("global-combat-events", by_id["global-combat-provider"]["calendarIds"])
        self.assertTrue(by_id["championship-detector"]["acceptanceCriteria"])

    def test_source_monitor_exposes_all_current_source_tracks(self) -> None:
        monitor = source_monitor_payload()
        by_id = {item["id"]: item for item in monitor["items"]}

        self.assertEqual(monitor["total"], len(monitor["items"]))
        self.assertGreaterEqual(monitor["watching"], 1)
        self.assertGreaterEqual(monitor["planned"], 1)
        self.assertIn("openligadb-football", by_id)
        self.assertIn("yourcalendar-sample", by_id)
        self.assertIn("global-combat-provider", by_id)
        self.assertEqual(by_id["openligadb-football"]["eventCountLabel"], "Pro Abruf ermittelt")
        self.assertIn("global-combat-events", by_id["global-combat-provider"]["calendarIds"])

    def test_source_monitor_merges_latest_persisted_run(self) -> None:
        run = {
            "sourceId": "openligadb-football",
            "status": "ok",
            "checkedAt": "2026-05-21T12:00:00+02:00",
            "checkedLabel": "Geprüft 21.05.2026 12:00 CEST",
            "eventCount": 18,
            "message": "Der OpenLigaDB-Abruf lieferte Termine.",
        }

        monitor = source_monitor_payload({"openligadb-football": run})
        openliga = {
            item["id"]: item for item in monitor["items"]
        }["openligadb-football"]

        self.assertEqual(openliga["lastRun"]["eventCount"], 18)
        self.assertEqual(openliga["lastRun"]["checkedLabel"], "Geprüft 21.05.2026 12:00 CEST")

    def test_source_run_store_keeps_latest_run_by_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source-runs.json"
            first = SourceRunRecord(
                source_id="openligadb-football",
                status="empty",
                checked_at=datetime(2026, 5, 21, 11, 0, tzinfo=ZoneInfo("Europe/Berlin")),
                checked_label="Geprüft 21.05.2026 11:00 CEST",
                event_count=0,
                message="Keine Termine.",
            )
            second = SourceRunRecord(
                source_id="openligadb-football",
                status="ok",
                checked_at=datetime(2026, 5, 21, 12, 0, tzinfo=ZoneInfo("Europe/Berlin")),
                checked_label="Geprüft 21.05.2026 12:00 CEST",
                event_count=7,
                message="Termine gefunden.",
            )

            record_source_run(path, first)
            record_source_run(path, second)
            latest = latest_runs_by_source(path)

        self.assertEqual(latest["openligadb-football"]["status"], "ok")
        self.assertEqual(latest["openligadb-football"]["eventCount"], 7)

    def test_source_health_marks_empty_live_queries_with_recovery_hints(self) -> None:
        params = normalize_feed_params({"sample": ["false"], "leagues": ["bl2"], "season": ["2026"]})

        health = source_health_payload(False, 0, params)

        self.assertEqual(health["status"], "empty")
        self.assertEqual(health["label"], "Keine Termine")
        self.assertIn("2026", " ".join(health["hints"]))
        self.assertEqual(health["selectedLeagues"], ["2. Bundesliga"])
        self.assertEqual(health["monitorObservation"]["sourceId"], "openligadb-football")
        self.assertEqual(health["monitorObservation"]["status"], "empty")
        self.assertEqual(health["monitorObservation"]["eventCount"], 0)

    def test_source_health_uses_safe_error_copy_for_openligadb_failures(self) -> None:
        params = normalize_feed_params({"sample": ["false"], "leagues": ["bl1"]})

        health = source_health_payload(False, 0, params, "HTTP 500 while fetching test-url")

        self.assertEqual(health["status"], "error")
        self.assertEqual(health["label"], "Quelle gestört")
        self.assertIn("nicht gelesen", health["title"])
        self.assertIn("Kalender bleibt verfügbar", health["detail"])
        self.assertEqual(health["technicalDetail"], "HTTP 500 while fetching test-url")
        self.assertEqual(health["monitorObservation"]["status"], "error")


class CachedFeedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.previous_cache_dir = web_app.FEED_CACHE_DIR
        web_app.FEED_CACHE_DIR = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        web_app.FEED_CACHE_DIR = self.previous_cache_dir
        self.tmpdir.cleanup()

    def test_published_feed_uses_cache_without_query(self) -> None:
        cache_path = web_app.cached_feed_path("sample-ksc")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n", encoding="utf-8")

        self.assertEqual(load_cached_feed("sample-ksc"), "BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n")

    def test_current_feed_and_filtered_feeds_do_not_use_cache(self) -> None:
        self.assertIsNone(load_cached_feed(CURRENT_FEED_ID))
        self.assertIsNone(load_cached_feed("sample-ksc", "sample=true"))


if __name__ == "__main__":
    unittest.main()
