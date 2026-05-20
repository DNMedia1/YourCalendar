# YourCalendar KSC POC Findings

Stand: 2026-05-18

## What Works

- A dependency-free CLI can generate a valid `.ics` calendar file.
- The generated file can be imported by Apple Calendar, Google Calendar, and
  Outlook.
- The same `.ics` file can become an automatically updating subscription once
  it is hosted at a stable HTTPS URL.

## What The First Real Test Showed

The first TheSportsDB test with a text search for `Karlsruher SC` resolved to an
unrelated result. The CLI now defaults to the known TheSportsDB team ID `135293`
instead of trusting fuzzy text search.

The corrected source call returned zero upcoming events on 2026-05-18. That is
plausible because the 2025/26 2. Bundesliga season ended around this date, but
it is not proven. It may also be a limitation of the demo/free API, incomplete
coverage, or missing future-season data.

## Product Lessons

- Source quality is the first hard problem, not calendar generation.
- We need source-level confidence labels: official, partner, paid provider,
  community database, scraped, manual.
- Google/Outlook direct API publishing should not be the first milestone. ICS
  subscriptions prove most of the calendar value with much less auth and
  compliance work.
- A useful product needs update semantics: postponed, cancelled, time changed,
  venue changed, and deleted events.

## Next Recommended Spikes

1. Compare KSC coverage across TheSportsDB, football-data.org, and one paid
   sports-data provider.
2. Check whether the official KSC website exposes structured event data or an
   RSS/ICS/feed endpoint.
3. Host the generated `.ics` file and test subscription refresh behavior in
   Apple Calendar, Google Calendar, and Outlook.
4. Add a persistence layer so updates can be tracked rather than regenerated
   blindly.
5. Only after that, build Google Calendar and Microsoft Graph OAuth publishing
   spikes.

