from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen

from .config import THESPORTSDB_BASE_URL


def resolve_provider_id(source: dict[str, str]) -> str:
    existing_id = source.get("ICSId") or ""
    if existing_id:
        team = lookup_thesportsdb_team(existing_id)
        if team and not looks_like_womens_team(team):
            return existing_id

    payload = get_json(f"{THESPORTSDB_BASE_URL}/searchteams.php?{urlencode({'t': source['Team']})}")
    teams = [team for team in payload.get("teams") or [] if not looks_like_womens_team(team)]
    if not teams:
        return ""
    return str(teams[0].get("idTeam") or "")


def lookup_thesportsdb_team(team_id: str) -> dict[str, str] | None:
    payload = get_json(f"{THESPORTSDB_BASE_URL}/lookupteam.php?{urlencode({'id': team_id})}")
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
