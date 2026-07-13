from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ..domain.calendar_entry import CalendarEntry


def build_calendar_public_url(settings: dict[str, Any], ics_id: str) -> str:
    base_url = str(settings.get("public_base_url") or "").rstrip("/")
    safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in ics_id)
    return f"{base_url}/ics/{quote(safe_id)}.ics"


def build_subscription_links(entry: CalendarEntry, settings: dict[str, Any]) -> dict[str, str]:
    public_url = build_calendar_public_url(settings, entry.ics_id)
    return {
        "name": entry.display_name,
        "ics": public_url,
        "google": f"https://calendar.google.com/calendar/r?cid={quote(public_url, safe='')}",
        "outlook": (
            "https://outlook.live.com/calendar/0/addcalendar"
            f"?url={quote(public_url, safe='')}&name={quote(entry.display_name, safe='')}"
        ),
        "apple": public_url.replace("http://", "webcal://").replace("https://", "webcal://", 1),
    }
