# Coding Guide

Stand: 2026-06-01.

## Ziel

Dieser Guide beschreibt allgemeine Coding-Prinzipien fuer wartbare Software.
Er ist bewusst generisch formuliert, damit er fuer Backend, Frontend, Tests,
Skripte und Dokumentation gleichermassen nutzbar ist. Projektspezifische Regeln
stehen am Ende und duerfen die allgemeinen Regeln nur konkretisieren, nicht
verwaessern.

Guter Code ist nicht nur Code, der heute funktioniert. Guter Code ist Code, der
spaeter verstanden, geaendert, getestet und geloescht werden kann, ohne dass das
Team raten muss. Deshalb bewertet dieser Guide Lesbarkeit, klare Verantwortung,
kleine Einheiten, explizite Fehlerbehandlung und nachvollziehbare Tests hoeher
als besonders clevere Abkuerzungen.

## Grundprinzipien

### Lesbarkeit vor Cleverness

Code wird deutlich haeufiger gelesen als geschrieben. Eine Loesung ist nur dann
gut, wenn eine andere Person den Zweck, die Annahmen und die Grenzen schnell
erkennen kann. Bevorzuge deshalb klare Namen, einfache Kontrollfluesse und
direkte Datenstrukturen.

Vermeide Tricks, die nur mit Spezialwissen verstaendlich sind. Wenn eine
komplexe Loesung wirklich noetig ist, kapsle sie hinter einer gut benannten
Funktion und dokumentiere den Grund kurz.

### Single Responsibility

Eine Funktion, Klasse oder Komponente sollte genau eine fachlich erkennbare
Aufgabe haben. Das bedeutet nicht, dass jede Funktion winzig sein muss. Es
bedeutet, dass die Funktion einen klaren Grund hat, sich zu aendern.

Wenn eine Funktion gleichzeitig Daten laedt, validiert, transformiert,
persistiert und eine HTTP-Antwort erzeugt, sind mehrere Verantwortlichkeiten
vermischt. Teile solche Funktionen entlang fachlicher Schritte auf:

- Eingabe lesen und validieren.
- Fachliche Entscheidung treffen.
- Daten transformieren.
- Ergebnis speichern oder ausgeben.
- Fehler in eine Antwort uebersetzen.

### Explizite Annahmen

Jeder Code enthaelt Annahmen: ueber Datenformate, Zeitzonen, externe APIs,
Sortierung, leere Werte oder Berechtigungen. Kritische Annahmen muessen im Code,
in Tests oder in Dokumentation sichtbar sein.

Wenn eine Annahme falsch werden kann, soll der Code entweder robust damit
umgehen oder bewusst fehlschlagen. Stilles Weitermachen mit erfundenen Defaults
ist riskant, wenn dadurch falsche Daten als korrekt erscheinen.

### Kleine, reversible Aenderungen

Arbeite in Aenderungen, die einzeln verstanden und zurueckgenommen werden
koennen. Eine gute Aenderung hat einen klaren Zweck. Sie vermischt nicht
Refactoring, Feature-Logik, Formatierung und Abhaengigkeitsupdates ohne Not.

Wenn ein Refactoring fuer ein Feature noetig ist, halte es eng am betroffenen
Code. Breite Umbauten brauchen einen eigenen Grund, eigene Tests und eine
bewusste Review.

### Verhalten ist Vertrag

Alles, was andere Teile des Systems nutzen, ist ein Vertrag:

- oeffentliche Funktionen und Klassen,
- API-Antworten,
- Datenbank- oder Dateiformate,
- URLs und Query-Parameter,
- CLI-Argumente,
- UI-Interaktionen,
- Fehlermeldungen, auf die Tests oder Nutzer reagieren.

Solche Vertraege duerfen nicht nebenbei geaendert werden. Wenn eine Aenderung
noetig ist, dokumentiere sie und sichere sie mit Tests ab.

## Namen und Struktur

### Gute Namen

