# YourCalendar Alpha Product Documentation

This document describes the current Alpha product, its data model, runtime
flow, extension points, mapping format, and test base.

## 1. Product Purpose

YourCalendar Alpha provides a generic website for subscribable ICS calendars.
The calendars are defined through CSV files instead of code changes. A sync
process reads the mapping, selects the configured API provider for each
calendar, fetches provider events, renders ICS files, and exposes those files
through the website.

The current Alpha focuses on football team calendars. The included mapping
covers 218 team calendars for:

- Germany: 1. Bundesliga, 2. Bundesliga, 3. Bundesliga
- Spain: La Liga, La Liga 2
- England: Premier League, Championship
- France: Ligue 1, Ligue 2
- Italy: Serie A, Serie B

Important domain assumption: the current football mapping intentionally contains
men's teams. Reserve teams can appear. Women's teams are intentionally excluded
for now and should later receive their own subgroup or category.

## 2. Runtime Flow

### 2.1 Website Request

1. `python -m yourcalendar_alpha.web_app` starts a local HTTP server.
2. `web_app.create_calendar_server()` creates a `ThreadingHTTPServer`.
3. `web.http_handler.CalendarHttpRequestHandler` handles incoming requests.
4. `GET /` calls `web.page_renderer.render_home_page()`.
5. The renderer loads `data/mapping.csv` and `data/group_logo_settings.csv`.
6. `calendar.tree_builder.build_calendar_tree()` converts mapping entries into
   category and group nodes.
7. The renderer creates HTML tiles for groups and calendar entries.
8. Browser behavior is loaded from `web/static/site.js`.
9. Visual design is loaded from `web/static/site.css`.

### 2.2 ICS Request

1. A calendar tile opens a subscribe dialog.
2. The dialog offers Google Calendar, Outlook, Apple Calendar, and direct ICS.
3. Those links point to `/ics/<ICSId>.ics`.
4. `web.http_handler.CalendarHttpRequestHandler` reads the matching file from
   `public/ics/`.
5. The server responds with `text/calendar; charset=utf-8`.

### 2.3 Calendar Sync

1. `python -m yourcalendar_alpha.update_calendars` starts a one-time sync.
2. `sync.service.sync_all_calendars()` loads all mapping entries.
3. `providers.registry.build_provider_registry()` creates available providers.
4. For each mapping entry, the provider named by `API-Provider` is selected.
5. The provider returns generic `CalendarEvent` objects.
6. Existing ICS event sequences are parsed from the target ICS file.
7. Created, updated, and deleted event counts are calculated.
8. `ics.renderer.render_ics_calendar()` writes the new ICS content.

### 2.4 Scheduler Loop

`python -m yourcalendar_alpha.scheduler_loop` runs the same sync repeatedly.
The interval is read from `settings.json` as `refresh_interval_hours`; the
default behavior is 6 hours.

## 3. Directory Responsibilities

```text
yourcalendar_alpha/
  calendar/       tree building, subscription URLs, safe calendar filenames
  config/         settings loading and path resolution
  domain/         core data classes
  ics/            ICS rendering, parsing, formatting, sequence calculation
  mapping/        CSV mapping and group-logo loading
  providers/      provider contract, registry, TheSportsDB implementation
  sync/           sync service, change counters, CLI report formatting
  web/            HTTP handler, HTML renderer, CSS, JavaScript
```

Compatibility modules remain at selected root paths:

- `yourcalendar_alpha.settings`
- `yourcalendar_alpha.models`
- `yourcalendar_alpha.ics`
- `yourcalendar_alpha.providers`
- `yourcalendar_alpha.sync`

These re-export package functions/classes for older imports. New code should
prefer the package paths.

## 4. Core Classes and Attributes

### 4.1 `domain.calendar_entry.CalendarEntry`

Represents one subscribable calendar entry from `data/mapping.csv`.

Attributes:

| Attribute | Type | Meaning |
|---|---|---|
| `calendar_name` | `str` | Slash-separated display and grouping path. |
| `country` | `str` | Country shown on calendar tiles. |
| `category` | `str` | Top-level website category, for example `Sport`. |
| `competition` | `str` | Competition or league shown on calendar tiles. |
| `api_provider` | `str` | Provider key used to select a registered provider. |
| `api_key_provider` | `str` | Environment variable name for an optional provider API key. |
| `ics_id` | `str` | Provider ID and local ICS file stem. |
| `logo_bytes` | `bytes | None` | Optional decoded logo bytes from `LogoBytes`. |
| `subgroup_order` | `int` | Sort order for calendar tiles inside the same subgroup. |

Properties:

| Property | Meaning |
|---|---|
| `path_parts` | Non-empty slash path parts from `calendar_name`. |
| `display_name` | Last path part; this is the calendar tile title. |
| `group_path` | All path parts before the calendar entry. |

