# YourCalendar Alpha

YourCalendar Alpha ist eine eigenstaendige Proof-of-Concept/Alpha-Version fuer
abonnierbare, automatisch aktualisierte ICS-Kalender. Die Alpha ist bewusst klein
gehalten und nutzt nur Python-Standardbibliothek plus CSV/JSON-Dateien, damit die
fachliche Idee ohne Framework- oder Infrastrukturbindung pruefbar bleibt.

## 1. Ziel und Nutzen

Das System loest ein wiederkehrendes Kalenderproblem: Viele Kalender sollen auf
einer Website auffindbar, abonnierbar und automatisch aktuell sein, ohne dass fuer
jeden neuen Kalender Code geaendert werden muss.

Der zentrale Nutzen:

- Neue Kalender werden ueber eine Mapping-Datei definiert.
- Die Website stellt diese Eintraege automatisch gruppiert dar.
- Nur echte Kalender-Eintraege sind abonnierbar; Gruppeneintraege dienen der Navigation.
- Ein Sync-Skript aktualisiert die ICS-Dateien ueber den passenden Provider.
- Die Provider-Auswahl ist pro Mapping-Eintrag generisch ueber `API-Provider` definiert.
- Die Kalender koennen ueber Google Calendar, Outlook, Apple Calendar oder direkt als ICS abonniert werden.

## 2. Auffaelliger fachlicher Hinweis

Die aktuelle Fussball-Mapping-Datei enthaelt Maennerteams und erlaubt Reserveteams
wie `Real Sociedad B`, `Hoffenheim II` oder `VfB Stuttgart II`.

Frauenteams sind in dieser Mapping-Datei absichtlich ausgeschlossen. Fuer
Frauenteams sollte spaeter eine eigene Untergruppe oder Kategorie definiert werden,
bevor sie ins Mapping kommen. Diese Entscheidung ist fachlich wichtig, weil
Provider-Suchen teilweise Frauenteams vor Maennerteams zurueckliefern.

## 3. Entwicklungsstand der Alpha

Die Alpha enthaelt:

- CSV-Mapping fuer 218 Fussball-Teamkalender.
- Gruppenstruktur `Sport > Fussball > Land > Liga > Team`.
- Statische Provider-ID-Sperrdatei `data/mapping.provider-lock.csv`.
- TheSportsDB-Provider fuer Event-Sync.
- ICS-Renderer.
- HTTP-Website mit responsiver Kachelansicht.
- Scheduler-Loop fuer 6-Stunden-Aktualisierung.
- Funktions-, Contract- und Integrationstests.

Nicht final definiert:

- Die endgueltige Struktur fuer gruppenbezogene Logos.
- Eine separate fachliche Kategorie/Subgruppe fuer Frauenteams.
- Eine produktive Deployment-Strategie fuer HTTPS, Domain und Cron-Service.

## 4. Projektstruktur

```text
alpha/
  data/
    mapping.csv
    mapping.provider-lock.csv
    group_logo_settings.csv
  public/
    ics/
  tests/
  tools/
    manual_mapping/
      builder.py
      config.py
      csv_table.py
      provider_lock_diff.py
      team_source_loader.py
      thesportsdb_team_resolver.py
    resolve_manual_team_ids.py
  yourcalendar_alpha/
    calendar/
      file_naming.py
      subscription_links.py
      tree_builder.py
    config/
      settings.py
    domain/
      calendar_entry.py
      calendar_event.py
      calendar_tree_node.py
      group_logo.py
      sync_result.py
    ics/
      line_formatter.py
      parser.py
      renderer.py
      sequence.py
    mapping/
      loader.py
    models.py
    providers/
      base.py
      errors.py
      registry.py
      thesportsdb_datetime.py
      thesportsdb_event_mapper.py
      thesportsdb_provider.py
    sync/
      change_counter.py
      report.py
      service.py
    web/
      static/
        site.css
        site.js
      http_handler.py
      page_renderer.py
    web_app.py
    update_calendars.py
    scheduler_loop.py
  settings.json
  README.md
```

