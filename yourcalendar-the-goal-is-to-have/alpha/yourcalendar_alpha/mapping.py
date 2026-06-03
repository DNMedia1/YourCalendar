from __future__ import annotations

import base64
import csv
from dataclasses import dataclass
from pathlib import Path


REQUIRED_COLUMNS = [
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


@dataclass(frozen=True)
class CalendarEntry:
    calendar_name: str
    country: str
    category: str
    competition: str
    api_provider: str
    api_key_provider: str
    ics_id: str
    logo_bytes: bytes | None
    subgroup_order: int

    @property
    def path_parts(self) -> list[str]:
        return [part.strip() for part in self.calendar_name.split("/") if part.strip()]

    @property
    def display_name(self) -> str:
        parts = self.path_parts
        return parts[-1] if parts else self.calendar_name

    @property
    def group_path(self) -> str:
        return "/".join(self.path_parts[:-1])


@dataclass(frozen=True)
class GroupLogo:
    category: str
    group_path: str
    logo_bytes: bytes | None
    group_order: int


def _decode_logo(raw_value: str, row_number: int, column_name: str) -> bytes | None:
    value = (raw_value or "").strip()
    if not value:
        return None
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:  # noqa: BLE001 - validation message should include row context.
        raise ValueError(f"Invalid base64 in {column_name} at row {row_number}") from exc


def load_mapping(path: str | Path) -> list[CalendarEntry]:
    mapping_path = Path(path)
    with mapping_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Mapping file is missing required columns: {', '.join(missing)}")

        entries: list[CalendarEntry] = []
        seen_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            values = {column: (row.get(column) or "").strip() for column in REQUIRED_COLUMNS}
            missing_values = [
                column
                for column in REQUIRED_COLUMNS
                if column not in {"API-Key-Provider", "LogoBytes"} and not values[column]
            ]
            if missing_values:
                raise ValueError(f"Row {row_number} is missing values: {', '.join(missing_values)}")
            if values["ICSId"] in seen_ids:
                raise ValueError(f"Duplicate ICSId '{values['ICSId']}' at row {row_number}")
            seen_ids.add(values["ICSId"])

            path_parts = [part.strip() for part in values["Kalendername"].split("/") if part.strip()]
            if not path_parts:
                raise ValueError(f"Row {row_number} has an empty Kalendername path")
            try:
                subgroup_order = int(values["SubGroupOrder"])
            except ValueError as exc:
                raise ValueError(f"Row {row_number} has invalid SubGroupOrder") from exc

            entries.append(
                CalendarEntry(
                    calendar_name=values["Kalendername"],
                    country=values["Land"],
                    category=values["Kategorie"],
                    competition=values["Wettbewerb"],
                    api_provider=values["API-Provider"],
                    api_key_provider=values["API-Key-Provider"],
                    ics_id=values["ICSId"],
                    logo_bytes=_decode_logo(values["LogoBytes"], row_number, "LogoBytes"),
                    subgroup_order=subgroup_order,
                )
            )
    return entries


def load_group_logos(path: str | Path) -> dict[tuple[str, str], GroupLogo]:
    logo_path = Path(path)
    if not logo_path.exists():
        return {}
    with logo_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        group_order_column = "groupOrder" if "groupOrder" in fieldnames else "GroupOrder"
        required = {"Kategorie", "GroupPath", "LogoBytes", group_order_column}
        missing = sorted(required.difference(fieldnames))
        if missing:
            raise ValueError(f"Group logo settings file is missing columns: {', '.join(missing)}")
        logos: dict[tuple[str, str], GroupLogo] = {}
        for row_number, row in enumerate(reader, start=2):
            category = (row.get("Kategorie") or "").strip()
            group_path = (row.get("GroupPath") or "").strip()
            if not category or not group_path:
                raise ValueError(f"Group logo row {row_number} needs Kategorie and GroupPath")
            try:
                group_order = int((row.get(group_order_column) or "").strip())
            except ValueError as exc:
                raise ValueError(f"Group logo row {row_number} has invalid groupOrder") from exc
            logos[(category, group_path)] = GroupLogo(
                category=category,
                group_path=group_path,
                logo_bytes=_decode_logo(row.get("LogoBytes") or "", row_number, "LogoBytes"),
                group_order=group_order,
            )
    return logos