### 4.2 `domain.group_logo.GroupLogo`

Represents one row from `data/group_logo_settings.csv`.

Attributes:

| Attribute | Type | Meaning |
|---|---|---|
| `category` | `str` | Category the group belongs to. |
| `group_path` | `str` | Slash-separated group path inside the category. |
| `logo_bytes` | `bytes | None` | Optional decoded logo bytes. |
| `group_order` | `int` | Sort order for group tiles inside the same level. |

### 4.3 `domain.calendar_tree_node.CalendarTreeNode`

Represents one node in the website navigation tree.

Attributes:

| Attribute | Type | Meaning |
|---|---|---|
| `name` | `str` | Display name of the group/category node. |
| `path` | `str` | Group path without category. |
| `depth` | `int` | Nesting level used by rendering/CSS. |
| `children` | `dict[str, CalendarTreeNode]` | Nested group nodes. |
| `entries` | `list[CalendarEntry]` | Calendar entries directly below this node. |

### 4.4 `domain.calendar_event.CalendarEvent`

Provider-independent event model used by the ICS renderer.

Attributes:

| Attribute | Type | Meaning |
|---|---|---|
| `uid` | `str` | Stable event ID. Must not change between updates of the same event. |
| `title` | `str` | ICS event summary. |
| `starts_at` | `datetime` | Timezone-aware event start. |
| `ends_at` | `datetime` | Timezone-aware event end. |
| `location` | `str` | Venue, city, or location text. |
| `description` | `str` | Event details written into ICS description. |
| `source_hash` | `str` | Hash of provider source data for update detection. |

### 4.5 `domain.sync_result.SyncResult`

Represents the sync result for one calendar.

Attributes:

| Attribute | Type | Meaning |
|---|---|---|
| `calendar_id` | `str` | Mapping `ICSId`. |
| `calendar_name` | `str` | Full mapping calendar path. |
| `created` | `int` | Number of new events compared with existing ICS. |
| `updated` | `int` | Number of changed events compared with existing ICS. |
| `deleted` | `int` | Number of removed events compared with existing ICS. |
| `written_path` | `Path` | Path of the generated ICS file. |

### 4.6 `providers.base.CalendarProvider`

Abstract provider contract.

Class attributes and methods:

| Member | Meaning |
|---|---|
| `name` | Provider key used in `API-Provider`. |
| `fetch_events(entry)` | Returns `list[CalendarEvent]` for one mapping entry. |

### 4.7 `providers.thesportsdb_provider.TheSportsDBProvider`

Current concrete provider.

Constructor attributes:

| Attribute | Meaning |
|---|---|
| `base_url` | TheSportsDB API base URL without trailing slash. |
| `free_api_key` | Fallback API key from settings. |
| `default_duration_minutes` | Event duration used when provider data has no end. |
| `opener` | HTTP opener, injectable for tests. |

Methods:

| Method | Meaning |
|---|---|
| `fetch_events(entry)` | Fetches next and last events and maps them to `CalendarEvent`. |
| `fetch_json(entry, endpoint, params)` | Calls one TheSportsDB endpoint and decodes JSON. |
| `api_key_for(entry)` | Reads the configured environment key or falls back. |

The provider interprets `entry.ics_id` as TheSportsDB `idTeam`.

### 4.8 `web.http_handler.CalendarHttpRequestHandler`

HTTP route handler.

Routes:

| Route | Behavior |
|---|---|
| `/` | Render website HTML. |
| `/ics/<id>.ics` | Serve generated ICS file from configured output directory. |
| `/static/site.css` | Serve CSS from `web/static`. |
| `/static/site.js` | Serve browser JavaScript from `web/static`. |

## 5. Mapping Files

### 5.1 Calendar Mapping: `data/mapping.csv`

Each row defines exactly one subscribable calendar.

Required columns:

| Column | Type | Required | Meaning |
|---|---|---|---|
| `Kalendername` | string | yes | Slash-separated group path and calendar name. Last segment is the subscribable calendar. |
| `Land` | string | yes | Country displayed on the tile. |
| `Kategorie` | string | yes | Top-level category displayed on the website. |
| `Wettbewerb` | string | yes | League/competition displayed on the tile. |
| `API-Provider` | string | yes | Provider registry key, for example `TheSportsDB`. |
| `API-Key-Provider` | string | no | Environment variable name for a provider API key. Empty is allowed. |
| `ICSId` | string | yes | Provider-specific ID and local ICS filename stem. |
| `LogoBytes` | base64 bytes | no | Optional base64-encoded logo bytes. Empty is allowed. |
| `SubGroupOrder` | integer | yes | Calendar tile order inside the same subgroup. |

Example:

