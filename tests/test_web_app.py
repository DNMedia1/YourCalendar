from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs

import web_app
from web_app import (
    CURRENT_FEED_ID,
    PUBLISHED_CALENDARS,
    build_source,
    feed_filename,
    feed_path_for_params,
    normalize_feed_params,
    render_feed,
    resolve_feed,
)


class FeedParamTests(unittest.TestCase):
    def test_normalize_feed_params_adds_safe_defaults(self) -> None:
        params = normalize_feed_params({})

        self.assertEqual(params["sample"], ["false"])
        self.assertEqual(params["leagues"], ["bl1,bl2,bl3"])
        self.assertEqual(params["includePast"], ["false"])

    def test_feed_path_preserves_supported_query_keys(self) -> None:
        params = parse_qs("sample=true&leagues=bl1,bl2&team=Karlsruhe&ignored=value")

        self.assertEqual(
            feed_path_for_params(params),
            "/feeds/current.ics?sample=true&leagues=bl1%2Cbl2&team=Karlsruhe&includePast=false",
        )

    def test_feed_filename_strips_unsafe_characters(self) -> None:
        self.assertEqual(feed_filename("../sample feed"), "yourcalendar-samplefeed.ics")


class FeedRenderingTests(unittest.TestCase):
    def test_current_sample_feed_renders_marked_ics(self) -> None:
        content, is_sample = render_feed(
            CURRENT_FEED_ID,
            "sample=true&leagues=bl1,bl2,bl3&includePast=true",
        )

        self.assertTrue(is_sample)
        self.assertIn("BEGIN:VCALENDAR", content)
        self.assertIn("[SAMPLE]", content)

    def test_published_sample_feed_resolves_without_query(self) -> None:
        name, params, is_sample = resolve_feed("sample-ksc", "")

        self.assertEqual(name, PUBLISHED_CALENDARS["sample-ksc"].name)
        self.assertEqual(params["sample"], ["true"])
        self.assertTrue(is_sample)

    def test_unknown_published_feed_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            resolve_feed("missing-feed", "")


class SourceApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.previous_sources_path = web_app.SOURCES_PATH
        web_app.SOURCES_PATH = Path(self.tmpdir.name) / "sources.json"
        web_app.SOURCES_PATH.write_text("[]\n")

    def tearDown(self) -> None:
        web_app.SOURCES_PATH = self.previous_sources_path
        self.tmpdir.cleanup()

    def test_post_sources_creates_source(self) -> None:
        source, error = build_source(
            {
                "name": "OpenLigaDB",
                "url": "https://api.openligadb.de",
                "category": "football",
                "license": "public",
                "status": "active",
            },
        )

        self.assertIsNone(error)
        self.assertTrue(source["id"])
        self.assertEqual(source["name"], "OpenLigaDB")
        self.assertEqual(source["url"], "https://api.openligadb.de")
        self.assertEqual(source["status"], "active")
        self.assertIsNone(source["lastImport"])
        self.assertIn("createdAt", source)

        web_app.save_sources([source])
        self.assertEqual(web_app.load_sources(), [source])

    def test_post_sources_requires_name_and_url(self) -> None:
        source, error = build_source({"name": "Only name"})

        self.assertIsNone(source)
        self.assertEqual(error, "Missing required field: url")


if __name__ == "__main__":
    unittest.main()
