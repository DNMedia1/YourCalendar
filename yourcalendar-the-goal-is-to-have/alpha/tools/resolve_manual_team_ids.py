from __future__ import annotations

import argparse

from manual_mapping.builder import build_mapping_and_lock_rows
from manual_mapping.config import LOCK, LOCK_FIELDNAMES, MAPPING_FIELDNAMES, OUT
from manual_mapping.csv_table import write_csv_rows
from manual_mapping.provider_lock_diff import print_provider_lock_diff, provider_lock_changed
from manual_mapping.team_source_loader import load_provider_lock_rows, load_team_source_rows


def main() -> int:
    args = parse_args()
    source_rows = load_team_source_rows()
    lock_rows = load_provider_lock_rows() if LOCK.exists() else []
    mapping_rows, generated_lock_rows = build_mapping_and_lock_rows(
        source_rows=source_rows,
        lock_rows=lock_rows,
        refresh_provider=args.refresh_provider,
    )

    if provider_lock_changed(lock_rows, generated_lock_rows) and not args.update_lock:
        print("Provider ID lock changed. Review differences before accepting:")
        print_provider_lock_diff(lock_rows, generated_lock_rows)
        print("Run again with --update-lock only after intentionally accepting the changes.")
        return 1

    write_csv_rows(OUT, MAPPING_FIELDNAMES, mapping_rows)
    write_csv_rows(LOCK, LOCK_FIELDNAMES, generated_lock_rows)
    print(f"Wrote {len(mapping_rows)} calendar mappings to {OUT}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the static sports mapping from curated team sources.")
    parser.add_argument("--refresh-provider", action="store_true", help="Resolve/verify IDs through the configured provider.")
    parser.add_argument("--update-lock", action="store_true", help="Accept generated provider ID changes and rewrite the lock file.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
