from __future__ import annotations

import time

from .provider_resolvers import resolve_provider_id


def build_mapping_and_lock_rows(
    source_rows: list[dict[str, str]],
    lock_rows: list[dict[str, str]],
    refresh_provider: bool,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    lock_by_key = {(row["Team"], row["Provider"]): row["ICSId"] for row in lock_rows}
    mapping_rows: list[dict[str, str]] = []
    generated_lock_rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for source in source_rows:
        ics_id = resolve_ics_id(source, lock_by_key, refresh_provider)
        if ics_id in seen_ids:
            raise RuntimeError(f"Duplicate provider ID {ics_id} for {source['Team']}")
        seen_ids.add(ics_id)

        mapping_rows.append(build_mapping_row(source, ics_id))
        generated_lock_rows.append({"Team": source["Team"], "ICSId": ics_id, "Provider": source["API-Provider"]})

    return mapping_rows, generated_lock_rows


def resolve_ics_id(
    source: dict[str, str],
    lock_by_key: dict[tuple[str, str], str],
    refresh_provider: bool,
) -> str:
    team = source["Team"]
    provider = source["API-Provider"]
    ics_id = source["ICSId"] or lock_by_key.get((team, provider), "")
    if refresh_provider or not ics_id:
        ics_id = resolve_provider_id(source)
        time.sleep(2.1)
    if not ics_id:
        raise RuntimeError(f"No provider ID found for {team}")
    return ics_id


def build_mapping_row(source: dict[str, str], ics_id: str) -> dict[str, str]:
    return {
        "Kalendername": f"{source['Kalenderpfad']}/{source['Team']}",
        "Land": source["Land"],
        "Kategorie": source["Kategorie"],
        "Wettbewerb": source["Wettbewerb"],
        "API-Provider": source["API-Provider"],
        "API-Key-Provider": source["API-Key-Provider"],
        "ICSId": ics_id,
        "LogoBytes": "",
        "SubGroupOrder": source["SubGroupOrder"],
    }
