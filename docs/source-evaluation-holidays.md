# Source Evaluation: Public Holidays

Stand: 2026-05-22

## Ziel

Issue #10 verlangt eine erste rechtlich und technisch verlaesslichere MVP-Quelle
als freie Fussballdaten. Dieser Spike prueft Feiertage als risikoarmen
Kalender-Use-Case.

## Kurzentscheidung

Nager.Date ist als technischer PoC geeignet, aber noch keine finale
Produktionsentscheidung.

Die Quelle ist fuer den naechsten MVP-Schritt nuetzlich, weil sie ohne OAuth,
ohne Nutzerkonto und mit stabiler JSON-Struktur echte Kalendertermine liefert.
Sie ist aber keine amtliche Regierungsquelle. Vor produktiver oder kommerzieller
Nutzung muessen Nutzungsbedingungen, Quellenangabe, regionale Abdeckung und
Fallback-Verhalten final geprueft werden.

## Bewertete Quellen

| Quelle | Status | Staerken | Risiken | Entscheidung |
| --- | --- | --- | --- | --- |
| Nager.Date Holiday API | Umgesetzt als PoC | JSON, keine Auth, mehr als 100 Laender, einfache Jahresabfrage | Keine amtliche Quelle, Terms/SLA muessen produktiv geprueft werden | MVP-PoC |
| Deutscher Bundestag DIP | Bewertet | Offizielle Parlamentsdaten, klare Nutzungsbedingungen fuer API-Daten mit Quellenangabe | API-Schluessel erforderlich, fachlich eher Politik-Feed als allgemeiner Feiertagskalender | Spaeterer Politik-Spike |
| OpenLigaDB | Vorhandener POC | Gute freie Fussball-Testquelle | Kein garantierter Realtime-SLA, rechtliche/produktive Sport-Coverage nicht final | Nicht erste sichere MVP-Quelle |

## PoC-Umsetzung

Der Importer nutzt:

```text
GET https://date.nager.at/api/v3/PublicHolidays/{year}/{countryCode}
```

Die Antwort wird in `CalendarEvent` normalisiert:

- `category`: `holidays`
- `source`: `Nager.Date`
- `source_quality`: `community`
- `all_day`: `true`
- `uid`: stabil aus Land, Datum und lokalem Namen
- regionale Filterung ueber Subdivision-Codes wie `DE-BW`

Beispiel:

```bash
python3 yourcalendar_poc.py \
  --source nager-holidays \
  --holiday-year 2026 \
  --holiday-country DE \
  --max-events 10 \
  --calendar-name "German Public Holidays" \
  --show-events
```

Der Webserver stellt zusaetzlich einen veroeffentlichten Feed bereit:

```text
/feeds/holidays-germany.ics
```

## Quellenhinweise

- Nager.Date dokumentiert den Endpoint `PublicHolidays/{Year}/{CountryCode}`,
  JSON-Felder wie `date`, `localName`, `global`, `counties` und `types` sowie
  die moeglichen Typwerte `Public`, `Bank`, `School`, `Authorities`,
  `Optional`, `Observance`.
- Nager.Date beschreibt sich als Open-Source-Projekt und verweist auf eigene
  Terms of Service. Diese Terms sind vor Production-Einsatz noch gesondert zu
  pruefen.
- Die DIP-Nutzungsbedingungen des Deutschen Bundestags/Bundesrats sagen, dass
  API-Daten unentgeltlich bereitgestellt werden und maschinenlesbare API-Daten
  umfassend weiterverarbeitet werden duerfen, aber mit Quellenangabe und
  kenntlich gemachten Veraenderungen.

## Offene Risiken

- Feiertage koennen regional unterschiedlich gelten; das UI muss Region/Ort
  spaeter klar auswaehlbar machen.
- Nager.Date ist nicht amtlich. Fuer ein finales Produkt kann ein amtlicher oder
  vertraglich abgesicherter Anbieter sinnvoller sein.
- Der aktuelle PoC speichert keine Provider-SLA, keinen Health-Status und keine
  Retention-Regeln pro Quelle.
- Wenn DIP spaeter genutzt wird, braucht der Betrieb einen API-Schluessel und
  eine saubere Quellenangabe `Deutscher Bundestag/Bundesrat - DIP`.

## Fazit

Feiertage sind als erster MVP-Datenstrom sinnvoller als Fussball, weil sie
alltagstauglich, kalendernativ und technisch weniger zeitkritisch sind. Der
naechste sinnvolle Schritt ist Import-Monitoring (#12), damit fuer diese und
spaetere Quellen sichtbar wird, wann Daten leer, veraltet oder fehlerhaft sind.
