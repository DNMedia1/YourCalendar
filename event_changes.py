from __future__ import annotations

import json
from pathlib import Path


TRACKED_FIELDS = ("summary", "startsAt", "location", "status")


def unfold_ics_lines(content: str) -> list[str]:
    lines: list[str] = []
    for raw_line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw_line.startswith((" ", "\t")) and lines:
            lines[-1] += raw_line[1:]
        elif raw_line:
            lines.append(raw_line)
    return lines


def property_value(line: str) -> tuple[str, str]:
    key, _, value = line.partition(":")
    key = key.split(";", 1)[0].upper()
    return key, value


def snapshot_from_ics(content: str) -> dict[str, dict]:
    events: dict[str, dict] = {}
    current: dict[str, str] | None = None
    for line in unfold_ics_lines(content):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current and current.get("uid"):
                uid = current["uid"]
                events[uid] = {
                    "uid": uid,
                    "summary": current.get("summary", ""),
                    "startsAt": current.get("startsAt", ""),
                    "location": current.get("location", ""),
                    "status": current.get("status", "CONFIRMED"),
                }
            current = None
            continue
        if current is None:
            continue
        key, value = property_value(line)
        if key == "UID":
            current["uid"] = value
        elif key == "SUMMARY":
            current["summary"] = value
        elif key == "DTSTART":
            current["startsAt"] = value
        elif key == "LOCATION":
            current["location"] = value
        elif key == "STATUS":
            current["status"] = value
    return events


def compare_snapshots(previous: dict[str, dict], current: dict[str, dict]) -> list[dict]:
    changes: list[dict] = []
    for uid, event in sorted(current.items()):
        old_event = previous.get(uid)
        if old_event is None:
            changes.append({"uid": uid, "type": "new", "event": event})
            continue
        changed_fields = {
            field: {"before": old_event.get(field, ""), "after": event.get(field, "")}
            for field in TRACKED_FIELDS
            if old_event.get(field, "") != event.get(field, "")
        }
        if changed_fields:
            changes.append(
                {
                    "uid": uid,
                    "type": "changed",
                    "fields": changed_fields,
                    "event": event,
                }
            )
    for uid, event in sorted(previous.items()):
        if uid not in current:
            changes.append({"uid": uid, "type": "missing", "event": event})
    return changes


def summarize_changes(changes: list[dict]) -> dict:
    return {
        "total": len(changes),
        "new": sum(1 for change in changes if change["type"] == "new"),
        "changed": sum(1 for change in changes if change["type"] == "changed"),
        "missing": sum(1 for change in changes if change["type"] == "missing"),
    }


def load_snapshot(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_snapshot(path: Path, snapshot: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_changes(path: Path, changes: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"summary": summarize_changes(changes), "changes": changes}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
