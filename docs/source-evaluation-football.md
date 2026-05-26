# Source Evaluation: Football Data Providers

Stand: 2026-05-26

## Ziel

Issue #11 verlangt einen Vergleich von Fussball-Datenanbietern, damit
YourCalendar entscheiden kann, ob Sportkalender mit akzeptabler Qualitaet und
legaler Nutzung moeglich sind.

Diese Recherche ist keine Rechtsberatung. Preise, Limits und Nutzungsrechte
koennen sich aendern; vor einem produktiven Vertrag muessen die jeweiligen
Terms und der konkrete Tarif erneut geprueft werden.

## Kurzentscheidung

Fussball bleibt fuer den MVP ein attraktiver, aber risikoreicher Datenstrom.
OpenLigaDB ist weiter gut fuer POC-Feeds, sollte aber nicht als garantierter
Produktionsprovider behandelt werden.

Fuer einen kleinen MVP-Spike mit Top-Ligen ist football-data.org die
naheliegendste Low-Cost-Option: begrenzte, klare Fussball-Coverage, einfache
REST-API, Attribution geregelt und Free/Paid-Stufen sichtbar. Fuer breitere
globale Coverage ist API-FOOTBALL/API-SPORTS der guenstigere bezahlte Spike.
Wenn Fussball ein Kernprodukt wird, sollte Sportmonks als spaeterer
Produktionskandidat geprueft werden, weil Coverage, API-Struktur und
Live-Datenanspruch staerker wirken, aber die Kosten hoeher sind.

TheSportsDB bleibt nuetzlich fuer Prototypen und Multi-Sport-Metadaten, ist
aber als primaerer Produktionsprovider fuer Fussballkalender zu unsicher, bis
ein bezahlter Plan, Nutzungsrechte und Coverage konkret getestet sind.

## Entscheidungsmatrix

| Anbieter | Liga-Coverage | Kosten / Limits | Nutzungsrechte | Update-Latenz | API-Stabilitaet | Empfehlung |
| --- | --- | --- | --- | --- | --- | --- |
| OpenLigaDB | Stark fuer deutsche Ligen/Community-Ligen; nicht als globale Profi-Coverage bewertet | Kostenlos, kein API-Key fuer Abruf | Daten laut Anbieter unter ODbL; Community-Pflege | Community-abhaengig, kein SLA gefunden | Simple JSON-API, bisher im POC nutzbar | Nur POC / Fallback, nicht als Produktions-SLA |
| football-data.org | Free Tier umfasst 12 Wettbewerbe inkl. Topligen, World Cup und European Championships; Paid bis 100 Wettbewerbe | Free 10 Calls/min; Paid u.a. 12 EUR, 29 EUR, 49 EUR, 99 EUR, 199 EUR pro Monat je nach Paket | Registrierung/Terms, Attribution erforderlich; Logos/Fotos separat klaeren; keine Garantie fuer Datenrichtigkeit/Verfuegbarkeit | Free: Scores/Schedules delayed; Live-Scores nur in bezahlten Plaenen | Dokumentierte REST-API und klare Rate Limits | MVP-Spike fuer begrenzte Top-Ligen |
| TheSportsDB | Breite Multi-Sport-Datenbank mit Soccer-Leagues weltweit; Coverage crowd-sourced | Free 30 Requests/min; Premium ab 9 USD/Monat, Business 20 USD/Monat laut Pricing | Offizielle Endpoints erlaubt; Free nicht fuer App-Store-Apps; Paid braucht Quellenhinweis; Drittinhalte/Logos rechtlich klaeren | Paid nennt 2-Minuten-Livescore fuer Soccer/NFL/NBA/MLB/NHL; Free-Limits unklar | V1 alt/einfach; V2 moderner, aber Premium-only | Prototyp / Metadaten, nicht primaerer MVP-Provider |
| API-FOOTBALL / API-SPORTS | Sehr breite Wettbewerbslisten, inkl. Welt-/Kontinentalturniere und Qualifikationen | Free 100 Requests/Tag; Paid ab 19.00/Monat laut Pricing-Seite, Waehrung im Textauszug nicht eindeutig; hohe Tageskontingente | Paid gibt alle Endpoints/Competitions; Logos/Images nur identifizierend, Rechte muessen vom Nutzer geklaert werden; Datenverfuegbarkeit nicht garantiert | Live-/Sportdatenanbieter, aber konkrete Latenz/SLA fuer unseren Tarif nicht gesichert | Umfangreiche REST-Endpunkte, Quoten und Coverage ueber API/Website sichtbar | Bezahlter MVP-Spike fuer breite Coverage |
| Sportmonks | Sehr breite Football-Coverage, aktuell ueber 2.200/2.300 Ligen je nach offizieller Seite; flexible League-Auswahl je Plan | Starter 29 EUR/Monat fuer 5 Ligen, Growth 99 EUR/Monat fuer 30, Pro 249 EUR/Monat fuer 120; Enterprise custom | Nutzung fuer Apps/Websites moeglich, Reselling verboten; pro Domain; Logos/Fotos separat klaeren; keine Vollstaendigkeitsgarantie | Anbieter nennt Realtime/Live-Daten und haeufig <15 Sekunden fuer Scores, aber Terms schliessen 100%-Garantie aus | Moderne API mit Filtern/Includes, Trial/Free-Testoptionen | Spaeterer Produktionskandidat, wenn Fussball Kernprodukt wird |