## 5. Start und Betrieb

Website starten:

```powershell
cd alpha
python -m yourcalendar_alpha.web_app
```

Danach ist die Website lokal erreichbar:

```text
http://127.0.0.1:8080
```

Kalender einmalig aktualisieren:

```powershell
cd alpha
python -m yourcalendar_alpha.update_calendars
```

6-Stunden-Loop starten:

```powershell
cd alpha
python -m yourcalendar_alpha.scheduler_loop
```

Cron-Beispiel fuer Unix-Systeme:

```cron
0 */6 * * * cd /path/to/alpha && python -m yourcalendar_alpha.update_calendars
```

Die generierten ICS-Dateien liegen in:

```text
public/ics/
```

## 6. Funktionsweise

### 6.1 Mapping laden

`yourcalendar_alpha.mapping.load_mapping()` liest `data/mapping.csv`, validiert
Pflichtspalten, prueft leere Pflichtwerte und verhindert doppelte `ICSId`-Werte.

### 6.2 Website darstellen

`yourcalendar_alpha.page_renderer.render_home_page()` liest Mapping und
GroupLogoSettings, baut daraus eine Baumstruktur und rendert daraus HTML.

Die Website-Verantwortung ist in der Alpha bewusst getrennt:

- `domain/`: einzelne Datenklassen fuer Kalender, Events, Gruppen und Sync-Ergebnisse.
- `models.py`: Re-Export der Datenklassen fuer bequeme Imports.
- `calendar/`: Baumaufbau, Zaehlung, Sortierung, Dateinamen und abonnierbare Kalender-URLs.
- `mapping/`: CSV-Loader und Mapping-/GroupLogoSettings-Validierung.
- `web/page_renderer.py`: HTML-Rendering.
- `web/http_handler.py`: HTTP-Routen fuer HTML, ICS und statische Assets.
- `web_app.py`: Serverstart und Server-Factory.
- `web/static/site.css`: visuelles Design.
- `web/static/site.js`: Browser-Interaktion, Darkmode und Tree-Verhalten.

Weitere Verantwortlichkeiten sind ebenfalls getrennt:

- `ics/`: ICS-Ausgabe, bestehende Event-Sequenzen und Formatierungsregeln.
- `providers/`: generischer Provider-Vertrag, Fehler, Registrierung und konkrete TheSportsDB-Anbindung.
- `sync/`: Synchronisationsfluss, Change-Zaehler und CLI-Ausgabe.
- `config/`: Settings laden und Pfade aufloesen.

Die Darstellung folgt dieser Regel:

```text
Kategorie > Kalendername-Pfad
```

Beispiel:

```text
Kategorie: Sport
Kalendername: Fussball/Deutschland/1. Bundesliga/FC Augsburg
```

Die Website zeigt daraus:

```text
Sport
  Fussball
  Fussball / Deutschland
  Fussball / Deutschland / 1. Bundesliga
    FC Augsburg
```

Alle Pfadsegmente vor dem letzten Segment sind GroupEntries. Nur das letzte
Segment ist ein KalenderEntry und abonnierbar.

### 6.3 Kalender abonnieren

Jede Kalender-Kachel erzeugt vier Ziel-Links:

- Google Calendar: Web-Link mit `cid=<ics-url>`.
- Outlook Web Calendar: Web-Link mit `url=<ics-url>`.
- Apple Calendar: `webcal://...`.
- ICS-Datei: direkter Download/Abruf.

Wichtig: Fuer echte externe Abos muss `public_base_url` in `settings.json` eine
oeffentlich erreichbare HTTPS-URL sein. Lokale URLs wie `127.0.0.1` koennen von
Google oder Outlook nicht extern abgerufen werden.

### 6.4 Events synchronisieren

`yourcalendar_alpha.sync.sync_all()` liest alle Mapping-Eintraege, sucht den
passenden Provider ueber `API-Provider`, ruft Events ab und schreibt je Kalender
eine ICS-Datei.

Der Ablauf pro Eintrag:

