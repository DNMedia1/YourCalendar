from __future__ import annotations

from pathlib import Path

from .config import LOCK, LOCK_FIELDNAMES, OPTIONAL_SOURCE_FIELDNAMES, SOURCE_FIELDNAMES, SOURCE_FILES
from .csv_table import read_csv_rows


def load_team_source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_file in SOURCE_FILES:
        rows.extend(load_source_file_rows(source_file))
    if not rows:
        raise RuntimeError(f"No teams found in configured source files")
    return rows


def load_source_file_rows(source_file: Path) -> list[dict[str, str]]:
    rows = read_csv_rows(source_file)
    if not rows:
        raise RuntimeError(f"No teams found in {source_file}")
    missing = sorted(set(SOURCE_FIELDNAMES).difference(rows[0]))
    if missing:
        raise RuntimeError(f"{source_file} is missing columns: {', '.join(missing)}")
    for index, row in enumerate(rows, start=2):
        for fieldname in SOURCE_FIELDNAMES + OPTIONAL_SOURCE_FIELDNAMES:
            row[fieldname] = (row.get(fieldname) or "").strip()
        row["Kategorie"] = row["Kategorie"] or "Sport"
        row["Kalenderpfad"] = row["Kalenderpfad"] or build_default_calendar_path(row)
        if not row["SubGroupOrder"].isdigit():
            raise RuntimeError(f"Invalid SubGroupOrder at {source_file}:{index}")
    return rows


def build_default_calendar_path(row: dict[str, str]) -> str:
    return f"Fussball/{row['Land']}/{row['Wettbewerb']}"


def load_provider_lock_rows() -> list[dict[str, str]]:
    rows = read_csv_rows(LOCK)
    for row in rows:
        for fieldname in LOCK_FIELDNAMES:
            row[fieldname] = (row.get(fieldname) or "").strip()
    return rows
