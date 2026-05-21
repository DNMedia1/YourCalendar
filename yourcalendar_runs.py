from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SourceRunRecord:
    source_id: str
    status: str
    checked_at: datetime
    checked_label: str
    event_count: int
    message: str
    technical_detail: str | None = None


def source_run_payload(record: SourceRunRecord) -> dict:
    payload = {
        "sourceId": record.source_id,
        "status": record.status,
        "checkedAt": record.checked_at.isoformat(),
        "checkedLabel": record.checked_label,
        "eventCount": record.event_count,
        "message": record.message,
    }
    if record.technical_detail:
        payload["technicalDetail"] = record.technical_detail
    return payload


def load_source_runs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    runs = payload.get("runs", [])
    if not isinstance(runs, list):
        return []
    return [run for run in runs if isinstance(run, dict)]


def latest_runs_by_source(path: Path) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for run in load_source_runs(path):
        source_id = run.get("sourceId")
        checked_at = run.get("checkedAt")
        if not source_id or not checked_at:
            continue
        previous = latest.get(source_id)
        if previous is None or checked_at > previous.get("checkedAt", ""):
            latest[source_id] = run
    return latest


def record_source_run(path: Path, record: SourceRunRecord, max_runs: int = 100) -> dict:
    runs = load_source_runs(path)
    run_payload = source_run_payload(record)
    runs.append(run_payload)
    runs = sorted(runs, key=lambda item: item.get("checkedAt", ""))[-max_runs:]

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(
        json.dumps({"runs": runs}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)
    return run_payload
