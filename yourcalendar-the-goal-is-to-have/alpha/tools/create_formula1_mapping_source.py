from __future__ import annotations

from mapping_generation.config import FORMULA1_SOURCE, ROOT
from mapping_generation.csv_table import read_csv_rows, write_csv_rows


FORMULA1_SOURCE_FIELDNAMES = [
    "Kategorie",
    "Kalenderpfad",
    "Land",
    "Wettbewerb",
    "Team",
    "SubGroupOrder",
    "API-Provider",
    "API-Key-Provider",
    "ICSId",
]
FORMULA1_SOURCE_ROWS = [
    {
        "Kategorie": "Sport",
        "Kalenderpfad": "Motorsport/Formel 1",
        "Land": "Global",
        "Wettbewerb": "Motorsport/Formel 1",
        "Team": "Veranstaltungen",
        "SubGroupOrder": "1",
        "API-Provider": "OpenF1",
        "API-Key-Provider": "",
        "ICSId": "formula-1",
    }
]
GROUP_LOGO_SETTINGS = ROOT / "data" / "group_logo_settings.csv"
GROUP_LOGO_FIELDNAMES = ["Kategorie", "GroupPath", "LogoBytes", "groupOrder"]
FORMULA1_GROUP_ROWS = [
    {"Kategorie": "Sport", "GroupPath": "Motorsport", "LogoBytes": "", "groupOrder": "4"},
    {"Kategorie": "Sport", "GroupPath": "Motorsport/Formel 1", "LogoBytes": "", "groupOrder": "1"},
]


def main() -> int:
    write_csv_rows(FORMULA1_SOURCE, FORMULA1_SOURCE_FIELDNAMES, FORMULA1_SOURCE_ROWS)
    ensure_formula1_group_rows()
    print(f"Wrote OpenF1 Formula 1 source mapping to {FORMULA1_SOURCE}")
    return 0


def ensure_formula1_group_rows() -> None:
    rows = read_csv_rows(GROUP_LOGO_SETTINGS)
    row_by_key = {(row["Kategorie"], row["GroupPath"]): row for row in rows}
    for group_row in FORMULA1_GROUP_ROWS:
        row_by_key[(group_row["Kategorie"], group_row["GroupPath"])] = group_row
    write_csv_rows(GROUP_LOGO_SETTINGS, GROUP_LOGO_FIELDNAMES, list(row_by_key.values()))


if __name__ == "__main__":
    raise SystemExit(main())
