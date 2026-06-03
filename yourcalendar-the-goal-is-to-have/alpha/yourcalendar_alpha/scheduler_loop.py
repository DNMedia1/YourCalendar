from __future__ import annotations

import time
from typing import Any

from .config.settings import load_settings
from .sync.report import format_sync_result
from .sync.service import sync_all_calendars


def refresh_interval_seconds(settings: dict[str, Any]) -> int:
    return int(float(settings.get("refresh_interval_hours", 6)) * 60 * 60)


def main() -> int:
    settings = load_settings()
    interval_seconds = refresh_interval_seconds(settings)
    while True:
        results = sync_all_calendars(settings)
        for result in results:
            print(format_sync_result(result), flush=True)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
