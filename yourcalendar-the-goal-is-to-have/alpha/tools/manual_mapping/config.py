from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "football_team_source.csv"
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
