from __future__ import annotations

from typing import Any

from ..config.settings import resolve_path
from ..ics.renderer import render_ics_calendar
from ..mapping.loader import load_mapping
from .file_naming import safe_calendar_file_stem


def ensure_placeholder_ics_files(settings: dict[str, Any]) -> int:
    mapping_path = resolve_path(settings, settings["mapping_file"])
    output_dir = resolve_path(settings, settings["ics_output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    for entry in load_mapping(mapping_path):
        ics_path = output_dir / f"{safe_calendar_file_stem(entry.ics_id)}.ics"
        if ics_path.exists():
            continue
        ics_path.write_text(render_ics_calendar(entry.calendar_name, []), encoding="utf-8", newline="")
        created += 1
    return created
