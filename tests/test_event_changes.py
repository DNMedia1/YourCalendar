from __future__ import annotations

import unittest

from event_changes import compare_snapshots, snapshot_from_ics, summarize_changes


def ics_event(uid: str, summary: str, starts_at: str, location: str = "", status: str = "CONFIRMED") -> str:
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTART:{starts_at}",
        f"SUMMARY:{summary}",
        f"STATUS:{status}",
    ]
    if location:
        lines.append(f"LOCATION:{location}")
    lines.append("END:VEVENT")
    return "\r\n".join(lines)


class EventChangeTests(unittest.TestCase):
    def test_snapshot_from_ics_extracts_stable_event_fields(self) -> None:
        snapshot = snapshot_from_ics(
            "\r\n".join(
                [
                    "BEGIN:VCALENDAR",
                    ics_event("event-1", "Team A vs Team B", "20260521T180000Z", "Arena"),
                    "END:VCALENDAR",
                    "",
                ]
            )
        )

        self.assertEqual(snapshot["event-1"]["uid"], "event-1")
        self.assertEqual(snapshot["event-1"]["summary"], "Team A vs Team B")
        self.assertEqual(snapshot["event-1"]["startsAt"], "20260521T180000Z")
        self.assertEqual(snapshot["event-1"]["location"], "Arena")
        self.assertEqual(snapshot["event-1"]["status"], "CONFIRMED")

    def test_compare_snapshots_detects_new_changed_and_missing_events(self) -> None:
        previous = {
            "changed": {
                "uid": "changed",
                "summary": "Old",
                "startsAt": "20260521T180000Z",
                "location": "Arena",
                "status": "CONFIRMED",
            },
            "missing": {
                "uid": "missing",
                "summary": "Removed",
                "startsAt": "20260522T180000Z",
                "location": "",
                "status": "CONFIRMED",
            },
        }
        current = {
            "changed": {
                "uid": "changed",
                "summary": "Old",
                "startsAt": "20260521T200000Z",
                "location": "New Arena",
                "status": "POSTPONED",
            },
            "new": {
                "uid": "new",
                "summary": "New",
                "startsAt": "20260523T180000Z",
                "location": "",
                "status": "CONFIRMED",
            },
        }

        changes = compare_snapshots(previous, current)
        by_type = {change["type"]: change for change in changes}

        self.assertEqual(summarize_changes(changes), {"total": 3, "new": 1, "changed": 1, "missing": 1})
        self.assertEqual(by_type["changed"]["fields"]["startsAt"]["before"], "20260521T180000Z")
        self.assertEqual(by_type["changed"]["fields"]["startsAt"]["after"], "20260521T200000Z")
        self.assertEqual(by_type["changed"]["fields"]["location"]["after"], "New Arena")
        self.assertEqual(by_type["changed"]["fields"]["status"]["after"], "POSTPONED")


if __name__ == "__main__":
    unittest.main()
