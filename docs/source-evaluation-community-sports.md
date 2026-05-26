# Community Sports Source Registry

Stand: 2026-05-26.

## Kurzfazit

Es gibt nach der aktuellen Recherche keine einzelne kostenlose GitHub-Quelle,
die verlaesslich alle Sportarten der Welt als rechtssichere Live-Event-API
abdeckt. Deshalb fuehrt YourCalendar jetzt ein getrenntes Kandidaten-Register:
Die Quellen sind auffindbar und per API abrufbar, aber noch keine automatisch
aktiven Produktionsimporte.

Das Register steckt in `sports_source_registry.py` und ist lokal abrufbar ueber:

```text
GET /api/source-candidates
GET /api/source-candidates?sport=mma
GET /api/source-candidates?includeRisky=false
```

## Bewertungslogik

| Feld | Bedeutung |
| --- | --- |
| `sourceQuality` | Vertrauensklasse aus dem internen Event-Modell. |
| `riskLevel` | `low`, `medium` oder `high` fuer Lizenz-, Terms-, Uptime- und Scraping-Risiko. |
| `usageDecision` | Empfehlung, ob die Quelle aktiv, nur Prototype, Research oder Paid-Evaluation ist. |
| `supportsLiveEvents` | Ob die Quelle grundsaetzlich fuer kommende Events geeignet wirkt. |
| `requiresApiKey` | Ob ein API-Key oder Account noetig ist. |

## Eingebundene Kandidaten

| Quelle | Sportarten | Typ | Entscheidung |
| --- | --- | --- | --- |
| OpenLigaDB | Fussball, Deutschland | REST API | Bereits aktiver POC fuer deutsche Fussballligen. |
| TheSportsDB | Multi-Sport | REST API | Prototype-Kandidat fuer breite, aber crowd-sourced Coverage. |
| Public ESPN API | Multi-Sport inkl. MMA | Unofficial public REST endpoints | Research-only, weil Datenrechte/Terms ungeprueft sind. |
| sport.db | Fussball, F1, Skiing, Hockey | Open datasets | Offline-Datenkandidat, nicht live. |
| openfootball football.json | Fussball, WM/EM-Daten | GitHub/raw dataset | Offline-Datenkandidat fuer Turnier-Seed-Daten. |
| OpenF1 | Formel 1 | REST API | Prototype-Kandidat fuer Motorsport. |
| Jolpica F1 | Formel 1 | REST API | Prototype-Kandidat fuer Ergast-kompatible F1-Kalenderdaten. |
| UFC Stats API | MMA/UFC | Community REST API | Prototype-only, hohes Scraping-/Rechte-Risiko. |
| Octagon API | MMA/UFC | Community REST API | Metadata-only research, kein voller Eventkalender. |
| UFC stats crawler | MMA/UFC | Scraper | Nicht aktivieren, nur Research-Referenz. |
| MMA API | MMA | Community API project | Research-only bis Setup und Datenrechte geklaert sind. |
| Cricsheet | Cricket | Open dataset | Offline-Datenkandidat, keine Live-Event-API. |
| Jeff Sackmann Tennis Data | Tennis ATP/WTA | GitHub/raw dataset | Historische Daten, nicht live; Non-Commercial beachten. |
| MySportsFeeds API client | US-Sportarten, Golf, Racing | API client fuer Provider | Paid-provider evaluation, nicht freie GitHub-Datenquelle. |
| public-apis sports catalog | Discovery | API-Katalog | Recherche-Checkliste, keine Eventquelle. |
| sportsipy | US-Sportarten, Soccer | Python library | Stats-only research, kein Eventkalender. |

## Kampfsport

Fuer Kampfsport ist die Lage unsicherer als bei Fussball oder F1. Es gibt
GitHub-Projekte fuer UFC/MMA, aber viele davon basieren auf Scraping oder
inoffiziellen Daten. Deshalb sind sie im Register sichtbar, aber mit
`riskLevel: high` markiert. Fuer Produktion waere ein lizenzierter Anbieter oder
eine offizielle Partnerquelle die sauberere Richtung.

Boxing/Kickboxing/BJJ haben in dieser Recherche keine stabile, freie
GitHub-API mit globalem Eventkalender geliefert, die ich mit gesicherter
Grundlage als Produktionsquelle empfehlen kann.

## Naechste technische Schritte

1. Pro Sportart eine kleine Import-Story anlegen: Quelle, Lizenz, Rate Limit,
   Event-Mapping, Testdaten.
2. OpenF1/Jolpica als ersten Nicht-Fussball-Importer spiken, weil die
   Kalenderdaten klarer modellierbar sind als bei Scraping-Quellen.
3. UFC Stats API nur lokal/prototypisch testen und nicht publishen, bis Rechte,
   Rate Limit und Uptime geprueft sind.
4. TheSportsDB als Multi-Sport-Fallback testen, aber nur mit klarer Attribution
   und Cache.
5. Fuer WM/EM-Fussball openfootball als Seed-Datenquelle gegen eine Live-Quelle
   gegenpruefen.
