from __future__ import annotations

from typing import Any

from .base import CalendarProvider
from .thesportsdb_provider import TheSportsDBProvider


def build_provider_registry(settings: dict[str, Any]) -> dict[str, CalendarProvider]:
    provider_defaults = settings.get("provider_defaults", {})
    sportsdb_settings = provider_defaults.get("TheSportsDB", {})
    return {
        "TheSportsDB": TheSportsDBProvider(
            base_url=sportsdb_settings.get("base_url", "https://www.thesportsdb.com/api/v1/json"),
            free_api_key=str(sportsdb_settings.get("free_api_key", "123")),
            default_duration_minutes=int(settings.get("default_event_duration_minutes", 120)),
        )
    }
