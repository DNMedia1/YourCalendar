from __future__ import annotations

from .config import LOCK, LOCK_FIELDNAMES, SOURCE, SOURCE_FIELDNAMES
from .csv_table import read_csv_rows


def load_team_source_rows() -> list[dict[str, str]]:
    rows = read_csv_rows(SOURCE)
    if not rows:
        raise RuntimeError(f"No teams found in {SOURCE}")
    missing = sorted(set(SOURCE_FIELDNAMES).difference(rows[0]))
    if missing:
        raise RuntimeError(f"{SOURCE} is missing columns: {', '.join(missing)}")
    for index, row in enumerate(rows, start=2):
        for fieldname in SOURCE_FIELDNAMES:
            row[fieldname] = (row.get(fieldname) or "").strip()
        if not row["SubGroupOrder"].isdigit():
            raise RuntimeError(f"Invalid SubGroupOrder at {SOURCE}:{index}")
    return rows


def load_provider_lock_rows() -> list[dict[str, str]]:
    rows = read_csv_rows(LOCK)
    for row in rows:
        for fieldname in LOCK_FIELDNAMES:
            row[fieldname] = (row.get(fieldname) or "").strip()
    return rows
