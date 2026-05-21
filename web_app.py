#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from zoneinfo import ZoneInfo

from yourcalendar_poc import (
    DEFAULT_OUTPUT,
    DEFAULT_TIMEZONE,
    OPENLIGADB_BASE,
    OPENLIGADB_LEAGUES,
    POCError,
    build_sample_events,
    default_football_season,
    fetch_json_list,
    fetch_openligadb_multi_league_events,
    render_ics,
    write_ics,
)
from yourcalendar_sources import source_plan_payload


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
OUTPUT_PATH = ROOT / DEFAULT_OUTPUT
CALENDAR_NAME = "YourCalendar German Football"
SAMPLE_CALENDAR_NAME = "YourCalendar Sample Football"
CURRENT_FEED_ID = "current"
FEED_PARAM_KEYS = ("sample", "leagues", "team", "favorites", "includePast", "season")


@dataclass(frozen=True)
class PublishedCalendar:
    feed_id: str
    category_id: str
    name: str
    description: str
    source_label: str
    source_type: str
    source_type_label: str
    quality_level: str
    quality_label: str
    update_policy: str
    reliability_note: str
    data_warnings: tuple[str, ...]
    params: dict[str, str] | None
    sample: bool = False


@dataclass(frozen=True)
class CalendarCategory:
    category_id: str
    name: str
    description: str


@dataclass(frozen=True)
class SportCoverageOption:
    option_id: str
    name: str
    scope: str
    group: str
    status_label: str
    description: str
    source_note: str


CALENDAR_CATEGORIES = (
    CalendarCategory(
        category_id="sports",
        name="Sport",
        description="Spielpläne und Wettbewerbe, die als abonnierbare Kalender bereitstehen.",
    ),
    CalendarCategory(
        category_id="combat",
        name="Kampfsport",
        description="Weltweite Kampfsportveranstaltungen. Datenanbieter ist noch nicht angebunden.",
    ),
    CalendarCategory(
        category_id="politics",
        name="Politik",
        description="Politische Termine und öffentliche Sitzungen. Noch nicht im MVP befüllt.",
    ),
    CalendarCategory(
        category_id="city",
        name="Stadt",
        description="Kommunale Termine, Stadtfeste und lokale Veranstaltungen. Noch nicht befüllt.",
    ),
    CalendarCategory(
        category_id="culture",
        name="Kultur",
        description="Kulturprogramme, Festivals und Veranstaltungen. Noch nicht befüllt.",
    ),
    CalendarCategory(
        category_id="holidays",
        name="Ferien",
        description="Ferien- und Feiertagskalender. Noch nicht befüllt.",
    ),
)


QUALITY_LEGEND = (
    {
        "id": "poc",
        "label": "POC",
        "description": "Frühe technische Validierung; noch keine produktive Datenzusage.",
    },
    {
        "id": "community",
        "label": "Community",
        "description": "Freie oder Community-nahe Quelle ohne garantierte Echtzeit- oder SLA-Zusage.",
    },
    {
        "id": "official",
        "label": "Offiziell",
        "description": "Direkte Partner- oder Rechteinhaberquelle mit klarer Aktualisierungszusage.",
    },
    {
        "id": "planned",
        "label": "Geplant",
        "description": "Im Produkt auswählbar, aber noch ohne produktive Datenquelle.",
    },
)


