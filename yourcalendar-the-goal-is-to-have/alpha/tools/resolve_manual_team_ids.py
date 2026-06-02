from __future__ import annotations

import csv
import json
import time
import argparse
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "mapping.csv"
LOCK = ROOT / "data" / "mapping.provider-lock.csv"
PROVIDER = "TheSportsDB"
API_KEY_ENV = "THESPORTSDB_API_KEY"
BASE_URL = "https://www.thesportsdb.com/api/v1/json/123"


LEAGUES = [
    ("Deutschland", "Bundesliga", [
        "FC Augsburg", "Union Berlin", "Werder Bremen", "Borussia Dortmund", "Eintracht Frankfurt",
        "SC Freiburg", "Hamburger SV", "1. FC Heidenheim", "TSG Hoffenheim", "1. FC Köln",
        "RB Leipzig", "Bayer Leverkusen", "Mainz 05", "Borussia Mönchengladbach", "Bayern Munich",
        "FC St. Pauli", "VfB Stuttgart", "VfL Wolfsburg",
    ]),
    ("Deutschland", "2. Bundesliga", [
        "Arminia Bielefeld", "VfL Bochum", "Darmstadt 98", "Dynamo Dresden", "Eintracht Braunschweig",
        "Fortuna Düsseldorf", "Greuther Fürth", "Hannover 96", "Hertha BSC", "Holstein Kiel",
        "Kaiserslautern", "Karlsruher SC", "1. FC Magdeburg", "1. FC Nürnberg", "SC Paderborn",
        "Preußen Münster", "Schalke 04", "SV Elversberg",
    ]),
    ("Deutschland", "3. Bundesliga", [
        "1860 Munich", "Alemannia Aachen", "Erzgebirge Aue", "Energie Cottbus", "MSV Duisburg",
        "Hansa Rostock", "Havelse", "Hoffenheim II", "FC Ingolstadt", "Jahn Regensburg",
        "Waldhof Mannheim", "VfL Osnabrück", "Rot-Weiss Essen", "Saarbrücken", "Schweinfurt",
        "VfB Stuttgart II", "SSV Ulm", "Verl", "Viktoria Köln", "Wehen Wiesbaden",
    ]),
    ("Spanien", "La Liga", [
        "Athletic Bilbao", "Atlético Madrid", "Barcelona", "Celta Vigo", "Deportivo Alavés",
        "Elche", "Espanyol", "Getafe", "Girona", "Levante", "Mallorca", "Osasuna",
        "Rayo Vallecano", "Real Betis", "Real Madrid", "Real Oviedo", "Real Sociedad",
        "Sevilla", "Valencia", "Villarreal",
    ]),
    ("Spanien", "La Liga 2", [
        "Albacete", "Almería", "Burgos", "Cádiz", "Castellón", "Ceuta", "Córdoba",
        "Cultural Leonesa", "Deportivo de La Coruña", "Eibar", "Granada", "Huesca",
        "Las Palmas", "Leganés", "Málaga", "Mirandés", "Racing Santander", "Real Sociedad B",
        "Real Valladolid", "Sporting Gijón", "Tenerife", "Zaragoza",
    ]),
    ("England", "Premier League", [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton and Hove Albion",
        "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham", "Leeds United",
        "Liverpool", "Manchester City", "Manchester United", "Newcastle United",
        "Nottingham Forest", "Sunderland", "Tottenham Hotspur", "West Ham United",
        "Wolverhampton Wanderers",
    ]),
    ("England", "Championship", [
        "Birmingham City", "Blackburn Rovers", "Bristol City", "Charlton Athletic",
        "Coventry City", "Derby County", "Hull City", "Ipswich Town", "Leicester City",
        "Middlesbrough", "Millwall", "Norwich City", "Oxford United", "Portsmouth",
        "Preston North End", "Queens Park Rangers", "Sheffield United", "Sheffield Wednesday",
        "Southampton", "Stoke City", "Swansea City", "Watford", "West Bromwich Albion",
        "Wrexham",
    ]),
    ("Frankreich", "Ligue 1", [
        "Angers", "Auxerre", "Brest", "Le Havre", "Lens", "Lille", "Lorient", "Lyon",
        "Marseille", "Metz", "Monaco", "Nantes", "Nice", "Paris FC", "Paris Saint-Germain",
        "Rennes", "Strasbourg", "Toulouse",
    ]),
    ("Frankreich", "Ligue 2", [
        "Amiens", "Annecy", "Bastia", "Boulogne", "Clermont Foot", "Dunkerque",
        "Grenoble", "Guingamp", "Laval", "Le Mans", "Montpellier", "Nancy", "Pau",
        "Red Star", "Reims", "Rodez", "Saint-Étienne", "Troyes",
    ]),
    ("Italien", "Serie A", [
        "AC Milan", "Atalanta", "Bologna", "Cagliari", "Como", "Cremonese", "Fiorentina",
        "Genoa", "Hellas Verona", "Inter Milan", "Juventus", "Lazio", "Lecce", "Napoli",
        "Parma", "Pisa", "Roma", "Sassuolo", "Torino", "Udinese",
    ]),
    ("Italien", "Serie B", [
        "Avellino", "Bari", "Carrarese", "Catanzaro", "Cesena", "Empoli", "Frosinone",
        "Juve Stabia", "Mantova", "Modena", "Monza", "Padova", "Palermo", "Pescara",
        "Reggiana", "Sampdoria", "Spezia", "Südtirol", "Venezia", "Virtus Entella",
    ]),
]


