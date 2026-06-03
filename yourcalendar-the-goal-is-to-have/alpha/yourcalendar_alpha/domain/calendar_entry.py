from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CalendarEntry:
    calendar_name: str
    country: str
    category: str
    competition: str
    api_provider: str
    api_key_provider: str
    ics_id: str
    logo_bytes: bytes | None
    subgroup_order: int

    @property
    def path_parts(self) -> list[str]:
        return [part.strip() for part in self.calendar_name.split("/") if part.strip()]

    @property
    def display_name(self) -> str:
        parts = self.path_parts
        return parts[-1] if parts else self.calendar_name

    @property
    def group_path(self) -> str:
        return "/".join(self.path_parts[:-1])
