from __future__ import annotations

from datetime import datetime, timezone


def parse_thesportsdb_datetime(date_value: str, time_value: str) -> datetime:
    clean_time = time_value.replace("Z", "").strip() or "00:00:00"
    if "T" in clean_time:
        parsed = datetime.fromisoformat(clean_time.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    if len(clean_time) == 5:
        clean_time = f"{clean_time}:00"
    try:
        return datetime.fromisoformat(f"{date_value}T{clean_time}").replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.fromisoformat(f"{date_value}T00:00:00").replace(tzinfo=timezone.utc)
