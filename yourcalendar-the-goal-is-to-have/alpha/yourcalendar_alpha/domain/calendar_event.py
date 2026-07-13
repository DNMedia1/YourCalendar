from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CalendarEvent:
    uid: str
    title: str
    starts_at: datetime
    ends_at: datetime
    location: str
    description: str
    source_hash: str
