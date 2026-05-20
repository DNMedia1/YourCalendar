# YourCalendar KSC POC

This is a first command-line proof of concept for the YourCalendar idea.

It fetches upcoming Karlsruher SC events, normalizes them, and writes an
iCalendar (`.ics`) file. That file can be imported into Apple Calendar, Google
Calendar, and Outlook. If the file is later hosted at a stable HTTPS URL, those
calendar apps can subscribe to it and receive updates automatically.

## Why ICS first?

Directly writing to Google Calendar and Outlook requires OAuth apps, user
consent, token storage, permissions, and provider review. Apple Calendar has no
equivalent cloud API for all Apple users; on macOS, a local `.ics` file can be
opened/imported.

ICS is the simplest common denominator for a POC because all three target
calendar ecosystems can consume it.

## Run

```bash
python3 yourcalendar_poc.py --show-events
```

Output:

```text
output/ksc.ics
```

Optional on macOS:

```bash
python3 yourcalendar_poc.py --publish apple
```

That opens the generated file in Apple Calendar.

To test calendar publishing without relying on live source availability:

```bash
python3 yourcalendar_poc.py --sample-events --show-events
```

Sample events are clearly prefixed with `[SAMPLE]` and must not be treated as
real fixtures.

## Web UI

Start the local web app:

```bash
python3 web_app.py
```

Open:

```text
http://127.0.0.1:8765
```

The UI supports:

- Bundesliga, 2. Bundesliga, 3. Liga and DFB-Pokal via OpenLigaDB.
- Switching between live data and sample data.
- Filtering by club name.
- Local browser favorites for clubs.
- Stable `.ics` feed URLs for the current filters.
- Copying a calendar subscription link for Apple Calendar, Google Calendar and
  Outlook.
- Opening the current filtered feed in Apple Calendar on macOS.

The local feed endpoint is generated from the current filters:

```text
http://127.0.0.1:8765/feeds/current.ics?sample=true&leagues=bl1%2Cbl2%2Cbl3&includePast=true
```

Published feed examples:

```text
http://127.0.0.1:8765/feeds/football-germany.ics
http://127.0.0.1:8765/feeds/sample-ksc.ics
```

In production, set `YOURCALENDAR_PUBLIC_BASE_URL` to the deployed HTTPS origin
so the UI exposes subscription URLs such as:

```bash
YOURCALENDAR_PUBLIC_BASE_URL=https://calendar.example.com python3 web_app.py
```

Sample feeds are rendered with `[SAMPLE]` event summaries and the `sample`
category so they cannot be confused with real fixtures.

Important: OpenLigaDB is useful for this POC, but it is not the same as a
commercial real-time provider with guaranteed update latency and SLA.

## Source

The current POC uses TheSportsDB:

```bash
python3 yourcalendar_poc.py \
  --source thesportsdb \
  --thesportsdb-team-id 135293 \
  --show-events
```

By default it uses the public demo key `123`. You can set your own key:

```bash
THESPORTSDB_API_KEY=your_key python3 yourcalendar_poc.py --show-events
```

## Known POC Problems

- On 2026-05-18, TheSportsDB returned zero upcoming KSC events for team ID
  `135293`. This may be correct because the 2025/26 season just ended, or it
  may be a data coverage/free-key limitation. We do not have enough certainty
  yet to decide which.
- TheSportsDB free/demo access may return only a limited number of events.
- TheSportsDB documentation notes limitations for free team schedule calls, so
  away games or a full fixture list may be missing.
- TheSportsDB text search did not reliably resolve `Karlsruher SC` during the
  first test run, so the POC defaults to the known team ID `135293`.
- Kickoff times must be verified before production use. The POC stores a time
  quality note in each event description.
- Google and Outlook direct publishing are intentionally not implemented yet.
  They should be separate OAuth spikes after we confirm that source quality and
  calendar feed generation are worth continuing.
- A local `.ics` import is static. Automatic updates require hosting the file
  and subscribing to its HTTPS URL.

## Event Model

The POC now normalizes source data into a dedicated internal `CalendarEvent`
model before rendering ICS. The model covers timezone-aware start/end times,
all-day events, source quality, category, status, external IDs, locations,
source URLs, and data-quality notes.

See `docs/event-model.md` for the current schema and validation rules.

## Next Technical Spikes

1. Validate whether TheSportsDB is good enough for KSC.
2. Compare it with football-data.org or a paid sports-data provider.
3. Host `output/ksc.ics` locally or on a preview URL and test subscription
   refresh behavior in Google, Outlook, and Apple Calendar.
4. Add an event database so deleted/postponed/rescheduled matches can be tracked
   instead of blindly regenerating a feed.
5. Add Google Calendar OAuth only after the ICS feed proves useful.
# YourCalendar