```csv
Kalendername,Land,Kategorie,Wettbewerb,API-Provider,API-Key-Provider,ICSId,LogoBytes,SubGroupOrder
Fussball/Deutschland/1. Bundesliga/FC Augsburg,Deutschland,Sport,1. Bundesliga,TheSportsDB,THESPORTSDB_API_KEY,133652,,1
```

Path rule:

```text
GroupEntry/GroupEntry/CalendarEntry
```

Only the last segment is subscribable. Earlier path segments become group tiles.

### 5.2 Group Logo Settings: `data/group_logo_settings.csv`

Each row configures one group tile.

| Column | Type | Required | Meaning |
|---|---|---|---|
| `Kategorie` | string | yes | Category of the group. |
| `GroupPath` | string | yes | Slash-separated group path without category. |
| `LogoBytes` | base64 bytes | yes column, value can be empty | Optional logo bytes. |
| `groupOrder` | integer | yes | Group tile order inside the same level. |

`GroupOrder` is accepted as a compatibility spelling, but `groupOrder` is the
documented spelling.

### 5.3 Provider Lock: `data/mapping.provider-lock.csv`

This file locks manually curated team/provider IDs.

| Column | Meaning |
|---|---|
| `Team` | Team name from the source list. |
| `ICSId` | Provider ID. |
| `Provider` | Provider key. |

The manual mapping script compares newly generated lock rows with this file. If
they differ, the script fails unless `--update-lock` is explicitly passed.

### 5.4 Football Source: `data/football_team_source.csv`

This is the curated source for the current football mapping generator.

| Column | Meaning |
|---|---|
| `Land` | Country. |
| `Wettbewerb` | Competition/league. |
| `Team` | Team name. |
| `SubGroupOrder` | Calendar order inside the league. |
| `API-Provider` | Provider key. |
| `API-Key-Provider` | Environment variable for provider key. |
| `ICSId` | Provider team ID. |

## 6. Add A New Calendar Mapping

Use this when the provider already exists and the category workflow already has
a source script or manual CSV workflow.

1. Determine the provider key for `API-Provider`.
2. Determine the provider-specific calendar ID for `ICSId`.
3. Choose the website path in `Kalendername`.
4. Add a row to `data/mapping.csv`, or add a row to the category source file if
   that mapping is generated.
5. Set `SubGroupOrder` as an integer unique within the same subgroup.
6. Add or update the matching group rows in `data/group_logo_settings.csv`.
7. Set `groupOrder` for any new group path.
8. Run tests.

For the current football workflow, edit `data/football_team_source.csv` instead
of editing `data/mapping.csv` manually, then run:

```powershell
python tools/resolve_manual_team_ids.py
```

If the generated provider lock changes unexpectedly, review the diff and only
then run:

```powershell
python tools/resolve_manual_team_ids.py --update-lock
```

Use `--refresh-provider` only when live provider verification or ID lookup is
intended.

## 7. Implement A New Provider

Use this when a new API/provider should be selectable through `API-Provider`.

### 7.1 Create Provider Class

Create a file under `yourcalendar_alpha/providers/`, for example:

```text
yourcalendar_alpha/providers/example_provider.py
```

Implement the provider contract:

```python
from __future__ import annotations

from yourcalendar_alpha.domain.calendar_entry import CalendarEntry
from yourcalendar_alpha.domain.calendar_event import CalendarEvent
from yourcalendar_alpha.providers.base import CalendarProvider


class ExampleProvider(CalendarProvider):
    name = "ExampleProvider"

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        # 1. Read entry.ics_id as the provider-specific calendar/team ID.
        # 2. Read entry.api_key_provider if the provider needs an API key.
        # 3. Fetch provider data.
        # 4. Map provider data to CalendarEvent objects.
        return []
```

### 7.2 Map Provider Data To `CalendarEvent`

Every event must provide:

- stable `uid`
- `title`
- timezone-aware `starts_at`
- timezone-aware `ends_at`
- `location`
- `description`
- deterministic `source_hash`

The `source_hash` should change when relevant provider data changes. The sync
uses it to calculate ICS `SEQUENCE` and detect updates.

### 7.3 Register Provider

Update `yourcalendar_alpha/providers/registry.py`:

```python
from .example_provider import ExampleProvider


def build_provider_registry(settings: dict[str, Any]) -> dict[str, CalendarProvider]:
    return {
        "TheSportsDB": TheSportsDBProvider(...),
        "ExampleProvider": ExampleProvider(...),
    }
```

The registry key must match `API-Provider` in `data/mapping.csv`.

### 7.4 Add Provider Tests

Add tests that verify:

- provider API payloads are mapped into `CalendarEvent`
- missing optional fields do not crash
- API key lookup behavior is correct if applicable
- generated event UIDs are stable
- changed provider data changes `source_hash`
- sync works with the provider through a fake or mocked provider

