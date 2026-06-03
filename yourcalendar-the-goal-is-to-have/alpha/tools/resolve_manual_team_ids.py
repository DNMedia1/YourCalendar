from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "football_team_source.csv"
OUT = ROOT / "data" / "mapping.csv"
LOCK = ROOT / "data" / "mapping.provider-lock.csv"
BASE_URL = "https://www.thesportsdb.com/api/v1/json/123"

FIELDNAMES = [
    "Kalendername",
    "Land",
    "Kategorie",
    "Wettbewerb",
    "API-Provider",
    "API-Key-Provider",
    "ICSId",
    "LogoBytes",
    "SubGroupOrder",
]

LOCK_FIELDNAMES = ["Team", "ICSId", "Provider"]
SOURCE_FIELDNAMES = ["Land", "Wettbewerb", "Team", "SubGroupOrder", "API-Provider", "API-Key-Provider", "ICSId"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the static football mapping from the curated team source.")
    parser.add_argument("--refresh-provider", action="store_true", help="Resolve/verify IDs through the configured provider.")
    parser.add_argument("--update-lock", action="store_true", help="Accept generated provider ID changes and rewrite the lock file.")
    args = parser.parse_args()

    source_rows = load_source()
    lock_rows = load_lock() if LOCK.exists() else []
    lock_by_key = {(row["Team"], row["Provider"]): row["ICSId"] for row in lock_rows}

    mapping_rows: list[dict[str, str]] = []
    generated_lock: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for source in source_rows:
        team = source["Team"]
        provider = source["API-Provider"]
        ics_id = source["ICSId"] or lock_by_key.get((team, provider), "")
        if args.refresh_provider or not ics_id:
            ics_id = resolve_provider_id(source)
            time.sleep(2.1)
        if not ics_id:
            raise RuntimeError(f"No provider ID found for {team}")
        if ics_id in seen_ids:
            raise RuntimeError(f"Duplicate provider ID {ics_id} for {team}")
        seen_ids.add(ics_id)

        mapping_rows.append(
            {
                "Kalendername": f"Fussball/{source['Land']}/{source['Wettbewerb']}/{team}",
                "Land": source["Land"],
                "Kategorie": "Sport",
                "Wettbewerb": source["Wettbewerb"],
                "API-Provider": provider,
                "API-Key-Provider": source["API-Key-Provider"],
                "ICSId": ics_id,
                "LogoBytes": "",
                "SubGroupOrder": source["SubGroupOrder"],
            }
        )
        generated_lock.append({"Team": team, "ICSId": ics_id, "Provider": provider})

    if lock_rows and lock_rows != generated_lock and not args.update_lock:
        print("Provider ID lock changed. Review differences before accepting:")
        print_lock_diff(lock_rows, generated_lock)
        print("Run again with --update-lock only after intentionally accepting the changes.")
        return 1

    write_csv(OUT, FIELDNAMES, mapping_rows)
    write_csv(LOCK, LOCK_FIELDNAMES, generated_lock)
    print(f"Wrote {len(mapping_rows)} calendar mappings to {OUT}")
    return 0


def load_source() -> list[dict[str, str]]:
    rows = read_csv(SOURCE)
    if not rows:
        raise RuntimeError(f"No teams found in {SOURCE}")
    missing = sorted(set(SOURCE_FIELDNAMES).difference(rows[0]))
    if missing:
        raise RuntimeError(f"{SOURCE} is missing columns: {', '.join(missing)}")
    for index, row in enumerate(rows, start=2):
        for fieldname in SOURCE_FIELDNAMES:
            row[fieldname] = (row.get(fieldname) or "").strip()
        if not row["SubGroupOrder"].isdigit():
            raise RuntimeError(f"Invalid SubGroupOrder at {SOURCE}:{index}")
    return rows


def load_lock() -> list[dict[str, str]]:
    rows = read_csv(LOCK)
    for row in rows:
        for fieldname in LOCK_FIELDNAMES:
            row[fieldname] = (row.get(fieldname) or "").strip()
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def resolve_provider_id(source: dict[str, str]) -> str:
    provider = source["API-Provider"]
    if provider != "TheSportsDB":
        raise RuntimeError(f"No resolver implemented for provider {provider}")
    existing_id = source.get("ICSId") or ""
    if existing_id:
        team = lookup_thesportsdb_team(existing_id)
        if team and not looks_like_womens_team(team):
            return existing_id
    query = source["Team"]
    payload = get_json(f"{BASE_URL}/searchteams.php?{urlencode({'t': query})}")
    teams = [team for team in payload.get("teams") or [] if not looks_like_womens_team(team)]
    if not teams:
        return ""
    return str(teams[0].get("idTeam") or "")


def lookup_thesportsdb_team(team_id: str) -> dict[str, str] | None:
    payload = get_json(f"{BASE_URL}/lookupteam.php?{urlencode({'id': team_id})}")
    teams = payload.get("teams") or []
    return teams[0] if teams else None


def get_json(url: str) -> dict:
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def looks_like_womens_team(team: dict[str, str]) -> bool:
    haystack = " ".join(
        str(team.get(field) or "") for field in ["strTeam", "strAlternate", "strLeague"]
    ).lower()
    return any(marker in haystack for marker in ["women", "femenino", "female", "frauen"])


def print_lock_diff(current: list[dict[str, str]], generated: list[dict[str, str]]) -> None:
    current_by_key = {(row["Team"], row["Provider"]): row for row in current}
    generated_by_key = {(row["Team"], row["Provider"]): row for row in generated}
    for key in sorted(set(current_by_key) | set(generated_by_key)):
        old = current_by_key.get(key)
        new = generated_by_key.get(key)
        if old != new:
            print(f"- {key[0]} / {key[1]}: {old} -> {new}")


if __name__ == "__main__":
    raise SystemExit(main())
