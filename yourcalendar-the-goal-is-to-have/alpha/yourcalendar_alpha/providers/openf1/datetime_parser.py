from __future__ import annotations

from datetime import datetime, timezone


def parse_openf1_datetime(value: str) -> datetime | None:
    normalized_value = value.strip()
    if not normalized_value:
        return None
    if normalized_value.endswith("Z"):
        normalized_value = f"{normalized_value[:-1]}+00:00"
    parsed = datetime.fromisoformat(normalized_value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
