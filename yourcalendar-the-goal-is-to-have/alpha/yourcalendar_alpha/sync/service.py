from __future__ import annotations

from pathlib import Path
from typing import Any

from ..calendar.file_naming import safe_calendar_file_stem
from ..config.settings import resolve_path
from ..domain.calendar_entry import CalendarEntry
from ..domain.sync_result import SyncResult
from ..ics.parser import parse_existing_event_sequences
from ..ics.renderer import render_ics_calendar
from ..mapping import load_mapping
from ..providers.base import CalendarProvider
from ..providers.registry import build_provider_registry
from .change_counter import (
    build_event_sequences,
    count_created_events,
    count_deleted_events,
    count_updated_events,
)


def sync_all_calendars(
    settings: dict[str, Any],
    providers: dict[str, CalendarProvider] | None = None,
) -> list[SyncResult]:
    mapping_path = resolve_path(settings, settings["mapping_file"])
    output_dir = resolve_path(settings, settings["ics_output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = load_mapping(mapping_path)
    provider_registry = providers or build_provider_registry(settings)

    return [sync_calendar_entry(entry, provider_registry, output_dir) for entry in entries]


def sync_calendar_entry(
    entry: CalendarEntry,
    provider_registry: dict[str, CalendarProvider],
    output_dir: Path,
) -> SyncResult:
    provider = provider_registry.get(entry.api_provider)
    if not provider:
        raise ValueError(f"No provider registered for '{entry.api_provider}'")

    events = provider.fetch_events(entry)
    target_path = output_dir / f"{safe_calendar_file_stem(entry.ics_id)}.ics"
    existing_sequences = parse_existing_event_sequences(target_path)
    new_sequences = build_event_sequences(events)
    target_path.write_text(render_ics_calendar(entry.display_name, events), encoding="utf-8", newline="")

    return SyncResult(
        calendar_id=entry.ics_id,
        calendar_name=entry.calendar_name,
        created=count_created_events(existing_sequences, new_sequences),
        updated=count_updated_events(existing_sequences, new_sequences),
        deleted=count_deleted_events(existing_sequences, new_sequences),
        written_path=target_path,
    )