1. Provider aus Registry lesen.
2. Provider-Events fuer die `ICSId` holen.
3. Events in generische `CalendarEvent`-Objekte abbilden.
4. Bestehende ICS-Datei auslesen.
5. Erstellte, aktualisierte und geloeschte Events zaehlen.
6. Neue ICS-Datei schreiben.

## 7. Mapping ausfuehrlich erklaert

Die zentrale Datei ist:

```text
data/mapping.csv
```

Jede Zeile ist genau ein abonnierbarer Kalender.

### 7.1 Spalten

| Spalte | Typ | Pflicht | Bedeutung |
|---|---:|---:|---|
| `Kalendername` | string | ja | Pfad fuer Gruppierung und Anzeigename. Letztes Segment ist der Kalender. |
| `Land` | string | ja | Fachliches Land des Kalenders. Wird in Kacheln angezeigt. |
| `Kategorie` | string | ja | Oberste Website-Gruppe, z. B. `Sport`. |
| `Wettbewerb` | string | ja | Liga/Wettbewerb, z. B. `1. Bundesliga`. |
| `API-Provider` | string | ja | Provider-Schluessel, z. B. `TheSportsDB`. |
| `API-Key-Provider` | string | nein | Name der Umgebungsvariable fuer Provider-API-Key. |
| `ICSId` | string | ja | Provider-ID und lokale ICS-Datei-ID. |
| `LogoBytes` | bytes/base64 | nein | Base64-kodiertes Logo. Leer ist erlaubt. |
| `SubGroupOrder` | integer | ja | Reihenfolge der Kalenderkacheln innerhalb derselben Untergruppe. |

### 7.2 Kalendername-Regel

`Kalendername` ist ein Slash-getrennter Pfad:

```text
GroupEntry/GroupEntry/KalenderEntry
```

Beispiele:

```csv
Fussball/Deutschland/1. Bundesliga/FC Augsburg
Fussball/England/Premier League/Arsenal
Fussball/Spanien/La Liga 2/Real Sociedad B
```

Regeln:

- Slashes duerfen mehrere Ebenen bilden.
- Das letzte Segment ist immer der abonnierbare Kalender.
- Vorherige Segmente sind nicht abonnierbare Gruppen.
- `Kategorie` steht oberhalb dieses Pfads.

### 7.3 Neuen Kalender hinzufuegen

Eine kontextfremde Person kann einen neuen Eintrag so hinzufuegen:

1. Pruefen, ob der passende Provider bereits existiert.
2. Provider-spezifische ID ermitteln. Fuer `TheSportsDB` ist das aktuell `idTeam`.
3. Neue Zeile in `data/football_team_source.csv` ergaenzen oder eine vergleichbare Source-Datei pflegen.
4. `SubGroupOrder` innerhalb derselben Liga/Untergruppe eindeutig setzen.
5. `data/mapping.provider-lock.csv` um Team, ICSId und Provider erweitern.
6. `python tools/resolve_manual_team_ids.py` ausfuehren, um `data/mapping.csv` neu zu erstellen.
7. Bei Bedarf passenden Gruppenpfad in `data/group_logo_settings.csv` ergaenzen und `groupOrder` setzen.
8. Tests ausfuehren.

Beispiel:

```csv
Kalendername,Land,Kategorie,Wettbewerb,API-Provider,API-Key-Provider,ICSId,LogoBytes,SubGroupOrder
Fussball/Deutschland/1. Bundesliga/FC Augsburg,Deutschland,Sport,1. Bundesliga,TheSportsDB,THESPORTSDB_API_KEY,133652,,1
```

### 7.4 Fehler, die vermieden werden muessen

- `ICSId` doppelt vergeben.
- `API-Provider` schreiben, fuer den kein Provider registriert ist.
- Frauenteam-ID in das aktuelle Maennerteam-Mapping aufnehmen.
- Provider-ID eines Reserve- oder Fremdteams versehentlich fuer ein erstes Team nutzen.
- `public_base_url` lokal lassen, wenn externe Abos produktiv funktionieren sollen.

