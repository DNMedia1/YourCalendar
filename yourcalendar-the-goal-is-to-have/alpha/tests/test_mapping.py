from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from yourcalendar_alpha.mapping import load_group_logos, load_mapping


class MappingTests(unittest.TestCase):
    def test_loads_required_mapping_and_splits_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mapping.csv"
            path.write_text(
                "Kalendername,Land,Kategorie,Wettbewerb,API-Provider,API-Key-Provider,ICSId,LogoBytes,SubGroupOrder\n"
                "Fussball/Deutschland/1. Bundesliga/Test Team,Deutschland,Sport,1. Bundesliga,TheSportsDB,,123,,1\n",
                encoding="utf-8",
            )

            entries = load_mapping(path)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].display_name, "Test Team")
        self.assertEqual(entries[0].group_path, "Fussball/Deutschland/1. Bundesliga")
        self.assertEqual(entries[0].subgroup_order, 1)

    def test_rejects_missing_required_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mapping.csv"
            path.write_text("Kalendername,Land\nName,Deutschland\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required columns"):
                load_mapping(path)

    def test_rejects_duplicate_ics_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mapping.csv"
            path.write_text(
                "Kalendername,Land,Kategorie,Wettbewerb,API-Provider,API-Key-Provider,ICSId,LogoBytes,SubGroupOrder\n"
                "A,DE,Sport,1. Bundesliga,TheSportsDB,,1,,1\n"
                "B,DE,Sport,1. Bundesliga,TheSportsDB,,1,,2\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Duplicate ICSId"):
                load_mapping(path)

    def test_loads_group_logos_with_group_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "group_logo_settings.csv"
            path.write_text(
                "Kategorie,GroupPath,LogoBytes,groupOrder\n"
                "Sport,Fussball/Deutschland,,2\n",
                encoding="utf-8",
            )

            logos = load_group_logos(path)

        logo = logos[("Sport", "Fussball/Deutschland")]
        self.assertEqual(logo.group_order, 2)

    def test_loads_group_logos_with_legacy_group_order_casing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "group_logo_settings.csv"
            path.write_text(
                "Kategorie,GroupPath,LogoBytes,GroupOrder\n"
                "Sport,Fussball/Deutschland,,3\n",
                encoding="utf-8",
            )

            logos = load_group_logos(path)

        logo = logos[("Sport", "Fussball/Deutschland")]
        self.assertEqual(logo.group_order, 3)

    def test_rejects_invalid_group_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "group_logo_settings.csv"
            path.write_text(
                "Kategorie,GroupPath,LogoBytes,groupOrder\n"
                "Sport,Fussball/Deutschland,,abc\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "invalid groupOrder"):
                load_group_logos(path)


if __name__ == "__main__":
    unittest.main()
