from __future__ import annotations

from datetime import datetime, timezone


def escape_ics_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def fold_ics_line(line: str) -> list[str]:
    if len(line) <= 75:
        return [line]
    folded_lines = []
    while len(line) > 75:
        folded_lines.append(line[:75])
        line = " " + line[75:]
    folded_lines.append(line)
    return folded_lines


def format_utc_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
