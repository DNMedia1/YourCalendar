# YourCalendar POC

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

The deliberate scope decision to stay ICS-first for the MVP, and to defer direct
Google/Outlook OAuth integrations to later spikes, is documented in
`docs/calendar-integration-scope.md` (refs #14).

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
http://127.0.0.1:8765/feeds/holidays-germany.ics
http://127.0.0.1:8765/feeds/sample-ksc.ics
```

Published feeds can be refreshed by a repeatable import job:

```bash
python3 import_jobs.py
```

The job writes cached feed files to `output/feeds/` and appends run metadata to
`output/import-runs.json`. If a source import fails, the previous cached feed
file stays in place so existing subscription URLs can keep serving the last
successful calendar.

Each successful import also stores the latest event snapshot in
`output/event-snapshots/` and writes a change report to `output/event-changes/`.
The comparison is keyed by stable event `UID` and tracks changed start times,
locations, summaries and calendar status values.

The first scheduler architecture is documented in
`docs/hosting-scheduler-architecture.md`. The matching GitHub Actions workflow
can be started manually and also runs on a six-hour schedule. It uploads feed,
run-log, snapshot and change-report artifacts without committing generated
runtime files back into Git.

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

The sports POC can use TheSportsDB:

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

The first safer MVP source spike uses public holidays via Nager.Date:

```bash
python3 yourcalendar_poc.py \
  --source nager-holidays \
  --holiday-year 2026 \
  --holiday-country DE \
  --max-events 10 \
  --calendar-name "German Public Holidays" \
  --show-events
```

See `docs/source-evaluation-holidays.md` for the source decision, risks and
next steps. Nager.Date is useful for the PoC, but it is not treated as an
official government source or final production provider.

The football provider comparison for football-data.org, TheSportsDB,
API-FOOTBALL/API-SPORTS, Sportmonks and OpenLigaDB is documented in
`docs/source-evaluation-football.md`. Current recommendation: keep OpenLigaDB
as POC/Fallback, use football-data.org for a small top-league MVP spike, and
evaluate API-FOOTBALL or Sportmonks only when broader paid football coverage is
really needed.

## Community Sports Source Registry

The app exposes a local research registry for broader sports data candidates:

```text
GET /api/source-candidates
GET /api/source-candidates?sport=mma
GET /api/source-candidates?includeRisky=false
```

The registry is intentionally separate from active imports. It lists GitHub
repos, public APIs and datasets with risk labels, so experimental sources such
as UFC/MMA scrapers are visible without becoming production dependencies.

See `docs/source-evaluation-community-sports.md` for the current candidate
matrix and next integration steps.

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

## Performance and Accessibility

The current frontend quality baseline is documented in
`docs/performance-accessibility-baseline.md`. It covers asset-size budgets,
basic `axe-core` checks, accessible loading/empty states and the manual
browser checks expected before larger UI merges.

## Agent Collaboration

Codex, Claude Code and other agents share the repo-owned workflow in
`AGENTS.md`, `CLAUDE.md`, `docs/agent-collaboration.md` and
`docs/agent-status.md`. GitHub Issues and the GitHub Project Board remain the
planning source of truth. If no task is specified, agents must run the documented
session intake, select the next open GitHub issue by priority, claim it, and
write back handoff knowledge before stopping. Local knowledge-base snapshots
under `.claude/` or `.snapshots/.claude/knowledge_base/` stay private and must
not be committed.

## Next Technical Spikes

1. Build a small football-data.org spike behind source configuration and
   import monitoring.
2. Validate whether API-FOOTBALL or Sportmonks is worth a paid trial for broad
   coverage.
3. Host `output/ksc.ics` locally or on a preview URL and test subscription
   refresh behavior in Google, Outlook, and Apple Calendar.
4. Add an event database so deleted/postponed/rescheduled matches can be tracked
   instead of blindly regenerating a feed.
5. Add Google Calendar OAuth only after the ICS feed proves useful.
# YourCalendar
