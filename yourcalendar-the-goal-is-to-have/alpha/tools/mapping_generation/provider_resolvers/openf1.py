from __future__ import annotations


def resolve_openf1_provider_id(source: dict[str, str]) -> str:
    ics_id = source.get("ICSId") or ""
    if ics_id != "formula-1":
        raise RuntimeError("OpenF1 Formula 1 mappings must use ICSId 'formula-1'")
    return ics_id
