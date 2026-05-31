# Responsive QA Baseline

Stand: 2026-05-28. Bezug: GitHub Issue #25.

## Ziel

YourCalendar soll auf Smartphone, Tablet und Desktop ohne Zoomen bedienbar
sein. Diese Datei beschreibt die aktuellen Breakpoints und die manuellen
QA-Flows fuer Reviews.

## Breakpoints

- Desktop: groesser als 1100 px. Zweispaltiges App-Layout mit Sidebar und
  Kataloginhalt nebeneinander.
- Tablet: 901-1100 px. Verdichtete Abstaende, Monitoring-Karten auf zwei
  Spalten.
- Small Tablet / Large Phone: bis 900 px. Inhalt kommt vor der Sidebar,
  Aktionen werden als Touch-Grid angezeigt, Sidebar-Panels werden zweispaltig.
- Phone: bis 640 px. Sidebar und Content laufen einspaltig, Katalogkarten,
  Abo-Aktionen und Eventkarten sind Full-Width.
- Narrow Phone: bis 420 px. Header-Aktionen laufen einspaltig, Headline wird
  kompakter.

## Kritische Flows

1. Katalog oeffnen und Kategorie wechseln.
2. Kalenderkarte lesen: Status, Quelle, Qualitaet und Aktualisierung duerfen
   nicht aus dem Layout laufen.
3. Abo-Link kopieren oder ICS-Link laden.
4. Vorschau-Filter erreichen und Vereinsfilter nutzen.
5. Dark-Mode toggeln.
6. Event-Favorit setzen und wieder entfernen.

## Manuelle Review-Matrix

| Viewport | Ziel |
| --- | --- |
| 390 x 844 | iPhone/Android Hochformat, Hauptziel fuer Mobile-first. |
| 768 x 1024 | Tablet Hochformat, Sidebar-Panels zweispaltig pruefen. |
| 1280 x 800 | Desktop/Laptop, Sidebar und Katalog nebeneinander. |

## Automatisierte Checks

- `npm test` prueft UI-Smoke, Accessibility-Smoke und Asset-Budgets.
- `npm run build-storybook` prueft, dass die Komponentendokumentation baut.
- Ein spaeteres Cypress-Issue (#48) soll echte Browser-Flows in CI ergaenzen.
