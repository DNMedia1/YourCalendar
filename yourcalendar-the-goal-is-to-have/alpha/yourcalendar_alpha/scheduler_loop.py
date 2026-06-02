from __future__ import annotations

import time

from .settings import load_settings
from .sync import sync_all


def main() -> int:
    settings = load_settings()
    interval_seconds = int(float(settings.get("refresh_interval_hours", 6)) * 60 * 60)
    while True:
        results = sync_all(settings)
        for result in results:
            print(
                f"{result.calendar_id}: created={result.created} "
                f"updated={result.updated} deleted={result.deleted} -> {result.written_path}",
                flush=True,
            )
        time.sleep(interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
