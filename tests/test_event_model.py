from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from yourcalendar_model import CalendarEvent, EventCategory, EventStatus, SourceQuality
from yourcalendar_poc import render_ics


class CalendarEventModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tz = ZoneInfo("Europe/Berlin")
        self.starts_at = datetime(2026, 6, 1, 10, 0, tzinfo=self.tz)
        self.ends_at = self.starts_at + timedelta(hours=2)

    def test_normalizes_enum_fields(self) -> None:
        event = CalendarEvent(
            uid="event-1@example.test",
            title="Example event",
            starts_at=self.starts_at,
            ends_at=self.ends_at,
            source="Manual",
            category="sports",
            status="CONFIRMED",
            source_quality="manual",
        )

        self.assertEqual(event.category, EventCategory.SPORTS)
        self.assertEqual(event.status, EventStatus.CONFIRMED)
        self.assertEqual(event.source_quality, SourceQuality.MANUAL)

    def test_rejects_naive_datetimes(self) -> None:
        with self.assertRaisesRegex(ValueError, "starts_at must be timezone-aware"):
            CalendarEvent(
                uid="event-1@example.test",
                title="Example event",
                starts_at=datetime(2026, 6, 1, 10, 0),
                ends_at=self.ends_at,
                source="Manual",
            )

    def test_rejects_non_positive_duration(self) -> None:
        with self.assertRaisesRegex(ValueError, "ends_at must be after starts_at"):
            CalendarEvent(
                uid="event-1@example.test",
                title="Example event",
                starts_at=self.starts_at,
                ends_at=self.starts_at,
                source="Manual",
            )

    def test_rejects_all_day_events_without_midnight_boundaries(self) -> None:
        with self.assertRaisesRegex(ValueError, "all_day events must use local midnight boundaries"):
            CalendarEvent(
                uid="event-1@example.test",
                title="Example event",
                starts_at=self.starts_at,
                ends_at=self.ends_at,
                source="Manual",
                all_day=True,
            )

    def test_maps_postponed_status_to_ics_tentative(self) -> None:
        event = CalendarEvent(
            uid="event-1@example.test",
            title="Example event",
            starts_at=self.starts_at,
            ends_at=self.ends_at,
            source="Manual",
            status=EventStatus.POSTPONED,
        )

        self.assertEqual(event.ics_status, "TENTATIVE")

    def test_renders_all_day_events_as_date_values(self) -> None:
        event = CalendarEvent(
            uid="holiday-1@example.test",
            title="Example holiday",
            starts_at=datetime(2026, 6, 1, 0, 0, tzinfo=self.tz),
            ends_at=datetime(2026, 6, 2, 0, 0, tzinfo=self.tz),
            source="Manual",
            category=EventCategory.HOLIDAYS,
            source_quality=SourceQuality.MANUAL,
            all_day=True,
        )

        ics = render_ics([event], "Example Calendar")

        self.assertIn("DTSTART;VALUE=DATE:20260601", ics)
        self.assertIn("DTEND;VALUE=DATE:20260602", ics)
        self.assertIn("CATEGORIES:holidays", ics)

    def test_renders_quality_notes_in_description(self) -> None:
        event = CalendarEvent(
            uid="event-1@example.test",
            title="Example event",
            starts_at=self.starts_at,
            ends_at=self.ends_at,
            source="Manual",
            description="Base description.",
            quality_notes=("Kickoff time is unverified.",),
        )

        ics = render_ics([event], "Example Calendar")

        self.assertIn("Base description.\\nQuality notes: Kickoff time is unverified.", ics)


if __name__ == "__main__":
    unittest.main()
