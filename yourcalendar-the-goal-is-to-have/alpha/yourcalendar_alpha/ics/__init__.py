from __future__ import annotations

from ..domain.calendar_event import CalendarEvent
from .parser import parse_existing_event_sequences
from .renderer import render_ics_calendar
from .sequence import build_event_sequence


event_sequence = build_event_sequence
parse_existing_uids = parse_existing_event_sequences
render_calendar = render_ics_calendar


__all__ = [
    "CalendarEvent",
    "build_event_sequence",
    "event_sequence",
    "parse_existing_event_sequences",
    "parse_existing_uids",
    "render_calendar",
    "render_ics_calendar",
]