Namen sollen die fachliche Bedeutung ausdruecken, nicht nur den technischen Typ.
`events_for_calendar` ist hilfreicher als `data`; `cache_path` ist hilfreicher
als `p`.

Vermeide Abkuerzungen, wenn sie nicht allgemein bekannt sind. Ein laengerer,
praeziser Name ist besser als ein kurzer Name, der Kontextwissen verlangt.

Gute Namen beantworten:

- Was ist das?
- Wofuer wird es genutzt?
- In welchem Zustand befindet es sich?
- Ist es roh, validiert, normalisiert, gespeichert oder angezeigt?

### Funktionen

Eine Funktion sollte einen Namen haben, der ihren Effekt beschreibt. Wenn der
Name nur mit "and" sinnvoll waere, macht die Funktion wahrscheinlich zu viel.

Beispiele fuer klare Funktionsarten:

- `load_*`: liest Daten ohne fachliche Veraenderung.
- `parse_*`: wandelt Rohdaten in strukturierte Daten um.
- `normalize_*`: bringt Daten in ein einheitliches Format.
- `validate_*`: prueft Regeln und meldet Fehler.
- `build_*`: erzeugt ein neues Objekt oder Payload.
- `save_*` oder `write_*`: persistiert Daten.
- `render_*`: erzeugt eine Darstellung fuer UI, Text oder Datei.

Funktionen sollten Seiteneffekte sichtbar machen. Eine Funktion mit Namen
`format_event()` sollte nicht nebenbei eine Datei schreiben oder Netzwerkzugriff
ausloesen.

### Module und Dateien

Module sollten nach fachlicher Verantwortung organisiert sein. Vermeide Dateien,
die zur Sammelstelle fuer alles werden. Wenn eine Datei stark waechst, pruefe,
ob es erkennbare Gruppen gibt: Modell, Datenzugriff, API-Payloads, Rendering,
Importlogik, Tests.

Eine neue Datei ist sinnvoll, wenn sie eine klare Grenze schafft. Eine neue
Datei ist nicht sinnvoll, wenn sie nur eine einzelne Hilfsfunktion versteckt,
die nur an einer Stelle gebraucht wird.

## Daten und Seiteneffekte

### Datenvalidierung

Validiere Daten an Systemgrenzen:

- Benutzereingaben,
- API-Requests,
- Dateien,
- Umgebungsvariablen,
- Antworten externer Dienste.

Innerhalb des Systems sollten Daten moeglichst in einer normalisierten Form
weitergereicht werden. So muss nicht jede Funktion dieselben Sonderfaelle
erneut behandeln.

### Fehlerbehandlung

Fehler sollen dort behandelt werden, wo eine sinnvolle Entscheidung moeglich
ist. Tiefe Hilfsfunktionen sollten Fehler nicht verschlucken, wenn sie nicht
wissen, was fachlich korrekt ist.

Gute Fehlerbehandlung:

- erhaelt genuegend Kontext fuer Debugging,
- zeigt Nutzern keine internen Stacktraces,
- unterscheidet erwartbare Fehler von Programmierfehlern,
- hinterlaesst keine halbfertigen Dateien oder inkonsistenten Daten.

Wenn ein Fehler ignoriert wird, muss der Grund klar sein. Ein leeres `except`
oder `catch` ist fast immer falsch.

### Datei-I/O

Dateizugriffe brauchen explizite Entscheidungen zu Encoding, Newlines und
Atomizitaet. Das ist besonders wichtig fuer Formate, die plattformuebergreifend
gelesen werden.

Empfehlungen:

- UTF-8 explizit setzen.
- Newline-Verhalten explizit setzen, wenn das Format feste Zeilenenden verlangt.
- Schreibvorgaenge fuer wichtige Dateien atomar ausfuehren: erst temporaer
  schreiben, dann ersetzen.
- Pfadkonventionen in Helferfunktionen kapseln.
- Generierte Laufzeitdaten nicht versehentlich committen.

### Zeit und Zeitzonen

