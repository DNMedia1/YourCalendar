from __future__ import annotations


def safe_calendar_file_stem(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