EUROPEAN_SPORTS = (
    SportCoverageOption("football", "Fußball", "Europa", "Mannschaftssport", "Teilweise live", "Deutschland ist im POC über OpenLigaDB angebunden.", "OpenLigaDB deckt aktuell nur ausgewählte deutsche Fußballwettbewerbe ab."),
    SportCoverageOption("basketball", "Basketball", "Europa", "Mannschaftssport", "Provider nötig", "Europäische Ligen, Cups und Nationalteam-Termine.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("handball", "Handball", "Europa", "Mannschaftssport", "Provider nötig", "Club- und Verbandstermine in europäischen Wettbewerben.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("ice-hockey", "Eishockey", "Europa", "Mannschaftssport", "Provider nötig", "Nationale Ligen, Champions Hockey League und Turniere.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("tennis", "Tennis", "Europa", "Einzelsport", "Provider nötig", "ATP-, WTA-, Challenger- und ITF-Termine mit Europa-Fokus.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("volleyball", "Volleyball", "Europa", "Mannschaftssport", "Provider nötig", "Liga-, Cup- und Nationalteam-Termine.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("rugby", "Rugby", "Europa", "Mannschaftssport", "Provider nötig", "Union, League und europäische Wettbewerbe.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("cricket", "Cricket", "Europa", "Mannschaftssport", "Provider nötig", "Internationale und nationale Cricket-Termine in Europa.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("cycling", "Radsport", "Europa", "Ausdauer", "Provider nötig", "Straße, Bahn, Cyclocross und große Rundfahrten.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("motorsport", "Motorsport", "Europa", "Motorsport", "Provider nötig", "Formel-, Rallye-, Touring- und Motorradserien.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("athletics", "Leichtathletik", "Europa", "Olympisch", "Provider nötig", "Meetings, Meisterschaften und Straßenläufe.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("swimming", "Schwimmen", "Europa", "Olympisch", "Provider nötig", "Meetings, Meisterschaften und offene Wasser-Termine.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("winter-sports", "Wintersport", "Europa", "Winter", "Provider nötig", "Ski alpin, Langlauf, Biathlon, Bob, Rodeln und Eissport.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("field-hockey", "Hockey", "Europa", "Mannschaftssport", "Provider nötig", "Feld- und Hallenhockey-Termine.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("table-tennis", "Tischtennis", "Europa", "Rückschlag", "Provider nötig", "Ligen, Cups und Turniere.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("badminton", "Badminton", "Europa", "Rückschlag", "Provider nötig", "Turniere, Ligen und internationale Wettbewerbe.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("golf", "Golf", "Europa", "Einzelsport", "Provider nötig", "Tour-Events und nationale Turniere.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("darts", "Darts", "Europa", "Ziel-/Präzision", "Provider nötig", "Tour, Majors und regionale Events.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("snooker", "Snooker", "Europa", "Ziel-/Präzision", "Provider nötig", "Turniere und Tour-Termine.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("futsal", "Futsal", "Europa", "Mannschaftssport", "Provider nötig", "Nationale und internationale Futsal-Termine.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("water-polo", "Wasserball", "Europa", "Mannschaftssport", "Provider nötig", "Ligen, Cups und Nationalteam-Turniere.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("rowing", "Rudern", "Europa", "Ausdauer", "Provider nötig", "Regatten und Meisterschaften.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("sailing", "Segeln", "Europa", "Wasser", "Provider nötig", "Regatten, Serien und Meisterschaften.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("triathlon", "Triathlon", "Europa", "Ausdauer", "Provider nötig", "Rennen, Serien und Meisterschaften.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("gymnastics", "Turnen", "Europa", "Olympisch", "Provider nötig", "Turniere, Cups und Meisterschaften.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("horse-sports", "Pferdesport", "Europa", "Reitsport", "Provider nötig", "Springen, Dressur, Vielseitigkeit und Rennen.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("american-football", "American Football", "Europa", "Mannschaftssport", "Provider nötig", "ELF, nationale Ligen und internationale Termine.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("esports", "E-Sports", "Europa", "Digital", "Provider nötig", "Turniere und Liga-Termine mit Europa-Fokus.", "Noch keine verlässliche Quelle angebunden."),
    SportCoverageOption("other-european-sports", "Weitere Sportarten", "Europa", "Offen", "Provider nötig", "Fallback-Auswahl für Sportarten, die noch nicht als eigener Chip geführt sind.", "Die finale Sportartenliste muss aus der angebundenen Provider-Taxonomie kommen."),
)


GLOBAL_COMBAT_SPORTS = (
    SportCoverageOption("mma", "MMA", "Weltweit", "Kampfsport", "Provider nötig", "Organisationen, Fight Nights, Titelkämpfe und regionale Shows.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("boxing", "Boxen", "Weltweit", "Kampfsport", "Provider nötig", "Profikämpfe, Titelkämpfe, Amateurturniere und Fight Cards.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("kickboxing", "Kickboxen", "Weltweit", "Kampfsport", "Provider nötig", "Kickboxing-Events und internationale Shows.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("muay-thai", "Muay Thai", "Weltweit", "Kampfsport", "Provider nötig", "Stadion-Events, internationale Shows und Titelkämpfe.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("bjj-grappling", "BJJ & Grappling", "Weltweit", "Kampfsport", "Provider nötig", "Turniere, Superfights und Submission-Grappling-Events.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("wrestling", "Ringen", "Weltweit", "Kampfsport", "Provider nötig", "Freistil, griechisch-römisch, Turniere und Meisterschaften.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("judo", "Judo", "Weltweit", "Kampfsport", "Provider nötig", "Grand Slams, Cups, nationale und internationale Meisterschaften.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("karate", "Karate", "Weltweit", "Kampfsport", "Provider nötig", "Turniere, Serien und Meisterschaften.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("taekwondo", "Taekwondo", "Weltweit", "Kampfsport", "Provider nötig", "Turniere, Serien und Meisterschaften.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("sambo", "Sambo", "Weltweit", "Kampfsport", "Provider nötig", "Combat Sambo und Sport Sambo Events.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("sumo", "Sumo", "Weltweit", "Kampfsport", "Provider nötig", "Basho, internationale Turniere und Verbandsveranstaltungen.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("bare-knuckle", "Bare Knuckle", "Weltweit", "Kampfsport", "Provider nötig", "Fight Cards und regionale Shows.", "Noch keine globale, verlässliche Quelle angebunden."),
    SportCoverageOption("other-combat-sports", "Weitere Kampfsportarten", "Weltweit", "Kampfsport", "Provider nötig", "Fallback-Auswahl für weitere Kampfsportarten und regionale Eventformen.", "Die finale Kampfsportliste muss aus einer belastbaren globalen Datenquelle kommen."),
)


PUBLISHED_CALENDARS = {
    "football-germany": PublishedCalendar(
        feed_id="football-germany",
        category_id="sports",
        name=CALENDAR_NAME,
        description="Bundesliga, 2. Bundesliga, 3. Liga und DFB-Pokal aus OpenLigaDB.",
        source_label="OpenLigaDB, Community-Daten",
        source_type="community",
        source_type_label="Community-Quelle",
        quality_level="community",
        quality_label="Community, kein SLA",
        update_policy="Der Feed lädt Spielplandaten beim Abruf neu aus OpenLigaDB.",
        reliability_note="OpenLigaDB ist für den POC nützlich, aber kein garantierter Echtzeitprovider.",
        data_warnings=(
            "Anstoßzeiten und Verlegungen müssen später gegen eine verlässliche Quelle geprüft werden.",
            "Saisonende oder fehlende Spieltage können zu leeren Feeds führen.",
            "OpenLigaDB liefert keine SLA-Zusage für Vollständigkeit oder Aktualisierungslatenz.",
        ),
        params={
            "sample": "false",
            "leagues": "bl1,bl2,bl3,dfb",
            "includePast": "false",
        },
    ),
    "sample-ksc": PublishedCalendar(
        feed_id="sample-ksc",
        category_id="sports",
        name=SAMPLE_CALENDAR_NAME,
        description="Sample-Feed mit klar markierten Testspielen.",
        source_label="YourCalendar Sample-Daten",
        source_type="poc",
        source_type_label="POC-Testdaten",
        quality_level="poc",
        quality_label="Sample, nicht echt",
        update_policy="Statische Testdaten werden beim Feed-Abruf neu gerendert.",
        reliability_note="Dieser Kalender dient nur zum Testen des Abo-Flows.",
        data_warnings=(
            "Alle Termine sind mit [SAMPLE] markiert.",
            "Nicht für echte Spieltermine oder Erinnerungen verwenden.",
        ),
        params={
            "sample": "true",
            "leagues": "bl1,bl2,bl3",
            "includePast": "true",
        },
        sample=True,
    ),
    "europe-all-sports": PublishedCalendar(
        feed_id="europe-all-sports",
        category_id="sports",
        name="Europa Sportarten",
        description="Auswahl aller geplanten Sportarten mit Europa-Fokus. Feeds werden nach Datenquellen-Anbindung freigeschaltet.",
        source_label="Provider noch nicht angebunden",
        source_type="planned",
        source_type_label="Datenquelle offen",
        quality_level="planned",
        quality_label="Provider nötig",
        update_policy="Noch kein produktiver Importjob. Auswahl ist als Produktstruktur vorbereitet.",
        reliability_note="Sportarten sind auswählbar, aber ohne angebundene Quelle werden noch keine echten Termine angezeigt.",
        data_warnings=(
            "Keine Live-Termine ohne verifizierte Datenquelle.",
            "Ligen, Verbände und Rechte müssen je Sportart geklärt werden.",
            "Europaweite Vollständigkeit ist erst nach Provider- und Quellenprüfung belastbar.",
        ),
        params=None,
    ),
    "world-europe-championships": PublishedCalendar(
        feed_id="world-europe-championships",
        category_id="sports",
        name="WM & EM laufende Turniere",
        description="Welt- und Europameisterschaften sollen sichtbar werden, sobald sie laufen oder kurz bevorstehen.",
        source_label="Meisterschafts-Provider noch nicht angebunden",
        source_type="planned",
        source_type_label="Datenquelle offen",
        quality_level="planned",
        quality_label="Provider nötig",
        update_policy="Geplant ist ein Import, der laufende und bevorstehende WM-/EM-Turniere erkennt.",
        reliability_note="Ohne Turnierquelle kann YourCalendar noch nicht sicher wissen, welche WM oder EM gerade läuft.",
        data_warnings=(
            "WM/EM kann je Sportart, Verband und Altersklasse unterschiedlich definiert sein.",
            "Turnierzeiträume, Zeitzonen und Spielplanänderungen brauchen eine verlässliche Quelle.",
            "Bis zur Quellenanbindung werden keine echten WM-/EM-Termine behauptet.",
        ),
        params=None,
    ),
    "global-combat-events": PublishedCalendar(
        feed_id="global-combat-events",
        category_id="combat",
        name="Kampfsport weltweit",
        description="MMA, Boxen, Kickboxen, Muay Thai, Grappling und weitere Kampfsport-Events weltweit.",
        source_label="Globaler Kampfsport-Provider noch nicht angebunden",
        source_type="planned",
        source_type_label="Datenquelle offen",
        quality_level="planned",
        quality_label="Provider nötig",
        update_policy="Noch kein produktiver Importjob. Weltweite Fight Cards brauchen Provider- und Rechteklärung.",
        reliability_note="Sämtliche weltweiten Kampfsportveranstaltungen können erst mit belastbarer globaler Quelle angezeigt werden.",
        data_warnings=(
            "Ohne Provider sind keine vollständigen weltweiten Fight Cards gesichert.",
            "Regionale Shows, Verschiebungen, Weight-ins und kurzfristige Gegnerwechsel sind datenintensiv.",
            "Mehrere Quellen können nötig sein, weil kein einzelner freier Feed gesichert alle Kampfsportarten abdeckt.",
        ),
        params=None,
    ),
}


def split_title(title: str) -> tuple[str, str]:
    if " vs " not in title:
        return title, ""
    home, away = title.split(" vs ", 1)
    return home, away


def league_from_uid(uid: str) -> str:
    parts = uid.split("-")
    if len(parts) >= 3 and parts[0] == "openligadb":
        return parts[1]
    return "sample"


def event_to_dict(event) -> dict:
    home, away = split_title(event.title)
    league = league_from_uid(event.uid)
    return {
        "uid": event.uid,
        "title": event.title,
        "homeTeam": home,
        "awayTeam": away,
        "league": league,
        "leagueName": OPENLIGADB_LEAGUES.get(league, "Sample"),
        "startsAt": event.starts_at.isoformat(),
        "endsAt": event.ends_at.isoformat(),
        "dateLabel": event.starts_at.strftime("%d.%m.%Y"),
        "timeLabel": event.starts_at.strftime("%H:%M %Z"),
        "location": event.location,
        "source": event.source,
        "sourceQuality": event.source_quality,
        "category": event.category,
        "allDay": event.all_day,
        "qualityNotes": list(event.quality_notes),
        "description": event.description,
        "status": event.status,
    }


def selected_leagues(params: dict[str, list[str]]) -> list[str]:
    raw = params.get("leagues", ["bl1,bl2,bl3"])[0]
    leagues = [item.strip() for item in raw.split(",") if item.strip()]
    return [league for league in leagues if league in OPENLIGADB_LEAGUES]


def normalize_feed_params(params: dict[str, list[str]]) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for key in FEED_PARAM_KEYS:
        values = [value for value in params.get(key, []) if value != ""]
        if values:
            normalized[key] = values
    if "sample" not in normalized:
        normalized["sample"] = ["false"]
    if "leagues" not in normalized:
        normalized["leagues"] = ["bl1,bl2,bl3"]
    if "includePast" not in normalized:
        normalized["includePast"] = ["false"]
    return normalized


def params_from_calendar(calendar: PublishedCalendar) -> dict[str, list[str]]:
    if calendar.params is None:
        raise KeyError(calendar.feed_id)
    return {key: [value] for key, value in calendar.params.items()}


def calendar_name_for_params(params: dict[str, list[str]]) -> str:
    return SAMPLE_CALENDAR_NAME if params.get("sample", ["false"])[0] == "true" else CALENDAR_NAME


def feed_path_for_params(params: dict[str, list[str]]) -> str:
    normalized = normalize_feed_params(params)
    query_items = [(key, normalized[key][0]) for key in FEED_PARAM_KEYS if key in normalized]
    query = urlencode(query_items)
    return f"/feeds/{CURRENT_FEED_ID}.ics?{query}" if query else f"/feeds/{CURRENT_FEED_ID}.ics"


def published_feed_path(feed_id: str) -> str:
    calendar = PUBLISHED_CALENDARS.get(feed_id)
    if calendar is None or calendar.params is None:
        raise KeyError(feed_id)
    return f"/feeds/{feed_id}.ics"


def feed_filename(feed_id: str) -> str:
    safe_id = "".join(char for char in feed_id if char.isalnum() or char in ("-", "_"))
    return f"yourcalendar-{safe_id or CURRENT_FEED_ID}.ics"


def resolve_feed(feed_id: str, query: str) -> tuple[str, dict[str, list[str]], bool]:
    if feed_id == CURRENT_FEED_ID:
        params = normalize_feed_params(parse_qs(query))
        return calendar_name_for_params(params), params, params.get("sample", ["false"])[0] == "true"

    calendar = PUBLISHED_CALENDARS[feed_id]
    if calendar.params is None:
        raise KeyError(feed_id)
    return calendar.name, params_from_calendar(calendar), calendar.sample


def render_feed(feed_id: str, query: str = "") -> tuple[str, bool]:
    calendar_name, params, is_sample = resolve_feed(feed_id, query)
    return render_ics(load_events(params), calendar_name), is_sample


def catalog_timestamp(now: datetime | None = None) -> datetime:
    current = now or datetime.now(ZoneInfo(DEFAULT_TIMEZONE))
    if current.tzinfo is None:
        return current.replace(tzinfo=ZoneInfo(DEFAULT_TIMEZONE))
    return current.astimezone(ZoneInfo(DEFAULT_TIMEZONE))


def format_catalog_timestamp(value: datetime) -> str:
    return value.strftime("%d.%m.%Y %H:%M %Z")


def sport_coverage_option_payload(option: SportCoverageOption) -> dict:
    return {
        "id": option.option_id,
        "name": option.name,
        "scope": option.scope,
        "group": option.group,
        "statusLabel": option.status_label,
        "description": option.description,
        "sourceNote": option.source_note,
    }


def sports_coverage_payload() -> dict:
    return {
        "europeSports": [sport_coverage_option_payload(option) for option in EUROPEAN_SPORTS],
        "globalCombatSports": [sport_coverage_option_payload(option) for option in GLOBAL_COMBAT_SPORTS],
        "championships": [
            {
                "id": "world-championships",
                "name": "Weltmeisterschaften",
                "scope": "Weltweit",
                "group": "WM/EM",
                "statusLabel": "Provider nötig",
                "description": "Laufende und bevorstehende Weltmeisterschaften sollen je Sportart angezeigt werden.",
                "sourceNote": "Noch keine verlässliche sportartenübergreifende Turnierquelle angebunden.",
            },
            {
                "id": "european-championships",
                "name": "Europameisterschaften",
                "scope": "Europa",
                "group": "WM/EM",
                "statusLabel": "Provider nötig",
                "description": "Laufende und bevorstehende Europameisterschaften sollen je Sportart angezeigt werden.",
                "sourceNote": "Noch keine verlässliche sportartenübergreifende Turnierquelle angebunden.",
            },
        ],
    }


def calendar_payload(calendar: PublishedCalendar, absolute_url, checked_at: datetime) -> dict:
    has_feed = calendar.params is not None
    feed_url = published_feed_path(calendar.feed_id) if has_feed else None
    checked_label = format_catalog_timestamp(checked_at)
    status = "planned"
    status_label = "Geplant"
    if has_feed:
        status = "sample" if calendar.sample else "available"
        status_label = "Sample" if calendar.sample else "Verfügbar"
    return {
        "id": calendar.feed_id,
        "categoryId": calendar.category_id,
        "name": calendar.name,
        "description": calendar.description,
        "sourceLabel": calendar.source_label,
        "sample": calendar.sample,
        "hasFeed": has_feed,
        "status": status,
        "statusLabel": status_label,
        "quality": {
            "level": calendar.quality_level,
            "label": calendar.quality_label,
            "sourceType": calendar.source_type,
            "sourceTypeLabel": calendar.source_type_label,
            "updatePolicy": calendar.update_policy,
            "updatedAt": checked_at.isoformat(),
            "updatedLabel": f"Katalogstand {checked_label}",
            "reliabilityNote": calendar.reliability_note,
            "warnings": list(calendar.data_warnings),
        },
        "feedUrl": feed_url,
        "subscribeUrl": absolute_url(feed_url) if feed_url else None,
    }


def calendar_catalog(absolute_url, now: datetime | None = None) -> list[dict]:
    checked_at = catalog_timestamp(now)
    calendars_by_category: dict[str, list[dict]] = {
        category.category_id: [] for category in CALENDAR_CATEGORIES
    }
    for calendar in PUBLISHED_CALENDARS.values():
        calendars_by_category.setdefault(calendar.category_id, []).append(
            calendar_payload(calendar, absolute_url, checked_at)
        )

    return [
        {
            "id": category.category_id,
            "name": category.name,
            "description": category.description,
            "calendarCount": len(calendars_by_category.get(category.category_id, [])),
            "calendars": calendars_by_category.get(category.category_id, []),
        }
        for category in CALENDAR_CATEGORIES
    ]


def load_events(params: dict[str, list[str]]) -> list:
    use_sample = params.get("sample", ["false"])[0] == "true"
    if use_sample:
        return build_sample_events(DEFAULT_TIMEZONE)

    leagues = selected_leagues(params)
    include_past = params.get("includePast", ["false"])[0] == "true"
    season_raw = params.get("season", [""])[0]
    season = int(season_raw) if season_raw.isdigit() else default_football_season()
    events = fetch_openligadb_multi_league_events(
        leagues=leagues,
        season=season,
        upcoming_only=not include_past,
        tz_name=DEFAULT_TIMEZONE,
    )

    team_query = params.get("team", [""])[0].strip().casefold()
    favorites = [
        item.strip().casefold()
        for item in params.get("favorites", [""])[0].split(",")
        if item.strip()
    ]
    if team_query:
        events = [
            event
            for event in events
            if team_query in event.title.casefold()
        ]
    if favorites:
        events = [
            event
            for event in events
            if any(favorite in event.title.casefold() for favorite in favorites)
        ]
    return events


class YourCalendarHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/events":
            self.handle_events(parsed.query)
            return
        if parsed.path == "/api/leagues":
            self.handle_leagues(parsed.query)
            return
        if parsed.path == "/api/calendars":
            self.handle_calendars()
            return
        if parsed.path == "/api/open-apple":
            self.handle_open_apple(parsed.query)
            return
        if parsed.path.startswith("/feeds/") and parsed.path.endswith(".ics"):
            self.handle_feed(parsed)
            return
        if parsed.path == "/download/football.ics":
            self.handle_legacy_download(parsed.query)
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/feeds/") and parsed.path.endswith(".ics"):
            self.handle_feed(parsed, send_body=False)
            return
        super().do_HEAD()

    def log_message(self, format: str, *args) -> None:
        return

    def handle_events(self, query: str) -> None:
        params = parse_qs(query)
        try:
            normalized_params = normalize_feed_params(params)
            events = load_events(params)
            use_sample = normalized_params.get("sample", ["false"])[0] == "true"
            feed_url = feed_path_for_params(normalized_params)
            self.send_json(
                {
                    "ok": True,
                    "mode": "sample" if use_sample else "live",
                    "count": len(events),
                    "events": [event_to_dict(event) for event in events],
                    "feedUrl": feed_url,
                    "subscribeUrl": self.absolute_url(feed_url),
                    "downloadUrl": feed_url,
                    "sampleFeedUrl": published_feed_path("sample-ksc"),
                    "publishedFeedUrl": published_feed_path("football-germany"),
                    "sourceNote": source_note(use_sample, len(events)),
                }
            )
        except (POCError, ValueError) as exc:
            self.send_json(
                {
                    "ok": False,
                    "error": str(exc),
                    "events": [],
                    "sourceNote": "Die Quelle konnte gerade nicht gelesen werden.",
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

    def handle_calendars(self) -> None:
        generated_at = catalog_timestamp()
        categories = calendar_catalog(self.absolute_url, generated_at)
        calendars = [
            calendar
            for category in categories
            for calendar in category["calendars"]
        ]
        self.send_json(
            {
                "ok": True,
                "generatedAt": generated_at.isoformat(),
                "qualityLegend": list(QUALITY_LEGEND),
                "sportsCoverage": sports_coverage_payload(),
                "sourcePlan": source_plan_payload(),
                "categories": categories,
                "calendars": calendars,
            }
        )

    def handle_leagues(self, query: str) -> None:
        params = parse_qs(query)
        season_raw = params.get("season", [""])[0]
        season = int(season_raw) if season_raw.isdigit() else default_football_season()
        leagues = []
        for shortcut, name in OPENLIGADB_LEAGUES.items():
            teams = []
            try:
                raw_teams = fetch_json_list(f"{OPENLIGADB_BASE}/getavailableteams/{shortcut}/{season}")
                teams = sorted(
                    {
                        team.get("teamName")
                        for team in raw_teams
                        if team.get("teamName")
                    }
                )
            except POCError:
                teams = []
            leagues.append({"id": shortcut, "name": name, "teams": teams})
        self.send_json({"ok": True, "season": season, "leagues": leagues})

    def handle_open_apple(self, query: str) -> None:
        if platform.system() != "Darwin":
            self.send_json(
                {"ok": False, "error": "Apple Calendar import is only available on macOS."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            params = normalize_feed_params(parse_qs(query))
            write_ics(load_events(params), OUTPUT_PATH, calendar_name_for_params(params))
            subprocess.run(["open", str(OUTPUT_PATH)], check=True)
            self.send_json({"ok": True, "message": "Apple Calendar was opened."})
        except (POCError, ValueError) as exc:
            self.send_json(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_GATEWAY,
            )
        except subprocess.CalledProcessError as exc:
            self.send_json(
                {"ok": False, "error": f"Could not open Apple Calendar: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_feed(self, parsed, send_body: bool = True) -> None:
        feed_id = parsed.path.removeprefix("/feeds/").removesuffix(".ics")
        try:
            self.serve_feed(feed_id, parsed.query, disposition="inline", send_body=send_body)
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown calendar feed.")
        except (POCError, ValueError) as exc:
            self.send_error(HTTPStatus.BAD_GATEWAY, str(exc))

    def handle_legacy_download(self, query: str) -> None:
        try:
            self.serve_feed(CURRENT_FEED_ID, query, disposition="attachment")
        except (POCError, ValueError) as exc:
            self.send_error(HTTPStatus.BAD_GATEWAY, str(exc))

    def serve_feed(self, feed_id: str, query: str, disposition: str, send_body: bool = True) -> None:
        content, is_sample = render_feed(feed_id, query)
        content_bytes = content.encode("utf-8")
        if is_sample and "[SAMPLE]" not in content:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Sample feed is not clearly marked.")
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/calendar; charset=utf-8")
        self.send_header("Content-Disposition", f'{disposition}; filename="{feed_filename(feed_id)}"')
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(content_bytes)))
        self.end_headers()
        if send_body:
            self.wfile.write(content_bytes)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def absolute_url(self, path: str) -> str:
        public_base = os.environ.get("YOURCALENDAR_PUBLIC_BASE_URL", "").rstrip("/")
        if public_base:
            return f"{public_base}{path}"
        forwarded_proto = self.headers.get("X-Forwarded-Proto")
        scheme = forwarded_proto.split(",")[0].strip() if forwarded_proto else "http"
        host = self.headers.get("Host", "127.0.0.1:8765")
        return f"{scheme}://{host}{path}"


def source_note(use_sample: bool, count: int) -> str:
    if use_sample:
        return "Sample-Modus: Diese Termine sind Testdaten und keine echten Spiele."
    if count == 0:
        return (
            "OpenLigaDB liefert für diese Filter aktuell keine kommenden Termine. "
            "Saisonende, Liga-Auswahl oder Filter können der Grund sein."
        )
    return (
        "OpenLigaDB: freie Spielplan-/Ergebnisdaten für den POC. "
        "Für garantierte Realtime-Daten braucht es später einen Provider mit SLA."
    )


def main() -> None:
    host = "127.0.0.1"
    port = 8765
    server = ThreadingHTTPServer((host, port), YourCalendarHandler)
    print(f"YourCalendar UI: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
