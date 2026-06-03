from __future__ import annotations

import unittest
from pathlib import Path

from yourcalendar_alpha.calendar.subscription_links import build_calendar_public_url
from yourcalendar_alpha.calendar.tree_builder import build_calendar_tree
from yourcalendar_alpha.domain.calendar_entry import CalendarEntry
from yourcalendar_alpha.domain.group_logo import GroupLogo
from yourcalendar_alpha.web.page_renderer import render_category_section, render_footer, render_static_page


STATIC_DIR = Path(__file__).resolve().parents[1] / "yourcalendar_alpha" / "web" / "static"


class WebAppTests(unittest.TestCase):
    def test_build_tree_groups_by_category_and_path(self) -> None:
        entry = make_entry("Test Team", 1)

        tree = build_calendar_tree([entry])

        self.assertIn("Sport", tree)
        self.assertIn("Fussball", tree["Sport"].children)
        bundesliga = tree["Sport"].children["Fussball"].children["Deutschland"].children["1. Bundesliga"]
        self.assertEqual(bundesliga.entries[0].display_name, "Test Team")

    def test_calendar_public_url_uses_ics_route(self) -> None:
        settings = {"public_base_url": "https://calendar.example"}

        self.assertEqual(build_calendar_public_url(settings, "team 42"), "https://calendar.example/ics/team_42.ics")

    def test_render_category_uses_flat_tile_grid_markup(self) -> None:
        tree = build_calendar_tree([make_entry("Test Team", 1)])

        markup = render_category_section("Sport", tree["Sport"], {"public_base_url": "https://calendar.example"}, {})

        self.assertIn('class="tile-grid"', markup)
        self.assertNotIn('class="grid"', markup)
        self.assertNotIn("\u00c2", markup)
        self.assertIn("<details", markup)
        self.assertIn("Deutschland / 1. Bundesliga", markup)
        self.assertIn("Test Team", markup)

    def test_static_assets_contain_active_tree_behavior(self) -> None:
        tree = build_calendar_tree([make_entry("Test Team", 1)])
        markup = render_category_section("Sport", tree["Sport"], {"public_base_url": "https://calendar.example"}, {})
        css = (STATIC_DIR / "site.css").read_text(encoding="utf-8")
        js = (STATIC_DIR / "site.js").read_text(encoding="utf-8")

        self.assertIn('class="group-panel"', markup)
        self.assertIn(".tile-grid.has-open", css)
        self.assertIn("closeGroupTree(sibling)", js)
        self.assertIn("closeDescendantGroups(panel)", js)
        self.assertIn("child.open = false", js)
        self.assertIn("grid.classList.add('has-open')", js)
        self.assertIn(".brand-block", css)
        self.assertIn(".brand-mark", css)
        self.assertIn('[data-theme="dark"]', css)
        self.assertIn(".theme-toggle", css)
        self.assertIn(".site-footer", css)
        self.assertIn("data-theme-toggle", js)
        self.assertIn("localStorage.setItem('yc-theme'", js)
        self.assertIn("aria-pressed", js)

    def test_footer_exposes_only_impressum_link(self) -> None:
        markup = render_footer()

        self.assertIn('href="/impressum"', markup)
        self.assertIn("Impressum", markup)
        self.assertNotIn("Partnerships", markup)
        self.assertNotIn("Create Your Own Calendar", markup)

    def test_static_pages_exist_even_when_not_linked_in_footer(self) -> None:
        settings = {"site_title": "Test Calendar"}

        impressum = render_static_page("/impressum", settings)
        partnerships = render_static_page("/partnerships", settings)
        create_calendar = render_static_page("/create-your-own-calendar", settings)

        self.assertIsNotNone(impressum)
        self.assertIsNotNone(partnerships)
        self.assertIsNotNone(create_calendar)
        self.assertIn("Impressum", impressum or "")
        self.assertIn("Partnerships", partnerships or "")
        self.assertIn("Create Your Own Calendar", create_calendar or "")

    def test_calendar_tiles_are_sorted_by_subgroup_order(self) -> None:
        first = make_entry("First Team", 1, "1")
        second = make_entry("Second Team", 2, "2")
        tree = build_calendar_tree([second, first])

        markup = render_category_section("Sport", tree["Sport"], {"public_base_url": "https://calendar.example"}, {})

        self.assertLess(markup.index("First Team"), markup.index("Second Team"))

    def test_group_tiles_are_sorted_by_group_logo_order(self) -> None:
        spain = make_custom_entry("Fussball/Spanien/La Liga/Test Spanien", "Spanien", "La Liga", "1")
        england = make_custom_entry("Fussball/England/Premier League/Test England", "England", "Premier League", "2")
        tree = build_calendar_tree([spain, england])
        group_logos = {
            ("Sport", "Fussball/Spanien"): GroupLogo("Sport", "Fussball/Spanien", None, 2),
            ("Sport", "Fussball/England"): GroupLogo("Sport", "Fussball/England", None, 1),
        }

        markup = render_category_section(
            "Sport",
            tree["Sport"],
            {"public_base_url": "https://calendar.example"},
            group_logos,
        )

        self.assertLess(markup.index("Fussball / England"), markup.index("Fussball / Spanien"))


def make_entry(team_name: str, subgroup_order: int, ics_id: str = "42") -> CalendarEntry:
    return make_custom_entry(
        calendar_name=f"Fussball/Deutschland/1. Bundesliga/{team_name}",
        country="Deutschland",
        competition="1. Bundesliga",
        ics_id=ics_id,
        subgroup_order=subgroup_order,
    )


def make_custom_entry(
    calendar_name: str,
    country: str,
    competition: str,
    ics_id: str,
    subgroup_order: int = 1,
) -> CalendarEntry:
    return CalendarEntry(
        calendar_name=calendar_name,
        country=country,
        category="Sport",
        competition=competition,
        api_provider="TheSportsDB",
        api_key_provider="",
        ics_id=ics_id,
        logo_bytes=None,
        subgroup_order=subgroup_order,
    )


if __name__ == "__main__":
    unittest.main()