Zeit ist selten trivial. Verwende timezone-aware Zeitpunkte, wenn Daten
gespeichert, verglichen oder ueber Schnittstellen weitergegeben werden.

Empfehlungen:

- Technische Zeitstempel in UTC speichern.
- UI-Labels in der fachlich passenden Zeitzone anzeigen.
- Keine naive lokale Zeit fuer persistierte Daten verwenden.
- Tests fuer Grenzfaelle wie Jahreswechsel, Sommerzeit und fehlende Zeitzonen
  ergaenzen, wenn die Logik davon abhaengt.

## Architektur und Abhaengigkeiten

### Einfache Grenzen

Architektur soll Aenderungen leichter machen. Gute Grenzen trennen Dinge, die
aus unterschiedlichen Gruenden geaendert werden:

- Datenmodell,
- Datenzugriff,
- Fachlogik,
- Praesentation,
- Transport/API,
- externe Provider.

Eine Grenze ist nur hilfreich, wenn sie Komplexitaet reduziert. Abstraktionen
ohne konkreten Nutzen machen Code schwerer, nicht besser.

### Abhaengigkeiten

Neue Abhaengigkeiten brauchen einen klaren Nutzen. Bevor eine Library
hinzugefuegt wird, pruefe:

- Loest sie ein echtes Problem?
- Ist sie gepflegt?
- Passt sie zu Lizenz, Plattform und Build-System?
- Erhoeht sie Bundle-Groesse oder Startzeit?
- Ist der Lockfile aktualisiert?
- Gibt es eine kleinere bestehende Loesung im Projekt?

Eine Abhaengigkeit ist besonders gerechtfertigt, wenn sie etablierte,
fehleranfaellige Logik ersetzt, etwa Parsing, Kryptografie, Accessibility,
Datumslogik oder Standardprotokolle.

## Tests

### Was getestet werden soll

Tests sollen Verhalten absichern, nicht Implementierungsdetails konservieren.
Ein Test ist gut, wenn er bei einem echten Fehler fehlschlaegt und bei einem
harmlosen Refactoring stabil bleibt.

Priorisiere Tests fuer:

- fachliche Regeln,
- Datenformat-Konvertierung,
- Fehlerfaelle,
- Systemgrenzen,
- Regressionen aus echten Bugs,
- oeffentliche APIs und UI-Kernflows.

### Testarten

Unit-Tests pruefen kleine Einheiten schnell und gezielt. Integrationstests
pruefen, ob mehrere Teile korrekt zusammenspielen. UI- und Accessibility-Tests
pruefen, ob die Anwendung nutzbar bleibt.

Nicht jede Aenderung braucht jede Testart. Die Testtiefe soll zum Risiko passen:

- reine Doku-Aenderung: meist kein technischer Test.
- kleine reine Funktion: Unit-Test.
- API-Vertrag: Unit- oder Integrationstest.
- UI-Workflow: DOM-, Browser- oder Accessibility-Test.
- Build-/Dependency-Aenderung: Build-Check.

### Testdaten

Testdaten sollen absichtlich klein und aussagekraeftig sein. Vermeide grosse
Snapshots, wenn ein gezieltes Beispiel reicht.

Wenn Sample-Daten genutzt werden, muessen sie klar als Sample erkennbar bleiben.
Tests duerfen keine echten Zugangsdaten, Tokens oder privaten Daten enthalten.

## Frontend und UI

### Nutzerorientierung

UI-Code ist nicht nur Darstellung, sondern Produktverhalten. Texte, States und
Interaktionen muessen ehrlich und eindeutig sein. Wenn Daten fehlen, unsicher
sind oder nur geplant sind, muss die UI das sagen.

### Accessibility

Interaktive Elemente brauchen sinnvolle Namen, Tastaturbedienbarkeit,
Fokuszustaende und robuste Struktur. Accessibility ist kein spaeterer
Feinschliff, sondern Teil der Definition von funktionsfaehigem UI-Code.

Pruefe besonders:

