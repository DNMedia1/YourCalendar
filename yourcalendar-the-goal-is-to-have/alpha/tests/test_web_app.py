from __future__ import annotations

import unittest

from yourcalendar_alpha.mapping import CalendarEntry
from yourcalendar_alpha.web_app import build_tree, calendar_public_url, render_category


class WebAppTests(unittest.TestCase):
    def test_build_tree_groups_by_category_and_path(self) -> None:
        entry = CalendarEntry(
            calendar_name="Fussball/Deutschland/Bundesliga/Test Team",
            country="Deutschland",
            category="Sport",
            competition="Bundesliga",
            api_provider="TheSportsDB",
            api_key_provider="",
            ics_id="42",
            logo_bytes=None,
        )

        tree = build_tree([entry])

        self.assertIn("Sport", tree)
        self.assertIn("Fussball", tree["Sport"].children)
        bundesliga = tree["Sport"].children["Fussball"].children["Deutschland"].children["Bundesliga"]
        self.assertEqual(bundesliga.entries[0].display_name, "Test Team")

    def test_calendar_public_url_uses_ics_route(self) -> None:
        settings = {"public_base_url": "https://calendar.example"}

        self.assertEqual(calendar_public_url(settings, "team 42"), "https://calendar.example/ics/team_42.ics")

    def test_render_category_uses_flat_tile_grid_markup(self) -> None:
        entry = CalendarEntry(
            calendar_name="Fussball/Deutschland/Bundesliga/Test Team",
            country="Deutschland",
            category="Sport",
            competition="Bundesliga",
            api_provider="TheSportsDB",
            api_key_provider="",
            ics_id="42",
            logo_bytes=None,
        )
        tree = build_tree([entry])

        markup = render_category("Sport", tree["Sport"], {"public_base_url": "https://calendar.example"}, {})

        self.assertIn('class="tile-grid"', markup)
        self.assertNotIn('class="grid"', markup)
        self.assertNotIn("\u00c2", markup)
        self.assertIn("<details", markup)
        self.assertIn("Deutschland / Bundesliga", markup)
        self.assertIn("Test Team", markup)


if __name__ == "__main__":
    unittest.main()
