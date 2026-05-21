# YourCalendar Design System

## Ziel

YourCalendar nutzt ein ruhiges, mobile-first Interface fuer Kalenderauswahl, Favoriten und ICS-Aktionen. Die Gestaltung priorisiert schnelle Scanbarkeit, grosse Touch-Ziele und klare Statushinweise.

## Framework-Entscheidung

- Tailwind CSS ist als Build-Schicht fuer Tokens, Utility-Klassen und spaetere Komponenten eingefuehrt.
- Das aktuelle Frontend ist Vanilla HTML/JS. Headless UI oder Radix sollen erst bei einer React/Vite-Migration als Komponentenbasis eingefuehrt werden.
- Bis dahin bleiben Buttons, Segmente, Dialoge, Toggle und Event Cards als semantische Vanilla-Komponenten umgesetzt.

## Farben

- `--bg`: App-Hintergrund
- `--surface`: Sidebar- und Seitenflaechen
- `--panel`: Inhaltsflaechen und Cards
- `--ink`: primaerer Text
- `--muted`: sekundaerer Text
- `--line`: Rahmen und Trenner
- `--primary`: Hauptaktion und Fokusfarbe
- `--accent`: Favoriten- und Hinweisfarbe
- `--danger`: Fehlerstatus

Dark Mode wird ueber `data-theme=\"dark\"` auf `<html>` aktiviert. Ohne manuelle Auswahl folgt die App `prefers-color-scheme`.

## Spacing und Layout

- Basisraster: 4 px
- Kompakte Abstaende: 8 bis 12 px
- Panel- und Card-Abstaende: 16 bis 24 px
- Touch-Ziel: mindestens 48 px
- Border Radius: maximal 8 px fuer App-Flachen und Controls

## Typografie

- Systemfont-Stack mit Inter-kompatibler Anmutung
- Keine viewportbasierte Schriftskalierung
- Labels sind klein, fett und ohne negatives Letter-Spacing
- Event-Titel duerfen umbrechen und muessen auf kleinen Displays im Container bleiben

## Komponenten

- Buttons: primaer, sekundaer, Icon-Button, Mini-Button
- Segmente: zweigeteilte Auswahl fuer Live/Sample
- Toggle: Dark-Mode-Schalter im Header
- Event Card: Full-width Row/Card mit Datum, Titel, Meta, Favoriten und Liga-Tag
- Toast: Status- und Fehlermeldung

## Accessibility

- Interaktive Controls haben sichtbare Fokuszustaende.
- Icon-only Buttons benoetigen `aria-label`.
- Statusbereiche nutzen passende `aria-live`-Regionen.
- Farben sind fuer WCAG-AA-Kontrast ausgelegt; finale Pruefung erfolgt mit axe.

## Performance

- Tailwind scannt nur `web/**/*.{html,js}` und `stories/**/*.js`.
- Das CSS-Build wird minifiziert.
- Animationen respektieren `prefers-reduced-motion`.
