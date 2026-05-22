from __future__ import annotations

import unittest

from yourcalendar_model import EventCategory, SourceQuality
from yourcalendar_poc import (
    fetch_nager_holiday_events,
    holiday_applies_to_subdivision,
    nager_holiday_to_event,
)


HOLIDAY = {
    "date": "2026-01-01",
    "localName": "Neujahr",
    "name": "New Year's Day",
    "countryCode": "DE",
    "global": True,
    "counties": None,
    "types": ["Public"],
}


class HolidaySourceTests(unittest.TestCase):
    def test_nager_holiday_maps_to_all_day_calendar_event(self) -> None:
        event = nager_holiday_to_event(HOLIDAY, 2026, "DE", "", "Europe/Berlin")

        self.assertEqual(event.uid, "nager-de-2026-01-01-neujahr@yourcalendar.local")
        self.assertEqual(event.title, "Neujahr")
        self.assertEqual(event.category, EventCategory.HOLIDAYS)
        self.assertEqual(event.source_quality, SourceQuality.COMMUNITY)
        self.assertTrue(event.all_day)
        self.assertEqual(event.starts_at.isoformat(), "2026-01-01T00:00:00+01:00")
        self.assertEqual(event.ends_at.isoformat(), "2026-01-02T00:00:00+01:00")
        self.assertIn("not an official government source", " ".join(event.quality_notes))

    def test_subdivision_filter_keeps_global_and_matching_regional_holidays(self) -> None:
        regional = {
            **HOLIDAY,
            "global": False,
            "counties": ["DE-BW", "DE-BY"],
        }

        self.assertTrue(holiday_applies_to_subdivision(HOLIDAY, "DE-BW"))
        self.assertTrue(holiday_applies_to_subdivision(regional, "DE-BW"))
        self.assertFalse(holiday_applies_to_subdivision(regional, "DE-BE"))

    def test_fetch_nager_holiday_events_applies_limit_with_injected_fetcher(self) -> None:
        events = fetch_nager_holiday_events(
            2026,
            country_code="DE",
            max_events=1,
            tz_name="Europe/Berlin",
            raw_holidays=[
                HOLIDAY,
                {
                    **HOLIDAY,
                    "date": "2026-04-03",
                    "localName": "Karfreitag",
                    "name": "Good Friday",
                },
            ],
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].title, "Neujahr")


if __name__ == "__main__":
    unittest.main()