OVERRIDES = {
    "1. FC Köln": "FC Köln",
    "Darmstadt 98": "Darmstadt",
    "Fortuna Düsseldorf": "Fortuna Dusseldorf",
    "1. FC Nürnberg": "Nürnberg",
    "Preußen Münster": "Preussen Munster",
    "FC Ingolstadt": "Ingolstadt",
    "VfL Osnabrück": "Osnabruck",
    "Rot-Weiss Essen": "Rot-Weiss Essen",
    "VfB Stuttgart II": "Stuttgart II",
    "SSV Ulm": "Ulm",
    "Deportivo de La Coruña": "Deportivo La Coruna",
    "Sporting Gijón": "Sporting Gijon",
    "Queens Park Rangers": "QPR",
    "Paris Saint-Germain": "Paris SG",
    "Saint-Étienne": "Saint-Etienne",
    "Südtirol": "Sudtirol",
}


ID_OVERRIDES = {
    # TheSportsDB search can return women or unrelated teams first for these names.
    # These IDs must be verified by the live provider contract test before changes
    # are accepted.
    "SC Freiburg": "133653",
    "FC St. Pauli": "133813",
    "VfL Wolfsburg": "133655",
    "MSV Duisburg": "133877",
    "Rot-Weiss Essen": "138400",
    "Deportivo de La Coruña": "133816",
    "Sporting Gijón": "133723",
    "Zaragoza": "133737",
    "Paris Saint-Germain": "133714",
    "Saint-Étienne": "133717",
}


FIELDNAMES = [
    "Kalendername",
    "Land",
    "Kategorie",
    "Wettbewerb",
    "API-Provider",
    "API-Key-Provider",
    "ICSId",
    "LogoBytes",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve curated football teams to static TheSportsDB mapping rows.")
    parser.add_argument("--update-lock", action="store_true", help="Accept generated ID changes and rewrite the lock file.")
    args = parser.parse_args()

    rows = []
    lock_rows = []
    unresolved = []
    for country, league, teams in LEAGUES:
        for team in teams:
            resolved = resolve_team(team)
            if not resolved:
                unresolved.append(team)
                continue
            if looks_like_womens_team(resolved):
                unresolved.append(f"{team} resolved to women's team {resolved.get('strTeam')}")
                continue
            rows.append({
                "Kalendername": f"Fussball/{country}/{league}/{team}",
                "Land": country,
                "Kategorie": "Sport",
                "Wettbewerb": league,
                "API-Provider": PROVIDER,
                "API-Key-Provider": API_KEY_ENV,
                "ICSId": resolved["idTeam"],
                "LogoBytes": "",
            })
            lock_rows.append({
                "Team": team,
                "ICSId": resolved["idTeam"],
                "Provider": PROVIDER,
            })
            print(f"{resolved['idTeam']}\t{team}\t{resolved.get('strTeam')}")
            time.sleep(2.1)

    if unresolved:
        print("UNRESOLVED:")
        for team in unresolved:
            print(team)
        return 1

    if LOCK.exists() and not args.update_lock:
        current_lock = read_lock()
        if current_lock != lock_rows:
            print("Provider ID lock changed. Review differences before accepting:")
            print_lock_diff(current_lock, lock_rows)
            print("Run again with --update-lock only after intentionally accepting the changes.")
            return 1

    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    with LOCK.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Team", "ICSId", "Provider"])
        writer.writeheader()
        writer.writerows(lock_rows)
    print(f"Wrote {len(rows)} rows to {OUT}")
    return 0


def resolve_team(team: str) -> dict[str, str] | None:
    if team in ID_OVERRIDES:
        return lookup_team_by_id(ID_OVERRIDES[team])
    query = OVERRIDES.get(team, team)
    url = f"{BASE_URL}/searchteams.php?{urlencode({'t': query})}"
    with urlopen(url, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    teams = payload.get("teams") or []
    if not teams:
        return None
    return teams[0]


def lookup_team_by_id(team_id: str) -> dict[str, str] | None:
    url = f"{BASE_URL}/lookupteam.php?{urlencode({'id': team_id})}"
    with urlopen(url, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    teams = payload.get("teams") or []
    return teams[0] if teams else None


def read_lock() -> list[dict[str, str]]:
    with LOCK.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def print_lock_diff(current: list[dict[str, str]], generated: list[dict[str, str]]) -> None:
    current_by_team = {row["Team"]: row for row in current}
    generated_by_team = {row["Team"]: row for row in generated}
    for team in sorted(set(current_by_team) | set(generated_by_team)):
        old = current_by_team.get(team)
        new = generated_by_team.get(team)
        if old != new:
            print(f"- {team}: {old} -> {new}")


def looks_like_womens_team(team: dict[str, str]) -> bool:
    haystack = " ".join([
        str(team.get("strTeam") or ""),
        str(team.get("strAlternate") or ""),
        str(team.get("strLeague") or ""),
    ]).lower()
    return any(marker in haystack for marker in ["women", "femenino", "female", "frauen"])


if __name__ == "__main__":
    raise SystemExit(main())
