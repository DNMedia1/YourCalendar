from __future__ import annotations

from dataclasses import dataclass, field

from .calendar_entry import CalendarEntry


@dataclass
class CalendarTreeNode:
    name: str
    path: str
    depth: int = 0
    children: dict[str, "CalendarTreeNode"] = field(default_factory=dict)
    entries: list[CalendarEntry] = field(default_factory=list)
