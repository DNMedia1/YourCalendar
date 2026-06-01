#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from event_changes import (
    compare_snapshots,
    load_snapshot,
    save_changes,
    save_snapshot,
    snapshot_from_ics,
    summarize_changes,
)
from football_data_org import (
    DEFAULT_COMPETITION,
    FOOTBALL_DATA_PROVIDER_LABEL,
    FOOTBALL_DATA_TOKEN_ENV,
    events_by_team,
    fetch_bundesliga_matches,
    fetch_bundesliga_teams,
)
from web_app import PUBLISHED_CALENDARS, feed_filename, render_feed
from yourcalendar_poc import render_ics


ROOT = Path(__file__).resolve().parent
FEED_CACHE_DIR = ROOT / "output" / "feeds"
IMPORT_RUNS_PATH = ROOT / "output" / "import-runs.json"
EVENT_SNAPSHOT_DIR = ROOT / "output" / "event-snapshots"
EVENT_CHANGES_DIR = ROOT / "output" / "event-changes"
FOOTBALL_DATA_MANIFEST_PATH = ROOT / "output" / "football-data-bl1-teams.json"

RenderFeed = Callable[[str], tuple[str, bool]]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_text_preserving_newlines(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="")


def feed_cache_path(feed_id: str) -> Path:
    return FEED_CACHE_DIR / feed_filename(feed_id)


def importable_feed_ids() -> list[str]:
    return [
        feed_id
        for feed_id, calendar in PUBLISHED_CALENDARS.items()
        if calendar.params is not None
    ]


def event_snapshot_path(feed_id: str) -> Path:
    return EVENT_SNAPSHOT_DIR / f"{feed_id}.json"


def event_changes_path(feed_id: str) -> Path:
    return EVENT_CHANGES_DIR / f"{feed_id}.json"


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
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
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
    write_text_preserving_newlines(
        IMPORT_RUNS_PATH,
        json.dumps(runs, ensure_ascii=False, indent=2) + "\n",
    )


def append_import_runs(results: list[dict]) -> None:
    save_import_runs(load_import_runs() + results)


def import_calendar(feed_id: str, renderer: RenderFeed = render_feed) -> dict:
    started_at = utc_now_iso()
    try:
        content, is_sample = renderer(feed_id)
        event_count = count_events(content)
        previous_snapshot = load_snapshot(event_snapshot_path(feed_id))
        current_snapshot = snapshot_from_ics(content)
        changes = compare_snapshots(previous_snapshot, current_snapshot)
        save_snapshot(event_snapshot_path(feed_id), current_snapshot)
        save_changes(event_changes_path(feed_id), changes)
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
            "changeSummary": summarize_changes(changes),
            "changesPath": display_path(event_changes_path(feed_id)),
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


def football_data_manifest_payload(teams: list, grouped_events: dict[int, list], generated_at: str) -> dict:
    return {
        "provider": FOOTBALL_DATA_PROVIDER_LABEL,
        "competition": DEFAULT_COMPETITION,
        "generatedAt": generated_at,
        "teams": [
            {
                "id": team.team_id,
                "name": team.name,
                "shortName": team.short_name,
                "tla": team.tla,
                "venue": team.venue,
                "competition": DEFAULT_COMPETITION,
                "feedId": team.feed_id,
                "feedPath": f"/feeds/{team.feed_id}.ics",
                "eventCount": len(grouped_events.get(team.team_id, [])),
                "updatedAt": generated_at,
            }
            for team in teams
        ],
    }


def save_football_data_manifest(payload: dict) -> None:
    FOOTBALL_DATA_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_text_preserving_newlines(
        FOOTBALL_DATA_MANIFEST_PATH,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def import_football_data_bundesliga_team_calendars() -> list[dict]:
    started_at = utc_now_iso()
    if not os.getenv(FOOTBALL_DATA_TOKEN_ENV, "").strip():
        return [
            {
                "feedId": "football-data-bl1-teams",
                "status": "error",
                "startedAt": started_at,
                "finishedAt": utc_now_iso(),
                "eventCount": None,
                "sample": False,
                "warnings": [],
                "error": f"{FOOTBALL_DATA_TOKEN_ENV} is not configured.",
                "outputPath": display_path(FOOTBALL_DATA_MANIFEST_PATH),
            }
        ]

    try:
        teams = fetch_bundesliga_teams()
        matches = fetch_bundesliga_matches()
        grouped_events = events_by_team(teams, matches)
        generated_at = utc_now_iso()
        save_football_data_manifest(football_data_manifest_payload(teams, grouped_events, generated_at))
    except Exception as exc:
        return [
            {
                "feedId": "football-data-bl1-teams",
                "status": "error",
                "startedAt": started_at,
                "finishedAt": utc_now_iso(),
                "eventCount": None,
                "sample": False,
                "warnings": [],
                "error": str(exc),
                "outputPath": display_path(FOOTBALL_DATA_MANIFEST_PATH),
            }
        ]

    results = []
    for team in teams:
        feed_id = team.feed_id
        events = grouped_events.get(team.team_id, [])
        calendar_name = f"{team.short_name} Bundesliga-Kalender"
        content = render_ics(events, calendar_name)
        event_count = count_events(content)
        previous_snapshot = load_snapshot(event_snapshot_path(feed_id))
        current_snapshot = snapshot_from_ics(content)
        changes = compare_snapshots(previous_snapshot, current_snapshot)
        save_snapshot(event_snapshot_path(feed_id), current_snapshot)
        save_changes(event_changes_path(feed_id), changes)
        warnings = []
        if event_count == 0:
            warnings.append("Feed contains no events.")
        output_path = write_feed_cache(feed_id, content)
        results.append(
            {
                "feedId": feed_id,
                "status": "warning" if warnings else "success",
                "startedAt": started_at,
                "finishedAt": utc_now_iso(),
                "eventCount": event_count,
                "sample": False,
                "warnings": warnings,
                "error": None,
                "outputPath": display_path(output_path),
                "changeSummary": summarize_changes(changes),
                "changesPath": display_path(event_changes_path(feed_id)),
            }
        )
    return results


def run_import_job(feed_ids: list[str] | None = None, renderer: RenderFeed = render_feed) -> list[dict]:
    selected_feed_ids = feed_ids or importable_feed_ids()
    results = []
    if feed_ids is None:
        results.extend(import_football_data_bundesliga_team_calendars())
    results.extend(import_calendar(feed_id, renderer) for feed_id in selected_feed_ids)
    append_import_runs(results)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import and cache published YourCalendar feeds.")
    parser.add_argument(
        "--feed",
        action="append",
        choices=sorted(importable_feed_ids()),
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
