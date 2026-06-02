from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ics import event_sequence, parse_existing_uids, render_calendar
from .mapping import CalendarEntry, load_mapping
from .providers import CalendarProvider, build_provider_registry
from .settings import resolve_path


@dataclass(frozen=True)
class SyncResult:
    calendar_id: str
    calendar_name: str
    created: int
    updated: int
    deleted: int
    written_path: Path


def sync_all(settings: dict[str, Any], providers: dict[str, CalendarProvider] | None = None) -> list[SyncResult]:
    mapping_path = resolve_path(settings, settings["mapping_file"])
    output_dir = resolve_path(settings, settings["ics_output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = load_mapping(mapping_path)
    provider_registry = providers or build_provider_registry(settings)
    results: list[SyncResult] = []

    for entry in entries:
        provider = provider_registry.get(entry.api_provider)
        if not provider:
            raise ValueError(f"No provider registered for '{entry.api_provider}'")
        events = provider.fetch_events(entry)
        target_path = output_dir / f"{_safe_file_name(entry.ics_id)}.ics"
        existing = parse_existing_uids(target_path)
        rendered = render_calendar(entry.display_name, events)
        new_sequences = {event.uid: event_sequence(event.source_hash) for event in events}
        created = len([uid for uid in new_sequences if uid not in existing])
        updated = len([uid for uid, sequence in new_sequences.items() if uid in existing and existing[uid] != sequence])
        deleted = len([uid for uid in existing if uid not in new_sequences])
        target_path.write_text(rendered, encoding="utf-8", newline="")
        results.append(
            SyncResult(
                calendar_id=entry.ics_id,
                calendar_name=entry.calendar_name,
                created=created,
                updated=updated,
                deleted=deleted,
                written_path=target_path,
            )
        )
    return results


def _safe_file_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