- Buttons und Inputs haben sichtbaren Text oder `aria-label`.
- Statusmeldungen sind fuer Assistive Technology erreichbar.
- Fokus verschwindet nicht.
- Farbkontrast reicht aus.
- Inhalte bleiben bei kleinen Viewports lesbar.

### CSS

CSS soll bestehende Tokens, Breakpoints und Komponentenstile nutzen. Neue Farben,
Abstaende und Schatten brauchen einen UI-Grund. Reduziere Duplikation durch
gemeinsame Selektoren, aber vermeide so generische Klassen, dass lokale
Komponenten unabsichtlich beeinflusst werden.

Performance-Budgets sind Teil der UI-Qualitaet. Wenn CSS oder JavaScript stark
waechst, pruefe zuerst Duplikation, ungenutzte Regeln und zu breite Features.

## Dokumentation

Dokumentation soll Entscheidungen erklaeren, nicht offensichtlichen Code
nacherzaehlen. Gute Dokumentation beantwortet:

- Warum wurde diese Loesung gewaehlt?
- Welche Alternativen wurden verworfen?
- Welche Annahmen sind unsicher?
- Welche Tests oder Checks belegen den Stand?
- Was muss spaeter erneut geprueft werden?

README-Dateien eignen sich fuer Einstieg und Betrieb. Architektur-, Provider-,
Legal-, Performance- und Review-Entscheidungen gehoeren in eigene Dokumente.

## Reviews

Ein Review soll Risiken finden und die Wartbarkeit verbessern. Es ist keine
Geschmacksabstimmung. Kommentare sollten konkret, begruendet und priorisiert
sein.

Pruefe im Review:

- Ist der Scope klar?
- Ist das Verhalten getestet?
- Sind Namen und Grenzen verstaendlich?
- Werden Fehler bewusst behandelt?
- Gibt es unmarkierte Annahmen?
- Wurden oeffentliche Vertraege veraendert?
- Sind Abhaengigkeiten und generierte Dateien gerechtfertigt?
- Gibt es Sicherheits-, Datenschutz- oder Accessibility-Risiken?

## Sicherheit und Datenschutz

Sensible Daten duerfen nicht im Repo landen. Dazu gehoeren Tokens, API-Keys,
private Konfigurationsdateien, personenbezogene Rohdaten und lokale
Knowledgebase-Snapshots.

Logs und Fehlermeldungen sollen beim Debugging helfen, aber keine Geheimnisse
oder unnoetigen personenbezogenen Daten offenlegen. Wenn externe Dienste
angebunden werden, muessen deren Rechte, Nutzungsbedingungen und
Datenschutzfolgen geprueft oder als offen markiert werden.

## Projektkonkrete Regeln fuer YourCalendar

- Unsicherheit zu Datenquellen immer offenlegen. Keine Quelle als offiziell,
  vollstaendig oder echtzeitfaehig darstellen, wenn das nicht belegt ist.
- POC-, Sample- und produktionsnahe Daten muessen in Code, UI und Tests klar
  unterscheidbar bleiben.
- ICS-Ausgabe, Feed-URLs und API-Payloads sind oeffentliche Vertraege und
  brauchen Regressionstests bei Aenderungen.
- Der Yobsti/Core-Anschluss bleibt unveraendert, solange der User ihn nicht
  explizit zum Scope macht.
- Agenten-Handoffs werden in `docs/agent-status.md` dokumentiert.

## Praktische Checkliste

- Hat die Aenderung einen klaren Zweck?
- Sind Namen und Verantwortlichkeiten verstaendlich?
- Sind Annahmen sichtbar?
- Sind Fehlerfaelle behandelt?
- Sind Encoding, Newlines, Zeitzonen und Pfade explizit genug?
- Wurde der geaenderte Vertrag getestet?
- Sind neue Abhaengigkeiten begruendet und im Lockfile enthalten?
- Bleiben private Daten und generierte Laufzeitdateien aus Git heraus?
- Ist dokumentiert, was nicht sicher bekannt ist?
