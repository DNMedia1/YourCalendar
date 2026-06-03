from __future__ import annotations

from ..domain.sync_result import SyncResult


def format_sync_result(result: SyncResult) -> str:
    return (
        f"{result.calendar_id}: created={result.created} "
        f"updated={result.updated} deleted={result.deleted} -> {result.written_path}"
    )
