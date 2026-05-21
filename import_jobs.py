#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from web_app import PUBLISHED_CALENDARS, feed_filename, render_feed


ROOT = Path(__file__).resolve().parent
FEED_CACHE_DIR = ROOT / "output" / "feeds"
IMPORT_RUNS_PATH = ROOT / "output" / "import-runs.json"

RenderFeed = Callable[[str], tuple[str, bool]]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def feed_cache_path(feed_id: str) -> Path:
    return FEED_CACHE_DIR / feed_filename(feed_id)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def count_events(ics_content: str) -> int:
    return ics_content.count("BEGIN:VEVENT")


def write_feed_cache(feed_id: str, content: str) -> Path:
    FEED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target = feed_cache_path(feed_id)
    fd, temp_name = tempfile.mkstemp(prefix=f"{target.name}.", suffix=".tmp", dir=FEED_CACHE_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        Path(temp_name).replace(target)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise
    return target


def load_import_runs() -> list[dict]:
    if not IMPORT_RUNS_PATH.exists():
        return []
    try:
        data = json.loads(IMPORT_RUNS_PATH.read_text())
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def save_import_runs(runs: list[dict]) -> None:
    IMPORT_RUNS_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_RUNS_PATH.write_text(json.dumps(runs, ensure_ascii=False, indent=2) + "\n")


def append_import_runs(results: list[dict]) -> None:
    save_import_runs(load_import_runs() + results)


def import_calendar(feed_id: str, renderer: RenderFeed = render_feed) -> dict:
    started_at = utc_now_iso()
    try:
        content, is_sample = renderer(feed_id)
        event_count = count_events(content)
        warnings = []
        if event_count == 0:
            warnings.append("Feed contains no events.")
        output_path = write_feed_cache(feed_id, content)
        status = "warning" if warnings else "success"
        return {
            "feedId": feed_id,
            "status": status,
            "startedAt": started_at,
            "finishedAt": utc_now_iso(),
            "eventCount": event_count,
            "sample": is_sample,
            "warnings": warnings,
            "error": None,
            "outputPath": display_path(output_path),
        }
    except Exception as exc:
        return {
            "feedId": feed_id,
            "status": "error",
            "startedAt": started_at,
            "finishedAt": utc_now_iso(),
            "eventCount": None,
            "sample": None,
            "warnings": [],
            "error": str(exc),
            "outputPath": display_path(feed_cache_path(feed_id)),
        }


def run_import_job(feed_ids: list[str] | None = None, renderer: RenderFeed = render_feed) -> list[dict]:
    selected_feed_ids = feed_ids or list(PUBLISHED_CALENDARS)
    results = [import_calendar(feed_id, renderer) for feed_id in selected_feed_ids]
    append_import_runs(results)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import and cache published YourCalendar feeds.")
    parser.add_argument(
        "--feed",
        action="append",
        choices=sorted(PUBLISHED_CALENDARS),
        help="Published feed id to import. Can be passed multiple times. Defaults to all feeds.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = run_import_job(args.feed)
    print(json.dumps({"ok": True, "results": results}, ensure_ascii=False, indent=2))
    return 1 if all(result["status"] == "error" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
