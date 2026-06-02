from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CalendarEvent:
    uid: str
    title: str
    starts_at: datetime
    ends_at: datetime
    location: str
    description: str
    source_hash: str


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> list[str]:
    if len(line) <= 75:
        return [line]
    lines = []
    while len(line) > 75:
        lines.append(line[:75])
        line = " " + line[75:]
    lines.append(line)
    return lines


def _format_dt(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def event_sequence(source_hash: str) -> str:
    return str(int(hashlib.sha1(source_hash.encode("utf-8")).hexdigest()[:6], 16))


def render_calendar(calendar_name: str, events: list[CalendarEvent]) -> str:
    now = _format_dt(datetime.now(timezone.utc))
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//YourCalendar//Alpha//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
    ]
    for event in sorted(events, key=lambda item: item.starts_at):
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_escape(event.uid)}",
                f"DTSTAMP:{now}",
                f"DTSTART:{_format_dt(event.starts_at)}",
                f"DTEND:{_format_dt(event.ends_at)}",
                f"SUMMARY:{_escape(event.title)}",
                f"LOCATION:{_escape(event.location)}",
                f"DESCRIPTION:{_escape(event.description)}",
                f"SEQUENCE:{event_sequence(event.source_hash)}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    folded: list[str] = []
    for line in lines:
        folded.extend(_fold(line))
    return "\r\n".join(folded) + "\r\n"


def parse_existing_uids(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    uids: dict[str, str] = {}
    current_uid = ""
    current_sequence = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("UID:"):
            current_uid = line[4:]
        elif line.startswith("SEQUENCE:"):
            current_sequence = line[9:]
        elif line == "END:VEVENT" and current_uid:
            uids[current_uid] = current_sequence
            current_uid = ""
            current_sequence = ""
    return uids
