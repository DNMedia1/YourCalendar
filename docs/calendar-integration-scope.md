# Calendar Integration Scope: ICS-first

Stand: 2026-05-26
Bezug: Issue #14 [P1][Story] Google- und Outlook-Integrationen bewusst abgrenzen

## Kurzentscheidung

YourCalendar bleibt im MVP bei oeffentlichen, abonnierbaren ICS-Feeds
(iCalendar / RFC 5545). Direkte Schreib-Integrationen in Google Calendar oder
Outlook ueber OAuth und Microsoft Graph sind bewusst **nicht** Teil des MVP.

Diese Entscheidung bestaetigt die bereits in `project-backlog.md` und im
README-Abschnitt "Why ICS first?" festgehaltene Richtung und macht die Abgrenzung
explizit dokumentierbar.

## Welche Nutzerprobleme ICS bereits loest

Ein stabil gehosteter ICS-Feed (HTTPS-URL) deckt den Kern-Use-Case "Ich moechte
einen thematischen Kalender abonnieren und automatisch aktuell halten" ab, ohne
dass YourCalendar Nutzerkonten oder fremde Kalender-Zugriffsrechte braucht:

- **Apple Calendar**: Abonnieren ueber "Kalender abonnieren" mit der Feed-URL.
- **Google Calendar**: Abonnieren ueber "Per URL hinzufuegen".
- **Outlook**: Abonnieren ueber "Internetkalender abonnieren".
- **Kein Nutzerkonto noetig**: Abonnement passiert clientseitig in der jeweiligen
  Kalender-App des Nutzers.
- **Keine Speicherung von OAuth-Tokens**: YourCalendar haelt keine fremden
  Zugangsdaten und keine Refresh-Tokens.
- **Automatische Updates**: Clients pollen die Feed-URL und ziehen Aenderungen
  selbststaendig nach (Intervall ist clientabhaengig).

Damit ist der gemeinsame Nenner aller drei Ziel-Oekosysteme abgedeckt, ohne pro
Anbieter eine eigene API-Integration zu bauen.

### Bekannte Grenzen von ICS (ehrlich benannt)

- Das Aktualisierungsintervall bestimmt der Client, nicht YourCalendar. Manche
  Clients pollen nur alle paar Stunden bis taeglich.
- ICS ist ein Einbahn-Format: Nutzer abonnieren read-only. Es gibt keine
  Rueckschreibung in einen vorhandenen Kalender und keine Termin-Bestaetigung.
- Ein lokal importierter `.ics`-Snapshot aktualisiert sich nicht; nur die
  abonnierte HTTPS-URL bekommt Updates.

## Was bewusst NICHT Teil des MVP ist

- Google Calendar API Write-Integration (Termine direkt in Nutzerkalender
  schreiben).
- Microsoft Graph Calendar Write-Integration.
- OAuth-Login / "Mit Google anmelden" / "Mit Microsoft anmelden".
- Speicherung von Access- oder Refresh-Tokens fremder Anbieter.
- App Verification / Provider-Review-Prozesse bei Google und Microsoft.
- Nutzerspezifische, bidirektionale Kalender-Synchronisation.

## Spaetere Spike-Ideen (Post-MVP)

Diese Themen sind ausdruecklich erst nach einem validierten ICS-MVP und nach
geklaertem Datenschutz zu bewerten:

- **Google Calendar OAuth Spike**: minimaler Lese-/Schreib-Prototyp hinter
  Source- und Feature-Konfiguration.
- **Microsoft Graph OAuth Spike**: Consumer- vs. Tenant-Unterschiede und noetige
  Permissions evaluieren.
- **Token Storage / Refresh Token Security**: sichere Ablage, Rotation,
  Widerruf und Verschluesselung von Tokens.
- **Datenschutzpruefung**: rechtlich zu pruefen, welche Daten verarbeitet/
  gespeichert werden duerfen (keine Rechtsberatung in diesem Dokument).
- **Kosten-/Verification-Aufwand**: offizielle Anbieter-Dokumentation pruefen,
  bevor konkrete Kosten oder Review-Dauer genannt werden (hier bewusst keine
  erfundenen Zahlen).

## Risiken einer zu fruehen Direktintegration

- **Datenschutz**: Zugriff auf fremde Kalender bedeutet Verarbeitung
  personenbezogener Daten. Umfang und Rechtsgrundlage sind rechtlich zu pruefen.
- **Token-Leaks**: Gespeicherte OAuth-Tokens sind ein hochwertiges Angriffsziel
  und erhoehen die Sicherheitsverantwortung deutlich.
- **App Verification**: Google und Microsoft verlangen Review-/Verifizierungs-
  Schritte fuer sensible Scopes; Aufwand und Anforderungen sind in der jeweils
  aktuellen offiziellen Dokumentation zu pruefen.
- **Support-Aufwand**: pro Anbieter eigene Fehlerquellen (Consent abgelaufen,
  Permissions geaendert, Rate Limits, API-Deprecations).
- **Vendor-Lock-in**: anbieterspezifische Integrationen binden Aufwand, der dem
  anbieterneutralen ICS-Standard fehlt.

## Entscheidung

- Fuer das MVP bleibt YourCalendar bei oeffentlichen / abonnierbaren ICS-Feeds.
- Direkte Google-/Outlook-Integrationen werden erst nach validiertem MVP und
  geklaertem Datenschutz bewertet und dann als separate, abgegrenzte OAuth-Spikes
  geplant.

## Hinweis

Dieses Dokument ist eine Produkt- und Scoping-Entscheidung, keine Rechtsberatung.
Aussagen zu Datenschutz, Tokens, App Verification und Anbieter-Bedingungen sind
vor produktiver Nutzung rechtlich und anhand der aktuellen offiziellen
Anbieter-Dokumentation zu pruefen.
