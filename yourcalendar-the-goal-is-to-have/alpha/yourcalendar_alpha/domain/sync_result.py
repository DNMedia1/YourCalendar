from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SyncResult:
    calendar_id: str
    calendar_name: str
    created: int
    updated: int
    deleted: int
    written_path: Path
