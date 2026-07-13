from __future__ import annotations

from ..domain.sync_result import SyncResult
from .service import sync_all_calendars, sync_calendar_entry


sync_all = sync_all_calendars


__all__ = ["SyncResult", "sync_all", "sync_all_calendars", "sync_calendar_entry"]
