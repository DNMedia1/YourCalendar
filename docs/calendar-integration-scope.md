# Calendar Integration Scope: ICS-first

Stand: 2026-05-26
Bezug: Issue #14 [P1][Story] Google- und Outlook-Integrationen bewusst abgrenzen

## Kurzentscheidung

YourCalendar bleibt im MVP bei öffentlichen, abonnierbaren ICS-Feeds
(iCalendar / RFC 5545). Direkte Schreib-Integrationen in Google Calendar oder
Outlook über OAuth und Microsoft Graph sind bewusst **nicht** Teil des MVP.

Diese Entscheidung bestätigt die bereits in `project-backlog.md` und im
README-Abschnitt "Why ICS first?" festgehaltene Richtung und macht die Abgrenzung
explizit dokumentierbar.

## Welche Nutzerprobleme ICS bereits löst

Ein stabil gehosteter ICS-Feed (HTTPS-URL) deckt den Kern-Use-Case "Ich möchte
einen thematischen Kalender abonnieren und automatisch aktuell halten" ab, ohne
dass YourCalendar Nutzerkonten oder fremde Kalender-Zugriffsrechte braucht:

- **Apple Calendar**: Abonnieren über "Kalender abonnieren" mit der Feed-URL.
- **Google Calendar**: Abonnieren über "Per URL hinzufügen".
- **Outlook**: Abonnieren über "Internetkalender abonnieren".
- **Kein Nutzerkonto nötig**: Abonnement passiert clientseitig in der jeweiligen
  Kalender-App des Nutzers.
- **Keine Speicherung von OAuth-Tokens**: YourCalendar hält keine fremden
  Zugangsdaten und keine Refresh-Tokens.
- **Automatische Updates**: Clients pollen die Feed-URL und ziehen Änderungen
  selbstständig nach (Intervall ist clientabhängig).

Damit ist der gemeinsame Nenner aller drei Ziel-Ökosysteme abgedeckt, ohne pro
Anbieter eine eigene API-Integration zu bauen.

### Bekannte Grenzen von ICS (ehrlich benannt)

- Das Aktualisierungsintervall bestimmt der Client, nicht YourCalendar. Manche
  Clients pollen nur alle paar Stunden bis täglich.
- ICS ist ein Einbahn-Format: Nutzer abonnieren read-only. Es gibt keine
  Rückschreibung in einen vorhandenen Kalender und keine Termin-Bestätigung.
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

## Spätere Spike-Ideen (Post-MVP)

Diese Themen sind ausdrücklich erst nach einem validierten ICS-MVP und nach
geklärtem Datenschutz zu bewerten:

- **Google Calendar OAuth Spike**: minimaler Lese-/Schreib-Prototyp hinter
  Source- und Feature-Konfiguration.
- **Microsoft Graph OAuth Spike**: Consumer- vs. Tenant-Unterschiede und nötige
  Permissions evaluieren.
- **Token Storage / Refresh Token Security**: sichere Ablage, Rotation,
  Widerruf und Verschlüsselung von Tokens.
- **Datenschutzprüfung**: rechtlich zu prüfen, welche Daten verarbeitet/
  gespeichert werden dürfen (keine Rechtsberatung in diesem Dokument).
- **Kosten-/Verification-Aufwand**: offizielle Anbieter-Dokumentation prüfen,
  bevor konkrete Kosten oder Review-Dauer genannt werden (hier bewusst keine
  erfundenen Zahlen).

## Risiken einer zu frühen Direktintegration

- **Datenschutz**: Zugriff auf fremde Kalender bedeutet Verarbeitung
  personenbezogener Daten. Umfang und Rechtsgrundlage sind rechtlich zu prüfen.
- **Token-Leaks**: Gespeicherte OAuth-Tokens sind ein hochwertiges Angriffsziel
  und erhöhen die Sicherheitsverantwortung deutlich.
- **App Verification**: Google und Microsoft verlangen Review-/Verifizierungs-
  Schritte für sensible Scopes; Aufwand und Anforderungen sind in der jeweils
  aktuellen offiziellen Dokumentation zu prüfen.
- **Support-Aufwand**: pro Anbieter eigene Fehlerquellen (Consent abgelaufen,
  Permissions geändert, Rate Limits, API-Deprecations).
- **Vendor-Lock-in**: anbieterspezifische Integrationen binden Aufwand, der dem
  anbieterneutralen ICS-Standard fehlt.

## Entscheidung

- Für das MVP bleibt YourCalendar bei öffentlichen / abonnierbaren ICS-Feeds.
- Direkte Google-/Outlook-Integrationen werden erst nach validiertem MVP und
  geklärtem Datenschutz bewertet und dann als separate, abgegrenzte OAuth-Spikes
  geplant.

## Hinweis

Dieses Dokument ist eine Produkt- und Scoping-Entscheidung, keine Rechtsberatung.
Aussagen zu Datenschutz, Tokens, App Verification und Anbieter-Bedingungen sind
vor produktiver Nutzung rechtlich und anhand der aktuellen offiziellen
Anbieter-Dokumentation zu prüfen.