## Bewertung je MVP-Szenario

### Szenario A: Low-Cost-Topligen

Nutzung: Bundesliga, Champions League, EM/WM, wenige Topligen.

Empfehlung: football-data.org als erster API-Spike. Die Free-Coverage enthaelt
bereits grosse Wettbewerbe, aber Live-Daten und mehr Wettbewerbe erfordern
Paid-Tiers. Keine Logos nutzen, Attribution anzeigen und Import-Monitoring
aktiv lassen.

### Szenario B: Breite Fussball-Coverage

Nutzung: viele europaeische und internationale Ligen, Turniere, Qualifikation.

Empfehlung: API-FOOTBALL/API-SPORTS als guenstiger bezahlter Spike. Vor einer
Produktionsentscheidung muessen Datenqualitaet, Team-/League-IDs, Zeitzonen,
Stornos, Verschiebungen und Nutzungsrechte an 2-3 echten Ligen getestet werden.

### Szenario C: Fussball als Kernprodukt

Nutzung: viele Ligen, bessere Live-Qualitaet, planbarer Betrieb.

Empfehlung: Sportmonks evaluieren. Der Anbieter wirkt geeigneter fuer ein
professionelles Fussballprodukt, ist aber teurer und braucht eine klare
Budget-/Lizenzentscheidung. Erst nach Trial gegen unsere eigenen
Datenqualitaetsregeln entscheiden.

### Szenario D: Multi-Sport-Discovery

Nutzung: Nutzer sollen Sportarten/Kategorien entdecken, aber Fussball ist nicht
alleiniger Datenkern.

Empfehlung: TheSportsDB nur als Prototyp- oder Metadatenquelle pruefen. Fuer
Produktionskalender je Sportart weiterhin separate Rechte-/Provider-Spikes
planen, besonders fuer Kampfsport, weil Veranstaltungsrechte und offizielle
Schedules anders gelagert sind als bei Ligen.

## Nicht fuer den MVP empfehlen

- Live-Ergebnisprodukte oder Push-Alerts: Das ist kein Kalenderkern und zieht
  SLA-, Latenz- und Support-Erwartungen hoch.
- Logos, Clubwappen, Spielerbilder oder Highlight-Videos ohne Rechtepruefung.
- Einen kostenlosen Community-Provider als einzige Produktionsquelle.
- Direkte Google-/Outlook-API-Syncs nur wegen Sportdaten; ICS-first bleibt
  einfacher und risikoaermer.

## Integrations-Checkliste vor Code-Anbindung

1. Konkreten Tarif und erlaubte Nutzung dokumentieren.
2. API-Key nur ueber Environment/Secrets konfigurieren.
3. Attribution/Quellenhinweise im Kalenderfeed und UI anzeigen.
4. Keine Logos oder Bilder verwenden, bis Rechte geklaert sind.
5. Testdaten fuer mindestens Bundesliga, KSC/2. Bundesliga, Champions League,
   World Cup und European Championship importieren.
6. Zeitzone, verschobene Spiele, abgesagte Spiele und leere Antworten pruefen.
7. Import-Monitoring mit Warnung bei leeren Ergebnissen, alten Daten und
   geaenderten Kickoff-Zeiten aktivieren.
8. Caching/Fallback nutzen, damit bestehende ICS-Feeds bei Providerfehlern
   nicht leer werden.

## Quellen

- OpenLigaDB: https://beta.openligadb.de/
- football-data.org Pricing: https://www.football-data.org/pricing
- football-data.org Coverage: https://www.football-data.org/coverage
- football-data.org Policies: https://docs.football-data.org/general/v4/policies.html
- football-data.org Terms: https://www.football-data.org/client/register
- TheSportsDB Pricing: https://www.thesportsdb.com/pricing
- TheSportsDB Documentation: https://www.thesportsdb.com/documentation
- TheSportsDB Terms: https://www.thesportsdb.com/docs_terms_of_use.php
- API-FOOTBALL/API-SPORTS Football API: https://api-sports.io/sports/football
- API-SPORTS Terms: https://api-sports.io/terms
- Sportmonks Football API: https://www.sportmonks.com/football-api/
- Sportmonks Pricing: https://www.sportmonks.com/football-api/plans-pricing/
- Sportmonks Terms: https://www.sportmonks.com/terms-of-service/

## Naechste Empfehlung

Kurzfristig sollte YourCalendar einen kleinen football-data.org-Spike bauen,
aber ihn hinter Source-Konfiguration und Monitoring halten. Parallel kann ein
API-FOOTBALL- oder Sportmonks-Trial vorbereitet werden, sobald klar ist, ob
Fussball nach dem Feiertags-/Basis-MVP wirklich priorisiert wird.
