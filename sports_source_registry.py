from __future__ import annotations

from dataclasses import dataclass

from yourcalendar_model import SourceQuality


@dataclass(frozen=True)
class SourceCandidate:
    id: str
    name: str
    sports: tuple[str, ...]
    coverage: str
    endpoint_type: str
    base_url: str | None
    repo_url: str | None
    docs_url: str | None
    license: str
    source_quality: SourceQuality
    risk_level: str
    usage_decision: str
    supports_live_events: bool
    requires_api_key: bool
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "sports": list(self.sports),
            "coverage": self.coverage,
            "endpointType": self.endpoint_type,
            "baseUrl": self.base_url,
            "repoUrl": self.repo_url,
            "docsUrl": self.docs_url,
            "license": self.license,
            "sourceQuality": self.source_quality.value,
            "riskLevel": self.risk_level,
            "usageDecision": self.usage_decision,
            "supportsLiveEvents": self.supports_live_events,
            "requiresApiKey": self.requires_api_key,
            "notes": list(self.notes),
        }


SOURCE_CANDIDATES: tuple[SourceCandidate, ...] = (
    SourceCandidate(
        id="openligadb",
        name="OpenLigaDB",
        sports=("football", "soccer", "europe"),
        coverage="German football leagues and cups already used by the POC.",
        endpoint_type="rest-api",
        base_url="https://api.openligadb.de",
        repo_url=None,
        docs_url="https://www.openligadb.de",
        license="Community source; production license and SLA must be verified.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="medium",
        usage_decision="active-poc",
        supports_live_events=True,
        requires_api_key=False,
        notes=(
            "Current MVP source for Bundesliga, 2. Bundesliga, 3. Liga and DFB-Pokal.",
            "Good for prototyping, but not a guaranteed official schedule authority.",
        ),
    ),
    SourceCandidate(
        id="thesportsdb",
        name="TheSportsDB",
        sports=(
            "multi-sport",
            "football",
            "soccer",
            "basketball",
            "baseball",
            "ice-hockey",
            "motorsport",
            "rugby",
            "cricket",
            "tennis",
            "combat-sports",
        ),
        coverage="Crowd-sourced multi-sport teams, leagues and event endpoints.",
        endpoint_type="rest-api",
        base_url="https://www.thesportsdb.com/api/v1/json",
        repo_url=None,
        docs_url="https://www.thesportsdb.com/api.php",
        license="Free tier exists; paid/commercial and attribution rules must be verified before production.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="medium",
        usage_decision="prototype-candidate",
        supports_live_events=True,
        requires_api_key=False,
        notes=(
            "Useful as a broad fallback for many sports.",
            "Free endpoint coverage can be incomplete and crowd-sourced.",
        ),
    ),
    SourceCandidate(
        id="public-espn-api",
        name="Public ESPN API",
        sports=(
            "american-football",
            "baseball",
            "basketball",
            "cricket",
            "field-hockey",
            "football",
            "golf",
            "hockey",
            "ice-hockey",
            "lacrosse",
            "mma",
            "motorsport",
            "racing",
            "rugby",
            "rugby-league",
            "soccer",
            "tennis",
            "volleyball",
            "water-polo",
        ),
        coverage="Documented public ESPN scoreboard/site endpoints across many sports.",
        endpoint_type="unofficial-public-rest-api",
        base_url="https://site.api.espn.com/apis/site/v2/sports",
        repo_url="https://github.com/pseudo-r/Public-ESPN-API",
        docs_url="https://github.com/pseudo-r/Public-ESPN-API",
        license="Repository documents public endpoints; ESPN data usage rights must be verified.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="high",
        usage_decision="research-only",
        supports_live_events=True,
        requires_api_key=False,
        notes=(
            "Very broad sports coverage, including MMA and many US/international leagues.",
            "Treat as an undocumented third-party endpoint until legal and reliability checks pass.",
        ),
    ),
    SourceCandidate(
        id="sportdb",
        name="sport.db open sports datasets",
        sports=("football", "soccer", "motorsport", "formula-1", "skiing", "hockey"),
        coverage="Open data packages and tooling for historical sports datasets.",
        endpoint_type="open-dataset",
        base_url=None,
        repo_url="https://github.com/sportdb",
        docs_url="https://sportdb.github.io",
        license="Dataset-specific licenses; verify each package before redistribution.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="low",
        usage_decision="offline-data-candidate",
        supports_live_events=False,
        requires_api_key=False,
        notes=(
            "Better for seeded metadata, examples and historical data than live event calendars.",
            "Useful as a local fixture source when API coverage is missing.",
        ),
    ),
    SourceCandidate(
        id="openfootball-football-json",
        name="openfootball football.json",
        sports=("football", "soccer", "europe", "world-cup", "euro"),
        coverage="Open football fixtures/results in JSON, including national and tournament datasets.",
        endpoint_type="github-raw-dataset",
        base_url="https://raw.githubusercontent.com/openfootball/football.json/master",
        repo_url="https://github.com/openfootball/football.json",
        docs_url="https://github.com/openfootball/football.json",
        license="Public-domain style open data project; verify tournament package license before production.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="low",
        usage_decision="offline-data-candidate",
        supports_live_events=False,
        requires_api_key=False,
        notes=(
            "Good candidate for World Cup, Euro and other football tournament seed data.",
            "Not a live provider, so postponed/rescheduled matches need another confirmation source.",
        ),
    ),
    SourceCandidate(
        id="openf1",
        name="OpenF1",
        sports=("formula-1", "motorsport", "racing"),
        coverage="Formula 1 sessions, drivers, meetings, laps and timing-oriented data.",
        endpoint_type="rest-api",
        base_url="https://api.openf1.org/v1",
        repo_url="https://github.com/br-g/openf1",
        docs_url="https://openf1.org",
        license="Open source API project; event-data usage should still be checked before production.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="medium",
        usage_decision="prototype-candidate",
        supports_live_events=True,
        requires_api_key=False,
        notes=(
            "Strong motorsport candidate for Formula 1.",
            "Calendar/feed needs meeting/session mapping rather than simple team fixtures.",
        ),
    ),
    SourceCandidate(
        id="jolpica-f1",
        name="Jolpica F1 API",
        sports=("formula-1", "motorsport", "racing"),
        coverage="Ergast-compatible Formula 1 API successor for seasons, races and results.",
        endpoint_type="rest-api",
        base_url="https://api.jolpi.ca/ergast/f1",
        repo_url="https://github.com/jolpica/jolpica-f1",
        docs_url="https://api.jolpi.ca/ergast/f1",
        license="Community API; rate limits and terms must be checked before production.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="medium",
        usage_decision="prototype-candidate",
        supports_live_events=True,
        requires_api_key=False,
        notes=(
            "Good F1 calendar fallback where Ergast-compatible data is enough.",
            "Use cache/import monitoring because community APIs can change availability.",
        ),
    ),
    SourceCandidate(
        id="ufc-stats-api",
        name="UFC Stats API",
        sports=("mma", "ufc", "combat-sports"),
        coverage="UFC fighters, fights, events and statistics exposed by an open API project.",
        endpoint_type="community-rest-api",
        base_url="https://ufcapi.aristotle.me",
        repo_url="https://github.com/aristotle-malichetty/ufc-stats-api",
        docs_url="https://ufcapi.aristotle.me/docs",
        license="Personal/non-commercial style project; UFC data rights must be verified.",
        source_quality=SourceQuality.SCRAPED,
        risk_level="high",
        usage_decision="prototype-only",
        supports_live_events=True,
        requires_api_key=False,
        notes=(
            "Useful to prototype MMA/UFC event ingestion.",
            "Do not ship as a production source before legal, rate-limit and uptime checks.",
        ),
    ),
    SourceCandidate(
        id="octagon-api",
        name="Octagon API",
        sports=("mma", "ufc", "combat-sports"),
        coverage="MMA fighter, division and ranking data from an open-source API project.",
        endpoint_type="community-rest-api",
        base_url="https://api.octagon-api.com",
        repo_url="https://github.com/victor-lillo/octagon-api",
        docs_url="https://www.octagon-api.com",
        license="Repository terms and scraped upstream data rights must be verified.",
        source_quality=SourceQuality.SCRAPED,
        risk_level="high",
        usage_decision="metadata-only-research",
        supports_live_events=False,
        requires_api_key=False,
        notes=(
            "Good MMA metadata companion, but not a full event calendar source.",
            "The project documents a scraper, so keep it out of production until rights are clear.",
        ),
    ),
    SourceCandidate(
        id="ufc-stats-crawler",
        name="UFC stats crawler",
        sports=("mma", "ufc", "combat-sports"),
        coverage="Crawler-based UFC stats extraction from public pages.",
        endpoint_type="scraper-library",
        base_url=None,
        repo_url="https://github.com/fanghuiz/ufc-stats-crawler",
        docs_url="https://github.com/fanghuiz/ufc-stats-crawler",
        license="Repository license and upstream site terms must be verified.",
        source_quality=SourceQuality.SCRAPED,
        risk_level="high",
        usage_decision="do-not-activate",
        supports_live_events=False,
        requires_api_key=False,
        notes=(
            "Keep as research reference only.",
            "A crawler is more fragile and riskier than a documented API or licensed provider.",
        ),
    ),
    SourceCandidate(
        id="valish-mma-api",
        name="MMA API",
        sports=("mma", "ufc", "combat-sports"),
        coverage="Open-source MMA API project for fighters and events.",
        endpoint_type="community-api-project",
        base_url=None,
        repo_url="https://github.com/valish/mma-api",
        docs_url="https://github.com/valish/mma-api",
        license="Repository/project terms must be verified before use.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="high",
        usage_decision="research-only",
        supports_live_events=True,
        requires_api_key=False,
        notes=(
            "Candidate for broader MMA modeling beyond UFC-only data.",
            "Needs local setup and data-source review before an importer is built.",
        ),
    ),
    SourceCandidate(
        id="cricsheet",
        name="Cricsheet",
        sports=("cricket",),
        coverage="Ball-by-ball cricket data in YAML/CSV/JSON-style downloadable datasets.",
        endpoint_type="open-dataset",
        base_url="https://cricsheet.org/downloads",
        repo_url="https://github.com/cricsheet",
        docs_url="https://cricsheet.org",
        license="Cricsheet data license must be checked before redistribution.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="low",
        usage_decision="offline-data-candidate",
        supports_live_events=False,
        requires_api_key=False,
        notes=(
            "Good cricket data source, but not a direct upcoming-event calendar API.",
            "Useful for historical/statistical context or fixture snapshots.",
        ),
    ),
    SourceCandidate(
        id="jeffsackmann-tennis",
        name="Jeff Sackmann Tennis Data",
        sports=("tennis", "atp", "wta"),
        coverage="ATP/WTA match result datasets on GitHub.",
        endpoint_type="github-raw-dataset",
        base_url="https://raw.githubusercontent.com/JeffSackmann",
        repo_url="https://github.com/JeffSackmann/tennis_atp",
        docs_url="https://github.com/JeffSackmann/tennis_atp",
        license="CC BY-NC-SA style data; non-commercial restriction must be respected.",
        source_quality=SourceQuality.COMMUNITY,
        risk_level="medium",
        usage_decision="offline-data-candidate",
        supports_live_events=False,
        requires_api_key=False,
        notes=(
            "Strong historical tennis dataset.",
            "Not suitable as a live ATP/WTA event calendar without another schedule source.",
        ),
    ),
    SourceCandidate(
        id="mysportsfeeds-node",
        name="MySportsFeeds API client",
        sports=("american-football", "baseball", "basketball", "ice-hockey", "golf", "racing"),
        coverage="GitHub client for a commercial sports-data API with broad North American coverage.",
        endpoint_type="api-client",
        base_url="https://api.mysportsfeeds.com",
        repo_url="https://github.com/MySportsFeeds/mysportsfeeds-node",
        docs_url="https://www.mysportsfeeds.com/data-feeds/api-docs/",
        license="API account and provider terms required; not a free GitHub data source.",
        source_quality=SourceQuality.PAID_PROVIDER,
        risk_level="medium",
        usage_decision="paid-provider-evaluation",
        supports_live_events=True,
        requires_api_key=True,
        notes=(
            "Possible paid/provider path if free community sources are too unreliable.",
            "Keep separate from the free/open-source source track.",
        ),
    ),
    SourceCandidate(
        id="sportsipy",
        name="sportsipy",
        sports=("american-football", "baseball", "basketball", "ice-hockey", "soccer"),
        coverage="Python client that pulls sports-reference style statistics.",
        endpoint_type="python-library",
        base_url=None,
        repo_url="https://github.com/roclark/sportsipy",
        docs_url="https://sportsipy.readthedocs.io",
        license="MIT library; upstream website terms must be verified.",
        source_quality=SourceQuality.SCRAPED,
        risk_level="high",
        usage_decision="stats-only-research",
        supports_live_events=False,
        requires_api_key=False,
        notes=(
            "Useful for statistics experiments, not as an upcoming-event source.",
            "Do not combine with production imports until upstream terms are checked.",
        ),
    ),
    SourceCandidate(
        id="public-apis-sports-catalog",
        name="public-apis sports catalog",
        sports=("multi-sport", "discovery"),
        coverage="GitHub catalog of public APIs, including sports entries.",
        endpoint_type="catalog",
        base_url=None,
        repo_url="https://github.com/public-apis/public-apis",
        docs_url="https://github.com/public-apis/public-apis",
        license="Catalog only; each listed API has separate terms.",
        source_quality=SourceQuality.MANUAL,
        risk_level="low",
        usage_decision="discovery-reference",
        supports_live_events=False,
        requires_api_key=False,
        notes=(
            "Use as a discovery checklist, not as an event source.",
            "Each linked API still needs a separate integration decision.",
        ),
    ),
)


def list_source_candidates(
    sport: str | None = None,
    include_risky: bool = True,
) -> list[dict]:
    normalized_sport = (sport or "").strip().casefold()
    candidates = []
    for candidate in SOURCE_CANDIDATES:
        if normalized_sport and not _matches_sport(candidate, normalized_sport):
            continue
        if not include_risky and candidate.risk_level == "high":
            continue
        candidates.append(candidate.as_dict())
    return candidates


def source_candidate_sports() -> list[str]:
    sports = {sport for candidate in SOURCE_CANDIDATES for sport in candidate.sports}
    return sorted(sports)


def _matches_sport(candidate: SourceCandidate, sport: str) -> bool:
    return any(
        sport in candidate_sport.casefold()
        or candidate_sport.casefold() in sport
        for candidate_sport in candidate.sports
    )
