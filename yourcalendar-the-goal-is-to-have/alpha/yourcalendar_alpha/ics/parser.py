from __future__ import annotations

from pathlib import Path


def parse_existing_event_sequences(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    sequences_by_uid: dict[str, str] = {}
    current_uid = ""
    current_sequence = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("UID:"):
            current_uid = line[4:]
        elif line.startswith("SEQUENCE:"):
            current_sequence = line[9:]
        elif line == "END:VEVENT" and current_uid:
            sequences_by_uid[current_uid] = current_sequence
            current_uid = ""
            current_sequence = ""
    return sequences_by_uid
