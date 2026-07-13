from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GroupLogo:
    category: str
    group_path: str
    logo_bytes: bytes | None
    group_order: int