## 8. Mapping-ID-Pflege und Lockfile

`tools/resolve_manual_team_ids.py` ist ein einmaliges Pflege- und
Verifikationsskript. Es enthaelt eine kuratierte Teamliste und loest diese gegen
TheSportsDB-IDs auf.

Wichtig:

- Das Skript nutzt `data/football_team_source.csv` als vollstaendige fachliche Team-Quelle.
- Es nutzt nicht den auf 10 Teams begrenzten TheSportsDB-Liga-Endpunkt.
- Die Team-Auswahl ist kuratiert und enthaelt alle aktuell gewuenschten Vereine je Liga.
- TheSportsDB wird nur genutzt, um Provider-IDs zu ermitteln oder zu verifizieren.
- Beim erneuten Ausfuehren wird gegen `mapping.provider-lock.csv` verglichen.
- Wenn sich IDs aendern, schlaegt das Skript fehl.
- Nur mit `--update-lock` werden geaenderte IDs bewusst akzeptiert.
- `SubGroupOrder` wird aus der Source-Datei in `mapping.csv` uebernommen und von der Website zur Sortierung der Kalenderkacheln genutzt.

Ausfuehren:

```powershell
cd alpha
python tools/resolve_manual_team_ids.py
```

Provider-IDs live neu verifizieren oder ermitteln:

```powershell
cd alpha
python tools/resolve_manual_team_ids.py --refresh-provider
```

Geaenderte IDs bewusst akzeptieren:

```powershell
cd alpha
python tools/resolve_manual_team_ids.py --refresh-provider --update-lock
```

## 9. GroupLogoSettings

Die Datei ist:

```text
data/group_logo_settings.csv
```

Aktuelles Format:

| Spalte | Bedeutung |
|---|---|
| `Kategorie` | Kategorie, z. B. `Sport`. |
| `GroupPath` | Pfad innerhalb der Kategorie, z. B. `Fussball/Deutschland/1. Bundesliga`. |
| `LogoBytes` | Base64-kodierte Bilddaten. |
| `groupOrder` | Integer fuer die Reihenfolge von Gruppenkacheln innerhalb derselben Ebene. |

`groupOrder` sortiert nur GroupEntries. KalenderEntries innerhalb einer Gruppe
werden weiterhin ueber `SubGroupOrder` aus `data/mapping.csv` sortiert.

Die endgueltige fachliche Definition dieser Datei ist noch offen. Die Alpha kann
sie bereits laden und fuer GroupEntries nutzen.

## 10. Provider: aktueller Stand

Aktuell implementiert:

```text
TheSportsDB
```

Provider-Schluessel im Mapping:

```csv
API-Provider
TheSportsDB
```

TheSportsDB-Regel:

- `ICSId` wird als `idTeam` interpretiert.
- Events kommen aus `eventsnext.php?id=<idTeam>` und `eventslast.php?id=<idTeam>`.
- API-Key kommt aus der Umgebungsvariable in `API-Key-Provider`.
- Wenn kein Key vorhanden ist, wird der freie Beispiel-Key aus `settings.json` verwendet.

## 11. Neuen Provider implementieren

Ein neuer Provider muss den generischen Vertrag in
`yourcalendar_alpha/providers/base.py` erfuellen:

```python
class CalendarProvider:
    name = ""

    def fetch_events(self, entry: CalendarEntry) -> list[CalendarEvent]:
        raise NotImplementedError
```

### 11.1 Vorgehen

1. Neue Provider-Klasse in `yourcalendar_alpha/providers/` anlegen.
2. `name` auf den Mapping-Schluessel setzen, z. B. `ExampleSports`.
3. `fetch_events(entry)` implementieren.
4. Provider-spezifische API-ID aus `entry.ics_id` lesen.
5. Optionalen API-Key ueber `entry.api_key_provider` aus Umgebungsvariablen lesen.
6. Providerdaten in `CalendarEvent` umwandeln.
7. Provider in `yourcalendar_alpha/providers/registry.py` registrieren.
8. Unit-Test fuer Provider-Mapping ergaenzen.
9. Integrationstest fuer Sync mit Fake-Provider oder gemocktem HTTP ergaenzen.
10. Mapping-Zeile mit `API-Provider=<ProviderName>` ergaenzen.

