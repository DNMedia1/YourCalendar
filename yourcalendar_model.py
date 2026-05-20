from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EventStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    TENTATIVE = "TENTATIVE"
    CANCELLED = "CANCELLED"
    POSTPONED = "POSTPONED"
    UNKNOWN = "UNKNOWN"

    @property
    def ics_value(self) -> str:
        if self == EventStatus.CANCELLED:
            return "CANCELLED"
        if self in {EventStatus.TENTATIVE, EventStatus.POSTPONED, EventStatus.UNKNOWN}:
            return "TENTATIVE"
        return "CONFIRMED"


class EventCategory(StrEnum):
    SPORTS = "sports"
    POLITICS = "politics"
    CITY = "city"
    CULTURE = "culture"
    HOLIDAYS = "holidays"
    PARTNER = "partner"
    SAMPLE = "sample"
    UNKNOWN = "unknown"


class SourceQuality(StrEnum):
    OFFICIAL = "official"
    PARTNER = "partner"
    PAID_PROVIDER = "paid_provider"
    COMMUNITY = "community"
    SCRAPED = "scraped"
    MANUAL = "manual"
    SAMPLE = "sample"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CalendarEvent:
    """Normalized event model used between source importers and feed renderers."""

    uid: str
    title: str
    starts_at: datetime
    ends_at: datetime
    source: str
    category: EventCategory | str = EventCategory.UNKNOWN
    source_url: str | None = None
    location: str | None = None
    description: str | None = None
    status: EventStatus | str = EventStatus.CONFIRMED
    source_quality: SourceQuality | str = SourceQuality.UNKNOWN
    external_id: str | None = None
    all_day: bool = False
    quality_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self._require_text("uid", self.uid)
        self._require_text("title", self.title)
        self._require_text("source", self.source)
        self._require_aware_datetime("starts_at", self.starts_at)
        self._require_aware_datetime("ends_at", self.ends_at)
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        if self.all_day and (
            self.starts_at.time().isoformat() != "00:00:00"
            or self.ends_at.time().isoformat() != "00:00:00"
        ):
            raise ValueError("all_day events must use local midnight boundaries")

        object.__setattr__(self, "status", EventStatus(self.status))
        object.__setattr__(self, "category", EventCategory(self.category))
        object.__setattr__(self, "source_quality", SourceQuality(self.source_quality))
        object.__setattr__(self, "quality_notes", tuple(self.quality_notes))

    @staticmethod
    def _require_text(field_name: str, value: str) -> None:
        if not value or not value.strip():
            raise ValueError(f"{field_name} must not be empty")

    @staticmethod
    def _require_aware_datetime(field_name: str, value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware")

    @property
    def ics_status(self) -> str:
        return EventStatus(self.status).ics_value

    @property
    def source_label(self) -> str:
        return f"{self.source} ({self.source_quality})"