Avoid live network calls in normal tests. Use injected openers or fakes.

## 8. Add A New Category Script

Use this when a new category should have its own generated mapping source, like
football currently does.

Recommended structure:

```text
tools/
  <category_name>_mapping/
    __init__.py
    config.py
    csv_table.py
    source_loader.py
    builder.py
    provider_resolver.py
    provider_lock_diff.py
  resolve_<category_name>_calendar_ids.py
```

The script should:

1. Read a curated source file from `data/`.
2. Validate required source columns.
3. Resolve or verify provider IDs.
4. Build `data/mapping.csv` rows or a category-specific mapping output.
5. Compare generated provider IDs against a lock file.
6. Fail when provider IDs changed unexpectedly.
7. Only accept changed IDs with an explicit flag such as `--update-lock`.
8. Avoid using provider endpoints that return incomplete team lists unless the
   endpoint is verified as complete.
9. Include tests or contract checks for expected counts and critical IDs.

For a new category, define the category-specific source format explicitly. At
minimum it should contain:

- country or domain grouping value
- competition/subgroup value
- display name
- sort order
- provider key
- provider API key environment variable
- provider ID

Then define how that source becomes the standard `mapping.csv` columns.

Important: if a new category should not overwrite the football mapping, the
current single `data/mapping.csv` workflow must be extended to merge multiple
category sources. That merge workflow is not implemented yet.

## 9. Current Test Base

The normal test command is:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

The syntax/import check is:

```powershell
python -m compileall yourcalendar_alpha tests tools
```

### 9.1 Mapping Tests

`tests/test_mapping.py` verifies:

- required mapping columns are loaded
- `Kalendername` is split into group path and display name
- `SubGroupOrder` is parsed as integer
- missing required columns are rejected
- duplicate `ICSId` values are rejected
- `groupOrder` is loaded from group logo settings
- `GroupOrder` compatibility casing is accepted
- invalid `groupOrder` is rejected

### 9.2 Web Renderer Tests

`tests/test_web_app.py` verifies:

- mapping entries are grouped into the expected tree
- public ICS URLs use the `/ics/<id>.ics` route
- rendered category markup uses the tile grid and details/summary group markup
- rendered markup does not contain the previous `\u00c2` encoding artifact
- static CSS/JS contain active tree behavior
- dark mode CSS/JS hooks exist
- calendar tiles sort by `SubGroupOrder`
- group tiles sort by `groupOrder`

### 9.3 HTTP Integration Test

`tests/test_integration_web_http.py` starts an in-process HTTP server and
verifies:

- homepage renders a mapping entry
- group path is visible
- subscribe targets for Google, Outlook, Apple, and ICS are present
- CSS is served as `text/css; charset=utf-8`
- JS is served as `text/javascript; charset=utf-8`
- ICS files are served as `text/calendar; charset=utf-8`

### 9.4 Provider And Sync Tests

`tests/test_provider_and_sync.py` verifies:

- TheSportsDB payloads map to `CalendarEvent`
- event UID uses the provider event ID
- venue and city are combined into location
- both `eventsnext.php` and `eventslast.php` are called
- sync writes an ICS file
- first sync reports created events
- repeated sync with unchanged data reports no new or updated events

### 9.5 Mapping Contract Tests

`tests/test_mapping_contract.py` verifies the current curated mapping:

- expected league counts
- total number of mapping rows
- category is `Sport`
- provider is `TheSportsDB`
- provider API key environment variable is `THESPORTSDB_API_KEY`
- `ICSId` and `SubGroupOrder` are numeric
- no `/Women/` path appears
- `ICSId` values are unique
- `SubGroupOrder` is contiguous per league
- selected known problem IDs stay locked
- provider lock file matches mapping
- source file has expected teams and order values
- group logo settings cover all group paths and define numeric `groupOrder`

### 9.6 Optional Live Provider Test

The live test is skipped unless:

```powershell
$env:RUN_LIVE_PROVIDER_TESTS='1'
```

When enabled, it calls TheSportsDB for every mapped `ICSId` and verifies:

- the provider ID exists
- the returned data does not look like a women's team entry

This test is intentionally slow and network-dependent.

## 10. Current Limitations And Assumptions

- The Alpha uses one global `data/mapping.csv`.
- The current category generation script is football-specific.
- A multi-category merge workflow is not implemented yet.
- `ICSId` is both provider ID and local ICS filename stem.
- TheSportsDB `ICSId` means `idTeam`.
- External subscriptions require a public HTTPS `public_base_url`.
- The free TheSportsDB key in settings is only suitable for Alpha/testing.
- The current team list is curated and can become outdated when leagues change.
