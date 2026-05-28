# Datenschutz- und Impressumsbedarf (MVP)

Stand: 2026-05-28. Bezug: GitHub Issue #15.

## Zweck

Dieses Dokument listet den rechtlichen Mindestbedarf fuer den YourCalendar-MVP.
Es ist kein Rechtsgutachten. Offene Fragen sind explizit als offen markiert.
Vor Veroeffentlichung ist eine Pruefung durch eine rechtlich verantwortliche
Person notwendig.

## Notwendige Rechtstexte

### Impressum (Anbieterkennzeichnung)

Fuer oeffentlich erreichbare Websites gilt in Deutschland das Telemediengesetz
(TMG § 5 bzw. ab 2024 DDG § 5). Ein Impressum ist ab dem Zeitpunkt Pflicht, an
dem die Website oeffentlich erreichbar ist, auch im MVP-Stadium.

Pflichtangaben fuer natuerliche Personen:
- Name und Anschrift der verantwortlichen Person.
- E-Mail-Adresse (erreichbar). Eine Postfach-Adresse reicht als Ergaenzung, ersetzt aber nicht die direkte E-Mail.
- Ggf. Telefonnummer (bei Diensten mit Bezahlpflicht Pflicht, sonst empfohlen).

**Offene Frage:** Wer ist verantwortliche Person? Adresse oeffentlich oder Postfach? Eskar87 hat im GitHub Issue darauf hingewiesen, dass eine Postfach-Adresse moeglich ist.

### Datenschutzerklaerung

Eine Datenschutzerklaerung ist gemaess DSGVO (Art. 13/14) immer dann
vorgeschrieben, wenn personenbezogene Daten verarbeitet werden oder auch nur
verarbeitet werden koennten (z.B. durch Server-Logs eines Hosters).

Sobald die Seite oeffentlich gehostet wird, ist eine Datenschutzerklaerung
Pflicht, unabhaengig davon, ob der Betreiber selbst Daten sammelt.

**Offene Frage:** Welcher Hoster wird genutzt? Dessen Verarbeitungsverzeichnis und Datenschutzerklarung beeinflusst den eigenen Text.

## Verarbeitung personenbezogener Daten im aktuellen MVP

### Was der MVP aktuell verarbeitet oder nicht verarbeitet

| Bereich | Aktueller Stand | Beleg |
| --- | --- | --- |
| Nutzerkonten | Keine. Kein Login, keine Registrierung. | `web_app.py`, kein Session-/Cookie-Management |
| HTTP-Anfragelogs | Deaktiviert. `log_message` gibt nichts aus. | `web_app.py:832` |
| Cookies (Server-seitig) | Keine gesetzt. | `web_app.py`, kein `Set-Cookie`-Header |
| Browser-Favoriten | Im `localStorage` des Browsers gespeichert, serverseitig nie uebertragen. | README, UI-Code |
| Importierte Eventdaten | Nur oeffentlich verfuegbare Spielplan- und Feiertagsdaten aus OpenLigaDB und Nager.Date. Kein Personenbezug. | `import_jobs.py` |
| Feed-Dateien auf Disk | Gecachte ICS-Feeds und Snapshot-JSON lokal in `output/`. Kein Personenbezug. | `import_jobs.py:60-86` |
| Externe API-Zugriffe | `import_jobs.py` ruft externe APIs ab (OpenLigaDB, Nager.Date, TheSportsDB). Die eigene IP-Adresse wird dabei gegenueber den Anbietern sichtbar. | `import_jobs.py` |

**Fazit zum aktuellen Stand:** Im lokalen POC-Betrieb werden keine personenbezogenen Nutzerdaten verarbeitet. Sobald der MVP oeffentlich gehostet wird, gilt das anders: Der Hoster sieht IP-Adressen der Besucher.

### Was beim Hosting hinzukommt

Sobald der MVP auf einem oeffentlichen Server laeuft:

- IP-Adressen von Besuchern werden im Hoster-Log gespeichert (gesetzliche Pflicht des Hosters).
- Abonnement-Anfragen an ICS-Feed-URLs sind ebenfalls mit IP-Adresse im Log.
- Wenn ein CDN oder Reverse-Proxy genutzt wird, gelten deren eigene Datenschutzregeln.

## Logging- und Tracking-Entscheidungen

### Aktuell entschieden

- **Kein serverseitiges Request-Logging** im Python-App-Code (`log_message` suppressed in `web_app.py:832`).
- **Kein clientseitiges Tracking** (kein Google Analytics, kein Plausible, keine Pixels).
- **Keine Drittanbieter-Scripts** im Frontend (kein CDN fuer React/Bootstrap/GA).
- **Kein Feed-Abonnenten-Tracking**: Wer einen Feed abonniert, ist dem Server nicht bekannt.

### Noch nicht entschieden

- **Hoster-seitiges Logging**: Abhaengig vom Hoster; muss in Datenschutzerklaerung erwaehnt werden.
- **Fehlerlogging**: Kein strukturiertes Error-Tracking (z.B. Sentry) vorhanden. Wenn spaeter eins kommt, muss es in der Datenschutzerklaerung stehen.

## Offene Rechtsfragen

Diese Punkte sind nicht geklaert und muessen vor Veroeffentlichung beantwortet werden:

1. **Verantwortliche Person**: Wer traegt die rechtliche Verantwortung (Betreiber, Impressumspflicht)?
2. **Hoster-Wahl**: Welcher Hoster wird genutzt, und welche Datenschutzerklaerung gilt dort? (Hetzner, Fly.io, Vercel etc. haben unterschiedliche Verarbeitungsvertraege.)
3. **Auftragsverarbeitungsvertrag (AVV)**: Mit dem Hoster muss bei personenbezogenen Daten (IP-Adressen) ein AVV abgeschlossen werden.
4. **Drittquellen-Nutzungsbedingungen**: OpenLigaDB, Nager.Date und TheSportsDB haben eigene Nutzungsbedingungen. Eine kurze Pruefung, ob kommerzielle Nutzung erlaubt ist, steht noch aus.
5. **Postfach vs. Anschrift**: Die Frage aus dem GitHub Issue-Kommentar (eskar87), ob ein gemietetes Postfach genuegt, haengt vom konkreten Anbieter ab. Postalisch erreichbar muss man auf jeden Fall sein.
6. **Minderjaerige**: Kein spezifischer Schutz implementiert. Solange keine Anmeldung und keine Profilbildung, gibt es keine besonderen Pflichten. Aendert sich das, muss neu bewertet werden.

## Naechste Schritte

1. Impressumstext mit konkreten Angaben (Name, Adresse, E-Mail) erstellen, sobald Hoster und verantwortliche Person feststehen.
2. Datenschutzerklaerung anlegen (kann ein Generator-Text sein, muss aber Hoster-Abschnitt enthalten).
3. Beide Texte als statische Seiten in die Web-UI einbinden (`/impressum`, `/datenschutz`).
4. AVV mit gewahltem Hoster abschliessen oder pruefen, ob der Hoster DSGVO-konform in der EU ist.
5. Drittquellen-Nutzungsbedingungen kurz dokumentieren (reicht als Issue-Kommentar oder Docs-Eintrag).
