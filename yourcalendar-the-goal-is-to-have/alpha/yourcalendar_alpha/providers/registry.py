from __future__ import annotations

from typing import Any

from .base import CalendarProvider
from .openf1_provider import OpenF1Provider
from .thesportsdb_provider import TheSportsDBProvider


def build_provider_registry(settings: dict[str, Any]) -> dict[str, CalendarProvider]:
    provider_defaults = settings.get("provider_defaults", {})
    sportsdb_settings = provider_defaults.get("TheSportsDB", {})
    openf1_settings = provider_defaults.get("OpenF1", {})
    return {
        "TheSportsDB": TheSportsDBProvider(
            base_url=sportsdb_settings.get("base_url", "https://www.thesportsdb.com/api/v1/json"),
            free_api_key=str(sportsdb_settings.get("free_api_key", "123")),
            default_duration_minutes=int(settings.get("default_event_duration_minutes", 120)),
        ),
        "OpenF1": OpenF1Provider(
            base_url=openf1_settings.get("base_url", "https://api.openf1.org/v1"),
            default_duration_minutes=int(openf1_settings.get("default_duration_minutes", 120)),
            years=parse_openf1_years(openf1_settings.get("years")),
        ),
    }


def parse_openf1_years(value: Any) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("OpenF1 provider setting 'years' must be a list of integers")
    return [int(year) for year in value]
