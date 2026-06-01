from __future__ import annotations

from dataclasses import dataclass


SPORT_FEED_MANIFEST_VERSION = 1
SPORT_FEED_MANIFEST_FILENAME = "sport-feeds.json"


@dataclass(frozen=True)
class SportGroup:
    group_id: str
    name: str
    description: str


@dataclass(frozen=True)
class SportSubgroup:
    subgroup_id: str
    group_id: str
    name: str
    description: str


@dataclass(frozen=True)
class LeagueImportConfig:
    config_id: str
    group_id: str
    subgroup_id: str
    sport_id: str
    sport_name: str
    league_name: str
    provider: str
    provider_key: str
    calendar_mode: str
    source_quality: str
    season_format: str = "single-year"
    league_id: str | None = None
    api_key_env: str | None = None
    enabled: bool = True


SPORT_GROUPS = (
    SportGroup("team-sports", "Teamsport", "Ligen mit Teamkalendern je Mannschaft."),
    SportGroup("combat-sports", "Kampfsport", "Fight Cards und Events ohne stabile Teamstruktur."),
    SportGroup("motorsport", "Motorsport", "Serien, Rennen und Sessions."),
    SportGroup("tours-precision", "Turniere & Tours", "Tours, Turniere und Einzelwettbewerbe."),
    SportGroup("digital", "Digital", "Esports-Ligen und Turniere."),
)


SPORT_SUBGROUPS = (
    SportSubgroup("football", "team-sports", "Fußball", "Club- und Ligaspielpläne."),
    SportSubgroup("basketball", "team-sports", "Basketball", "Basketball-Ligen und Teams."),
    SportSubgroup("ice-hockey", "team-sports", "Eishockey", "Eishockey-Ligen und Teams."),
    SportSubgroup("baseball", "team-sports", "Baseball", "Baseball-Ligen und Teams."),
    SportSubgroup("american-football", "team-sports", "Football", "American-Football-Ligen und Teams."),
    SportSubgroup("boxing", "combat-sports", "Boxen", "Boxveranstaltungen und Fight Cards."),
    SportSubgroup("ufc", "combat-sports", "UFC", "UFC-Events und Fight Nights."),
    SportSubgroup("formula-1", "motorsport", "Formel 1", "Grand Prix und Sessions."),
    SportSubgroup("golf", "tours-precision", "Golf", "Tour-Events und Turniere."),
    SportSubgroup("tour-de-france", "tours-precision", "Tour de France", "Etappen und Tour-Termine."),
    SportSubgroup("darts", "tours-precision", "Dart", "Dart-Turniere und Majors."),
    SportSubgroup("chess", "tours-precision", "Schach", "Schachturniere und Online-Events."),
    SportSubgroup("esports", "digital", "Esports", "Digitale Wettbewerbe und Matches."),
)


LEAGUE_IMPORT_CONFIGS = (
    LeagueImportConfig(
        config_id="football-data-bl1",
        group_id="team-sports",
        subgroup_id="football",
        sport_id="football",
        sport_name="Fußball",
        league_name="Bundesliga",
        provider="football-data.org",
        provider_key="football-data",
        calendar_mode="team",
        source_quality="paid_provider",
        season_format="football-year-range",
        league_id="BL1",
        api_key_env="FOOTBALL_DATA_API_KEY",
    ),
    LeagueImportConfig("thesportsdb-nba", "team-sports", "basketball", "basketball", "Basketball", "NBA", "TheSportsDB", "thesportsdb", "team", "community", "football-year-range"),
    LeagueImportConfig("thesportsdb-mlb", "team-sports", "baseball", "baseball", "Baseball", "MLB", "TheSportsDB", "thesportsdb", "team", "community"),
    LeagueImportConfig("thesportsdb-nhl", "team-sports", "ice-hockey", "ice-hockey", "Eishockey", "NHL", "TheSportsDB", "thesportsdb", "team", "community", "football-year-range"),
    LeagueImportConfig("thesportsdb-nfl", "team-sports", "american-football", "american-football", "Football", "NFL", "TheSportsDB", "thesportsdb", "team", "community", "football-year-range"),
    LeagueImportConfig("thesportsdb-boxing", "combat-sports", "boxing", "boxing", "Boxen", "Boxing", "TheSportsDB", "thesportsdb", "competition", "community"),
    LeagueImportConfig("thesportsdb-ufc", "combat-sports", "ufc", "ufc", "UFC", "UFC", "TheSportsDB", "thesportsdb", "competition", "community"),
    LeagueImportConfig("jolpica-f1", "motorsport", "formula-1", "formula-1", "Formel 1", "Formula 1", "Jolpica F1", "jolpica-f1", "competition", "community"),
    LeagueImportConfig("thesportsdb-golf", "tours-precision", "golf", "golf", "Golf", "PGA Tour", "TheSportsDB", "thesportsdb", "competition", "community"),
    LeagueImportConfig("thesportsdb-darts", "tours-precision", "darts", "darts", "Dart", "PDC Darts", "TheSportsDB", "thesportsdb", "competition", "community"),
    LeagueImportConfig("lichess-tournaments", "tours-precision", "chess", "chess", "Schach", "Lichess Tournaments", "Lichess", "lichess", "competition", "community", enabled=False),
    LeagueImportConfig("pandascore-esports", "digital", "esports", "esports", "Esports", "Esports Fixtures", "PandaScore", "pandascore", "competition", "community", api_key_env="PANDASCORE_API_KEY", enabled=False),
    LeagueImportConfig("manual-tour-de-france", "tours-precision", "tour-de-france", "cycling", "Tour de France", "Tour de France", "Manuell kuratiert", "manual", "competition", "manual", enabled=False),
)


def sport_taxonomy_payload() -> dict:
    groups = [
        {
            "id": group.group_id,
            "name": group.name,
            "description": group.description,
            "subgroups": [
                {
                    "id": subgroup.subgroup_id,
                    "name": subgroup.name,
                    "description": subgroup.description,
                }
                for subgroup in SPORT_SUBGROUPS
                if subgroup.group_id == group.group_id
            ],
        }
        for group in SPORT_GROUPS
    ]
    providers = [
        {
            "id": config.config_id,
            "groupId": config.group_id,
            "subgroupId": config.subgroup_id,
            "sportId": config.sport_id,
            "sportName": config.sport_name,
            "leagueName": config.league_name,
            "provider": config.provider,
            "providerKey": config.provider_key,
            "calendarMode": config.calendar_mode,
            "sourceQuality": config.source_quality,
            "apiKeyEnv": config.api_key_env,
            "enabled": config.enabled,
        }
        for config in LEAGUE_IMPORT_CONFIGS
    ]
    return {"groups": groups, "providers": providers}
