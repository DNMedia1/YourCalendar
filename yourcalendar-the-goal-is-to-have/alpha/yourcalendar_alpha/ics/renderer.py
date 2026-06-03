from __future__ import annotations

from datetime import datetime, timezone

from ..domain.calendar_event import CalendarEvent
from .line_formatter import escape_ics_text, fold_ics_line, format_utc_datetime
from .sequence import build_event_sequence


def render_ics_calendar(calendar_name: str, events: list[CalendarEvent]) -> str:
    generated_at = format_utc_datetime(datetime.now(timezone.utc))
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//YourCalendar//Alpha//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_ics_text(calendar_name)}",
    ]
    for event in sorted(events, key=lambda item: item.starts_at):
        lines.extend(render_ics_event(event, generated_at))
    lines.append("END:VCALENDAR")

    folded_lines: list[str] = []
    for line in lines:
        folded_lines.extend(fold_ics_line(line))
    return "\r\n".join(folded_lines) + "\r\n"


def render_ics_event(event: CalendarEvent, generated_at: str) -> list[str]:
    return [
        "BEGIN:VEVENT",
        f"UID:{escape_ics_text(event.uid)}",
        f"DTSTAMP:{generated_at}",
        f"DTSTART:{format_utc_datetime(event.starts_at)}",
        f"DTEND:{format_utc_datetime(event.ends_at)}",
        f"SUMMARY:{escape_ics_text(event.title)}",
        f"LOCATION:{escape_ics_text(event.location)}",
        f"DESCRIPTION:{escape_ics_text(event.description)}",
        f"SEQUENCE:{build_event_sequence(event.source_hash)}",
        "END:VEVENT",
    ]
