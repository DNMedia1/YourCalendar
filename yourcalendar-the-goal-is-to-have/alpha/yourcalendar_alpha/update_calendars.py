from __future__ import annotations

from .settings import load_settings
from .sync import sync_all


def main() -> int:
    settings = load_settings()
    results = sync_all(settings)
    for result in results:
        print(
            f"{result.calendar_id}: created={result.created} "
            f"updated={result.updated} deleted={result.deleted} -> {result.written_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
