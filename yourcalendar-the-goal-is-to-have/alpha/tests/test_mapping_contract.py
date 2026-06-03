from __future__ import annotations

import csv
import json
import os
import time
import unittest
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data" / "mapping.csv"
LOCK = ROOT / "data" / "mapping.provider-lock.csv"
FOOTBALL_SOURCE = ROOT / "data" / "football_team_source.csv"
NFL_SOURCE = ROOT / "data" / "nfl_team_source.csv"
NBA_SOURCE = ROOT / "data" / "nba_team_source.csv"
FORMULA1_SOURCE = ROOT / "data" / "formula1_event_source.csv"
GROUP_LOGOS = ROOT / "data" / "group_logo_settings.csv"

EXPECTED_COUNTS = {
    ("Deutschland", "1. Bundesliga"): 18,
    ("Deutschland", "2. Bundesliga"): 18,
    ("Deutschland", "3. Bundesliga"): 20,
    ("Spanien", "La Liga"): 20,
    ("Spanien", "La Liga 2"): 22,
    ("England", "Premier League"): 20,
    ("England", "Championship"): 24,
    ("Frankreich", "Ligue 1"): 18,
    ("Frankreich", "Ligue 2"): 18,
    ("Italien", "Serie A"): 20,
    ("Italien", "Serie B"): 20,
    ("United States", "Football/NFL"): 32,
    ("United States", "Basketball/NBA"): 30,
    ("Global", "Motorsport/Formel 1"): 1,
}

KNOWN_PROVIDER_IDS = {
    "FC St. Pauli": "133813",
    "VfL Wolfsburg": "133655",
    "MSV Duisburg": "133877",
    "Rot-Weiss Essen": "138400",
    "Sporting Gij\u00f3n": "133723",
    "Zaragoza": "133737",
    "Paris Saint-Germain": "133714",
    "Saint-\u00c9tienne": "133717",
    "Inter Milan": "133681",
    "Arizona Cardinals": "134946",
    "Kansas City Chiefs": "134931",
    "Tennessee Titans": "134929",
    "Washington Commanders": "134937",
    "Boston Celtics": "134860",
    "Golden State Warriors": "134865",
    "Los Angeles Lakers": "134867",
    "Washington Wizards": "134884",
}

WOMENS_MARKERS = ("women", "femenino", "female", "frauen")


