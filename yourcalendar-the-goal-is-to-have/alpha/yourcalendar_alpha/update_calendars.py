from __future__ import annotations

from .config.settings import load_settings
from .sync.report import format_sync_result
from .sync.service import sync_all_calendars


def main() -> int:
    settings = load_settings()
    results = sync_all_calendars(settings)
    for result in results:
        print(format_sync_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
