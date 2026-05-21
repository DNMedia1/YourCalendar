from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence

from yourcalendar_model import CalendarEvent


@dataclass(frozen=True)
class SourceIntegrationPlan:
    plan_id: str
    title: str
    scope: str
    status: str
    status_label: str
    priority: str
    calendar_ids: tuple[str, ...]
    summary: str
    blockers: tuple[str, ...]
    next_steps: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]


@dataclass(frozen=True)
class SourceMonitorRecord:
    record_id: str
    source_label: str
    scope: str
    status: str
    status_label: str
    calendar_ids: tuple[str, ...]
    last_checked_mode: str
    event_count_label: str
    message: str
    next_action: str


class SourceAdapter(Protocol):
    """Adapter contract for future event source importers."""

    adapter_id: str
    source_label: str

    def fetch_events(self, *, now: datetime) -> Sequence[CalendarEvent]:
        """Return normalized events from the external source."""


SOURCE_INTEGRATION_PLANS = (
    SourceIntegrationPlan(
        plan_id="openligadb-football-poc",
        title="OpenLigaDB Fußball-POC härten",
        scope="Deutschland",
        status="active",
        status_label="Aktiv im POC",
        priority="P0",
        calendar_ids=("football-germany",),
        summary="Der bestehende Fußball-Feed funktioniert als technischer Beweis, braucht aber Qualitäts- und Fallback-Regeln.",
        blockers=(
            "Keine garantierte SLA- oder Echtzeit-Zusage.",
            "Coverage ist auf ausgewählte deutsche Fußballwettbewerbe begrenzt.",
        ),
        next_steps=(
            "Importfehler und leere Saisons sichtbar melden.",
            "Fallback-Text für fehlende Spieltage je Liga ergänzen.",
            "Entscheiden, ob OpenLigaDB nur POC bleibt oder produktiv genutzt werden darf.",
        ),
        acceptance_criteria=(
            "Fehlerhafte Abrufe liefern klare UI-Hinweise statt leere Kalender ohne Erklärung.",
            "Jeder importierte Termin hat Quelle, Liga, Startzeit und Zeitzone.",
        ),
    ),
    SourceIntegrationPlan(
        plan_id="europe-sports-provider",
        title="Europa-Multi-Sport-Provider anbinden",
        scope="Europa",
        status="research",
        status_label="Recherche nötig",
        priority="P1",
        calendar_ids=("europe-all-sports",),
        summary="Für die breite Sportarten-Auswahl braucht YourCalendar eine belastbare Provider-Taxonomie und Import-API.",
        blockers=(
            "Sportarten, Ligen, Länder und Rechte müssen je Anbieter geprüft werden.",
            "Ohne Provider-Taxonomie ist 'alle Sportarten' nicht belastbar vollständig.",
        ),
        next_steps=(
            "Provider-Matrix für Coverage, Preis, Nutzungsrechte und Update-Latenz erstellen.",
            "Adapter-Spike mit drei verschiedenen Sportarten planen.",
            "Normalisierte Sportart-, Liga- und Wettbewerbsschlüssel festlegen.",
        ),
        acceptance_criteria=(
            "Mindestens drei europäische Sportarten lassen sich über denselben Adapter importieren.",
            "Jeder Termin enthält Sportart, Wettbewerb, Land oder Region, Quelle und Aktualisierungszeit.",
            "Nicht abgedeckte Sportarten bleiben als 'Provider nötig' sichtbar.",
        ),
    ),
    SourceIntegrationPlan(
        plan_id="global-combat-provider",
        title="Globalen Kampfsport-Provider evaluieren",
        scope="Weltweit",
        status="research",
        status_label="Recherche nötig",
        priority="P1",
        calendar_ids=("global-combat-events",),
        summary="Weltweite Fight Cards brauchen wahrscheinlich mehrere Quellen oder einen spezialisierten Datenanbieter.",
        blockers=(
            "Eine einzelne freie Quelle für sämtliche Kampfsportveranstaltungen ist nicht gesichert.",
            "Fight Cards ändern sich kurzfristig; Zeitzonen, Absagen und Gegnerwechsel müssen abbildbar sein.",
        ),
        next_steps=(
            "Quellenstrategie für MMA, Boxen, Kickboxen und Grappling trennen.",
            "Partner-/Lizenzoptionen gegen Scraping-Risiko abwägen.",
            "Importformat für Fight Card, Gewichtsklasse, Organisation und Status definieren.",
        ),
        acceptance_criteria=(
            "Events können nach Kampfsportart, Organisation und Region gefiltert werden.",
            "Kurzfristige Statusänderungen werden als Aktualisierung im Kalender sichtbar.",
            "Unsichere oder unvollständige Cards werden klar gekennzeichnet.",
        ),
    ),
    SourceIntegrationPlan(
        plan_id="championship-detector",
        title="WM/EM-Erkennung pro Sportart bauen",
        scope="Weltweit und Europa",
        status="design",
        status_label="Konzept",
        priority="P1",
        calendar_ids=("world-europe-championships",),
        summary="WM und EM sollen angezeigt werden, wenn sie laufen oder bevorstehen, ohne Altersklassen und Verbände zu vermischen.",
        blockers=(
            "WM/EM-Begriffe sind je Sportart, Verband, Geschlecht und Altersklasse unterschiedlich.",
            "Turnierzeiträume und Spielpläne brauchen eine zuverlässige Primärquelle.",
        ),
        next_steps=(
            "Regel definieren, welche WM/EM-Arten im MVP zählen.",
            "Turnierfenster, Qualifikation und Hauptturnier getrennt modellieren.",
            "Kalenderansicht für laufend, bald startend und beendet spezifizieren.",
        ),
        acceptance_criteria=(
            "Laufende Turniere erscheinen automatisch mit Start- und Enddatum.",
            "Bevorstehende Turniere können als abonnierbarer Kalender veröffentlicht werden.",
            "Mehrdeutige Turniere werden nicht automatisch als offizielle WM/EM behauptet.",
        ),
    ),
)