### 11.2 CalendarEvent-Felder

Jeder Provider muss Events in dieses generische Format bringen:

| Feld | Bedeutung |
|---|---|
| `uid` | Stabile Event-ID. Muss ueber Updates hinweg gleich bleiben. |
| `title` | Kalenderevent-Titel. |
| `starts_at` | Startzeit als timezone-aware `datetime`. |
| `ends_at` | Endzeit als timezone-aware `datetime`. |
| `location` | Ort/Stadion/Adresse. |
| `description` | Detailtext. |
| `source_hash` | Hash der Provider-Rohdaten fuer Update-Erkennung. |

### 11.3 Provider-Qualitaetskriterien

Ein Provider ist erst sinnvoll integriert, wenn:

- fehlende API-Keys sauber behandelt werden,
- fehlende oder unvollstaendige Providerdaten nicht abstuerzen,
- Event-UIDs stabil sind,
- geaenderte Events einen anderen `source_hash` erzeugen,
- geloeschte Events aus der naechsten ICS-Version verschwinden,
- Tests Providerdaten ohne echten Netzwerkzugriff simulieren koennen.

## 12. Tests und Qualitaetssicherung

Normale Tests:

```powershell
cd alpha
python -m unittest discover -s tests -p "test_*.py"
```

Syntax-/Import-Pruefung:

```powershell
cd alpha
python -m compileall yourcalendar_alpha tests tools
```

Live-Provider-Verifikation:

```powershell
cd alpha
$env:RUN_LIVE_PROVIDER_TESTS='1'
python -m unittest tests.test_mapping_contract
```

Hinweis: Der Live-Test fragt TheSportsDB ab und ist absichtlich langsam, damit
Rate-Limits weniger wahrscheinlich sind.

### 12.1 Testarten

- Funktionstests:
  - Mapping laden und validieren.
  - Providerdaten in `CalendarEvent` abbilden.
  - ICS-Dateien schreiben und Update-Zaehler pruefen.
  - Web-Renderer-Struktur pruefen.

- Integrationstests:
  - HTTP-Server rendert Mapping-Eintraege.
  - HTTP-Server liefert ICS-Dateien mit `text/calendar`.
  - Sync verarbeitet Mapping plus Fake-Provider bis zur ICS-Datei.

- Contract-Tests:
  - Erwartete Ligen und Teamzahlen.
  - Provider-Konfiguration je Mapping-Zeile.
  - Eindeutige `ICSId`.
  - Lockfile-Konsistenz.
  - Optionale Live-Pruefung gegen TheSportsDB.

## 13. Clean-Code-Checkliste fuer diese Alpha

Vor Abschluss eines Aenderungspakets pruefen:

- Sind Mapping- und Provider-Verantwortung getrennt?
- Wird keine Provider-ID geraten?
- Bleibt die Website generisch und liest nur Mapping/Settings?
- Sind Gruppeneintraege nicht abonnierbar?
- Sind Kalender-Eintraege abonnierbar?
- Gibt es Tests fuer neue Mapping-Regeln oder Providerlogik?
- Sind generierte/temporare Dateien nicht versehentlich Teil der Logik?
- Sind Unsicherheiten dokumentiert statt im Code versteckt?

## 14. Bekannte Annahmen

- `ICSId` ist aktuell gleichzeitig Provider-ID und lokaler ICS-Dateiname.
- Fuer TheSportsDB bedeutet `ICSId`: `idTeam`.
- Der freie TheSportsDB-Key `123` ist nur fuer Alpha-/Testzwecke geeignet.
- Externe Kalenderabos brauchen eine oeffentlich erreichbare URL.
- Die Teamlisten wurden fuer die Alpha kuratiert; Ligen koennen sich saisonal aendern.