class MappingContractTests(unittest.TestCase):
    def test_mapping_contains_expected_leagues_and_static_provider_config(self) -> None:
        rows = load_csv(MAPPING)
        self.assertEqual(len(rows), sum(EXPECTED_COUNTS.values()))

        actual_counts: dict[tuple[str, str], int] = {}
        for row in rows:
            key = (row["Land"], row["Wettbewerb"])
            actual_counts[key] = actual_counts.get(key, 0) + 1
            self.assertEqual(row["Kategorie"], "Sport")
            self.assertIn(row["API-Provider"], {"TheSportsDB", "OpenF1"})
            if row["API-Provider"] == "TheSportsDB":
                self.assertEqual(row["API-Key-Provider"], "THESPORTSDB_API_KEY")
                self.assertTrue(row["ICSId"].isdigit(), row["Kalendername"])
            if row["API-Provider"] == "OpenF1":
                self.assertEqual(row["API-Key-Provider"], "")
                self.assertEqual(row["ICSId"], "formula-1")
            self.assertTrue(row["SubGroupOrder"].isdigit(), row["Kalendername"])
            self.assertNotIn("/Women/", row["Kalendername"])

        self.assertEqual(actual_counts, EXPECTED_COUNTS)
        self.assertEqual(len({row["ICSId"] for row in rows}), len(rows))
        for group, count in EXPECTED_COUNTS.items():
            orders = sorted(
                int(row["SubGroupOrder"])
                for row in rows
                if (row["Land"], row["Wettbewerb"]) == group
            )
            self.assertEqual(orders, list(range(1, count + 1)), group)

    def test_known_problem_ids_are_locked(self) -> None:
        rows = {row["Kalendername"].split("/")[-1]: row for row in load_csv(MAPPING)}
        for team, expected_id in KNOWN_PROVIDER_IDS.items():
            self.assertIn(team, rows)
            self.assertEqual(rows[team]["ICSId"], expected_id)

    def test_provider_lock_matches_mapping(self) -> None:
        mapping_rows = [
            {
                "Team": row["Kalendername"].split("/")[-1],
                "ICSId": row["ICSId"],
                "Provider": row["API-Provider"],
            }
            for row in load_csv(MAPPING)
        ]
        self.assertEqual(load_csv(LOCK), mapping_rows)

    def test_source_contains_all_expected_teams_and_orders(self) -> None:
        source_rows = (
            load_csv(FOOTBALL_SOURCE)
            + load_csv(NFL_SOURCE)
            + load_csv(NBA_SOURCE)
            + load_csv(FORMULA1_SOURCE)
        )
        self.assertEqual(len(source_rows), sum(EXPECTED_COUNTS.values()))
        for group, count in EXPECTED_COUNTS.items():
            orders = sorted(
                int(row["SubGroupOrder"])
                for row in source_rows
                if (row["Land"], row["Wettbewerb"]) == group
            )
            self.assertEqual(orders, list(range(1, count + 1)), group)

    def test_group_logo_settings_cover_mapping_groups_and_define_order(self) -> None:
        mapping_rows = load_csv(MAPPING)
        group_logo_rows = load_csv(GROUP_LOGOS)
        configured_groups = {(row["Kategorie"], row["GroupPath"]) for row in group_logo_rows}
        expected_groups: set[tuple[str, str]] = set()

        for row in mapping_rows:
            path_parts = [part for part in row["Kalendername"].split("/") if part]
            for index in range(1, len(path_parts)):
                expected_groups.add((row["Kategorie"], "/".join(path_parts[:index])))

        self.assertEqual(configured_groups, expected_groups)
        for row in group_logo_rows:
            self.assertTrue(row["groupOrder"].isdigit(), row["GroupPath"])
        self.assertEqual(group_order(group_logo_rows, "Sport", "Fussball"), 1)
        self.assertEqual(group_order(group_logo_rows, "Sport", "Football"), 2)
        self.assertEqual(group_order(group_logo_rows, "Sport", "Basketball"), 3)
        self.assertEqual(group_order(group_logo_rows, "Sport", "Motorsport"), 4)

    def test_formula1_mapping_uses_openf1_provider(self) -> None:
        rows = load_csv(MAPPING)
        formula1_rows = [row for row in rows if row["Kalendername"] == "Motorsport/Formel 1/Veranstaltungen"]

        self.assertEqual(len(formula1_rows), 1)
        self.assertEqual(formula1_rows[0]["Kategorie"], "Sport")
        self.assertEqual(formula1_rows[0]["Wettbewerb"], "Motorsport/Formel 1")
        self.assertEqual(formula1_rows[0]["API-Provider"], "OpenF1")
        self.assertEqual(formula1_rows[0]["ICSId"], "formula-1")


@unittest.skipUnless(os.environ.get("RUN_LIVE_PROVIDER_TESTS") == "1", "set RUN_LIVE_PROVIDER_TESTS=1")
class LiveProviderMappingTests(unittest.TestCase):
    def test_all_mapping_ids_exist_and_do_not_resolve_to_womens_entries(self) -> None:
        for row in load_csv(MAPPING):
            if row["API-Provider"] != "TheSportsDB":
                continue
            payload = fetch_team(row["ICSId"])
            self.assertIsNotNone(payload, row["Kalendername"])
            haystack = " ".join(
                str(payload.get(field) or "") for field in ["strTeam", "strAlternate", "strLeague"]
            ).lower()
            self.assertFalse(any(marker in haystack for marker in WOMENS_MARKERS), row["Kalendername"])
            time.sleep(2.1)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def group_order(rows: list[dict[str, str]], category: str, group_path: str) -> int:
    for row in rows:
        if row["Kategorie"] == category and row["GroupPath"] == group_path:
            return int(row["groupOrder"])
    raise AssertionError(f"Missing group logo row for {category}/{group_path}")


def fetch_team(team_id: str) -> dict[str, str] | None:
    url = f"https://www.thesportsdb.com/api/v1/json/123/lookupteam.php?{urlencode({'id': team_id})}"
    with urlopen(url, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    teams = payload.get("teams") or []
    return teams[0] if teams else None


if __name__ == "__main__":
    unittest.main()