SOURCE_MONITOR_RECORDS = (
    SourceMonitorRecord(
        record_id="openligadb-football",
        source_label="OpenLigaDB Fußball",
        scope="Deutschland",
        status="watching",
        status_label="Beobachtet",
        calendar_ids=("football-germany",),
        last_checked_mode="Beim Feed- oder UI-Abruf",
        event_count_label="Pro Abruf ermittelt",
        message="Der POC ruft Spielplandaten direkt beim Nutzerabruf ab. Ein geplanter Importjob existiert noch nicht.",
        next_action="Importjob mit persistierter letzter Prüfung und Fehlerhistorie bauen.",
    ),
    SourceMonitorRecord(
        record_id="yourcalendar-sample",
        source_label="YourCalendar Sample",
        scope="Intern",
        status="ok",
        status_label="Stabil",
        calendar_ids=("sample-ksc",),
        last_checked_mode="Lokal generiert",
        event_count_label="2 Sample-Termine",
        message="Sample-Daten sind bewusst statisch und dienen nur zum Prüfen des Abo-Flows.",
        next_action="Sample bleibt als Testmodus erhalten, darf aber nie als echter Sportkalender erscheinen.",
    ),
    SourceMonitorRecord(
        record_id="europe-sports-provider",
        source_label="Europa-Multi-Sport",
        scope="Europa",
        status="planned",
        status_label="Kein Job",
        calendar_ids=("europe-all-sports",),
        last_checked_mode="Noch nicht angebunden",
        event_count_label="Keine produktiven Events",
        message="Für breite europäische Sportarten fehlt noch eine verlässliche Provider-API.",
        next_action="Provider-Matrix abschließen und Adapter-Spike starten.",
    ),
    SourceMonitorRecord(
        record_id="global-combat-provider",
        source_label="Globaler Kampfsport",
        scope="Weltweit",
        status="planned",
        status_label="Kein Job",
        calendar_ids=("global-combat-events",),
        last_checked_mode="Noch nicht angebunden",
        event_count_label="Keine produktiven Events",
        message="Weltweite Fight Cards brauchen eine lizenzsichere Quelle oder mehrere geprüfte Quellen.",
        next_action="Quellenstrategie für MMA, Boxen, Kickboxen und Grappling getrennt prüfen.",
    ),
    SourceMonitorRecord(
        record_id="championship-detector",
        source_label="WM/EM-Erkennung",
        scope="Weltweit und Europa",
        status="design",
        status_label="Konzept",
        calendar_ids=("world-europe-championships",),
        last_checked_mode="Noch nicht angebunden",
        event_count_label="Keine produktiven Turniere",
        message="WM/EM-Erkennung braucht klare Regeln pro Sportart, Verband und Turnierphase.",
        next_action="Turniermodell definieren und erste Sportart als Spike auswählen.",
    ),
)


def source_integration_plan_payload(plan: SourceIntegrationPlan) -> dict:
    return {
        "id": plan.plan_id,
        "title": plan.title,
        "scope": plan.scope,
        "status": plan.status,
        "statusLabel": plan.status_label,
        "priority": plan.priority,
        "calendarIds": list(plan.calendar_ids),
        "summary": plan.summary,
        "blockers": list(plan.blockers),
        "nextSteps": list(plan.next_steps),
        "acceptanceCriteria": list(plan.acceptance_criteria),
    }


def source_plan_payload() -> dict:
    plans = [source_integration_plan_payload(plan) for plan in SOURCE_INTEGRATION_PLANS]
    return {
        "total": len(plans),
        "active": sum(1 for plan in SOURCE_INTEGRATION_PLANS if plan.status == "active"),
        "needsWork": sum(1 for plan in SOURCE_INTEGRATION_PLANS if plan.status != "active"),
        "items": plans,
    }


def source_monitor_record_payload(record: SourceMonitorRecord) -> dict:
    return {
        "id": record.record_id,
        "sourceLabel": record.source_label,
        "scope": record.scope,
        "status": record.status,
        "statusLabel": record.status_label,
        "calendarIds": list(record.calendar_ids),
        "lastCheckedMode": record.last_checked_mode,
        "eventCountLabel": record.event_count_label,
        "message": record.message,
        "nextAction": record.next_action,
    }


def source_monitor_payload() -> dict:
    records = [source_monitor_record_payload(record) for record in SOURCE_MONITOR_RECORDS]
    return {
        "total": len(records),
        "watching": sum(1 for record in SOURCE_MONITOR_RECORDS if record.status in {"watching", "ok"}),
        "planned": sum(1 for record in SOURCE_MONITOR_RECORDS if record.status in {"planned", "design"}),
        "items": records,
    }
