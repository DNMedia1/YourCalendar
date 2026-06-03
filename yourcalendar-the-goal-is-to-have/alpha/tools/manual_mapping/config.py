from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FOOTBALL_SOURCE = ROOT / "data" / "football_team_source.csv"
NFL_SOURCE = ROOT / "data" / "nfl_team_source.csv"
NBA_SOURCE = ROOT / "data" / "nba_team_source.csv"
SOURCE_FILES = [FOOTBALL_SOURCE, NFL_SOURCE, NBA_SOURCE]
OUT = ROOT / "data" / "mapping.csv"
LOCK = ROOT / "data" / "mapping.provider-lock.csv"
THESPORTSDB_BASE_URL = "https://www.thesportsdb.com/api/v1/json/123"

MAPPING_FIELDNAMES = [
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
OPTIONAL_SOURCE_FIELDNAMES = ["Kategorie", "Kalenderpfad"]
