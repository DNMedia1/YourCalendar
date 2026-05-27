# Performance and Accessibility Baseline

Stand: 2026-05-26.

## Zweck

Diese Baseline definiert die aktuelle Mindestqualitaet fuer die lokale
YourCalendar-Weboberflaeche. Sie ist bewusst klein gehalten, damit das MVP auf
mobilen Verbindungen schnell bleibt und grundlegende Accessibility nicht erst
spaet nachgezogen wird.

## Aktuelle Entscheidungen

- Die Weboberflaeche bleibt ohne Login und ohne Client-seitiges Framework
  nutzbar.
- Der sichtbare Event-Render ist auf 200 Karten begrenzt. Der ICS-Feed kann
  weiterhin alle gefilterten Events enthalten.
- Lade-, Leer- und Hinweiszustaende werden mit `aria-live`, `aria-busy` und
  `role="status"` fuer assistive Technologien sichtbar gemacht.
- Primaere Controls muessen einen sichtbaren Text, ein Label, einen Placeholder
  oder ein `aria-label` haben.
- Tailwind wird lokal gebaut, aber die ausgelieferte UI nutzt weiterhin
  schlanke statische Assets.

## Performance-Budget

Die Node-Tests pruefen aktuell diese unkomprimierten Groessen:

| Datei | Budget |
| --- | ---: |
| `web/app.js` | 32 KB |
| `web/styles.css` | 30 KB |
| `web/mobile.css` | 6 KB |
| `web/tailwind.css` | 10 KB |
| Summe | 75 KB |

Diese Budgets sind keine finale Lighthouse-Grenze. Sie verhindern aber, dass
das MVP unbemerkt grosse Framework- oder Asset-Last bekommt. Die Werte
beruecksichtigen den gemergten Kalenderkatalog mit Sportarten-, Provider- und
Quellenmonitor-Ansicht.

## Accessibility-Baseline

Automatisiert geprueft wird:

- statische HTML-Shell mit `axe-core`
- Dark-Mode-Toggle mit `data-theme` und `aria-pressed`
- primaere interaktive Controls mit zugreifbarem Namen
- leere Eventliste als Statusmeldung
- lange Eventlisten mit sichtbarem Limit-Hinweis

Der `axe-core` Smoke-Test deaktiviert aktuell `color-contrast`, weil JSDOM keine
vollstaendige visuelle Kontrastpruefung ersetzt. Farbkontrast muss deshalb bei
visuellen UI-Aenderungen zusaetzlich im Browser geprueft werden.

## Manuelle Pruefung vor groesseren UI-Merges

1. Desktop laden und sicherstellen, dass kein leerer Screen oder Error Overlay
   sichtbar ist.
2. Mobile Viewport pruefen: Header, Sidebar, Abo-Box und Eventkarten duerfen
   nicht ueberlaufen.
3. Tastaturfokus durch die wichtigsten Controls bewegen.
4. Sample- und Live-Modus testen.
5. Fehlerzustand einer Quelle simulieren oder mindestens die Fehlermeldung in
   der UI pruefen.

## Kommandos

```bash
python3 -m unittest discover -s tests
npm test
```

## Offene Risiken

- Kein echter Lighthouse-/Web-Vitals-Lauf in CI.
- Keine Browser-Matrix fuer iPhone Safari, Android Chrome und Desktop-Browser.
- Keine echte Screenreader-Pruefung.
- Kontrast wird automatisiert nur eingeschraenkt geprueft.
