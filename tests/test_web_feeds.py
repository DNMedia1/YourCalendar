from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import web_app
from web_app import (
    CURRENT_FEED_ID,
    feed_filename,
    feed_path_for_params,
    load_cached_feed,
    normalize_feed_params,
    render_feed,
    resolve_feed,
)


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
