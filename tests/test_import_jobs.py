from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import import_jobs


ICS_WITH_EVENT = "\r\n".join(
    [
        "BEGIN:VCALENDAR",
        "BEGIN:VEVENT",
        "UID:test@yourcalendar.local",
        "SUMMARY:Test Event",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
)


class ImportJobTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.previous_cache_dir = import_jobs.FEED_CACHE_DIR
        self.previous_runs_path = import_jobs.IMPORT_RUNS_PATH
        self.previous_snapshot_dir = import_jobs.EVENT_SNAPSHOT_DIR
        self.previous_changes_dir = import_jobs.EVENT_CHANGES_DIR
        temp_root = Path(self.tmpdir.name)
        import_jobs.FEED_CACHE_DIR = temp_root / "feeds"
        import_jobs.IMPORT_RUNS_PATH = temp_root / "import-runs.json"
        import_jobs.EVENT_SNAPSHOT_DIR = temp_root / "event-snapshots"
        import_jobs.EVENT_CHANGES_DIR = temp_root / "event-changes"

    def tearDown(self) -> None:
        import_jobs.FEED_CACHE_DIR = self.previous_cache_dir
        import_jobs.IMPORT_RUNS_PATH = self.previous_runs_path
        import_jobs.EVENT_SNAPSHOT_DIR = self.previous_snapshot_dir
        import_jobs.EVENT_CHANGES_DIR = self.previous_changes_dir
        self.tmpdir.cleanup()

    def test_import_calendar_writes_cache_and_success_result(self) -> None:
        result = import_jobs.import_calendar(
            "sample-ksc",
            renderer=lambda feed_id: (ICS_WITH_EVENT, True),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["eventCount"], 1)
        self.assertIsNone(result["error"])
        self.assertEqual(result["changeSummary"], {"total": 1, "new": 1, "changed": 0, "missing": 0})
        self.assertTrue(import_jobs.feed_cache_path("sample-ksc").exists())
        self.assertTrue(import_jobs.event_snapshot_path("sample-ksc").exists())
        self.assertTrue(import_jobs.event_changes_path("sample-ksc").exists())

    def test_import_calendar_marks_empty_feed_as_warning(self) -> None:
        result = import_jobs.import_calendar(
            "sample-ksc",
            renderer=lambda feed_id: ("BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n", True),
        )

        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["eventCount"], 0)
        self.assertEqual(result["warnings"], ["Feed contains no events."])

    def test_import_calendar_keeps_existing_cache_on_error(self) -> None:
        cache_path = import_jobs.write_feed_cache("sample-ksc", ICS_WITH_EVENT)

        def failing_renderer(feed_id: str):
            raise RuntimeError("source unavailable")

        result = import_jobs.import_calendar("sample-ksc", renderer=failing_renderer)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "source unavailable")
        with cache_path.open(encoding="utf-8", newline="") as handle:
            self.assertEqual(handle.read(), ICS_WITH_EVENT)

    def test_run_import_job_appends_run_log(self) -> None:
        results = import_jobs.run_import_job(
            ["sample-ksc"],
            renderer=lambda feed_id: (ICS_WITH_EVENT, True),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(import_jobs.load_import_runs(), results)


if __name__ == "__main__":
    unittest.main()
