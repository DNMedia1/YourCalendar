from __future__ import annotations

from ..domain.calendar_event import CalendarEvent
from ..ics.sequence import build_event_sequence


def build_event_sequences(events: list[CalendarEvent]) -> dict[str, str]:
    return {event.uid: build_event_sequence(event.source_hash) for event in events}


def count_created_events(existing_sequences: dict[str, str], new_sequences: dict[str, str]) -> int:
    return len([uid for uid in new_sequences if uid not in existing_sequences])


def count_updated_events(existing_sequences: dict[str, str], new_sequences: dict[str, str]) -> int:
    return len(
        [
            uid
            for uid, sequence in new_sequences.items()
            if uid in existing_sequences and existing_sequences[uid] != sequence
        ]
    )


def count_deleted_events(existing_sequences: dict[str, str], new_sequences: dict[str, str]) -> int:
    return len([uid for uid in existing_sequences if uid not in new_sequences])
