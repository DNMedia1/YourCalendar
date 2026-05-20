# YourCalendar Event Model

Stand: 2026-05-20

## Ziel

Das interne Eventmodell trennt externe Quellen von der Kalenderausgabe. Importer
normalisieren Rohdaten in `CalendarEvent`; Feed-Generatoren und UI lesen nur
dieses Modell.

## Felder

| Feld | Zweck |
| --- | --- |
| `uid` | Stabile interne Event-ID fuer Feed-Updates und Deduplizierung. |
| `title` | Nutzer sichtbarer Terminname. |
| `starts_at` / `ends_at` | Zeitzonenbewusster Start und Ende. |
| `all_day` | Markiert ganztaegige Events; Start/Ende bleiben als lokale Mitternacht-Datumsgrenzen modelliert. |
| `source` | Quellenname, z.B. OpenLigaDB oder Sample. |
| `source_quality` | Vertrauensklasse: `official`, `partner`, `paid_provider`, `community`, `scraped`, `manual`, `sample`, `unknown`. |
| `category` | Produktkategorie: `sports`, `politics`, `city`, `culture`, `holidays`, `partner`, `sample`, `unknown`. |
| `source_url` | Optionaler Link zur Quelle oder zum Originaltermin. |
| `location` | Optionaler Ort. |
| `description` | Nutzer sichtbare Beschreibung. |
| `status` | Fachlicher Status: `CONFIRMED`, `TENTATIVE`, `CANCELLED`, `POSTPONED`, `UNKNOWN`. |
| `external_id` | ID aus der Quelle, falls vorhanden. |
| `quality_notes` | Sichtbare Hinweise zu Datenqualität, fehlender Sicherheit oder POC-Einschränkungen. |

## Regeln

- `starts_at` und `ends_at` muessen timezone-aware sein.
- `ends_at` muss nach `starts_at` liegen.
- `uid`, `title` und `source` duerfen nicht leer sein.
- Ganztaegige Events werden als lokaler Start um 00:00 und exklusives Ende am
  Folgetag modelliert.
- Nicht-RFC-konforme fachliche Statuswerte werden fuer ICS gemappt:
  `POSTPONED` und `UNKNOWN` werden als `TENTATIVE` exportiert.

## Offene Punkte

- Deduplizierungsregeln zwischen mehreren Quellen sind noch nicht implementiert.
- Wiederholende Events sind noch nicht modelliert.
- Kalender-, Partner- und Source-Modelle sollten als naechster Schritt getrennt
  vom Eventmodell definiert werden.
