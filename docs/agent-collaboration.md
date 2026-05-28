# Agent Collaboration Protocol

Stand: 2026-05-28.

## Ziel

Codex, Claude Code und weitere Agenten sollen nicht gegeneinander arbeiten.
Dieses Dokument legt fest, welche Informationen geteilt werden, was lokal
bleibt und wie Arbeit uebergeben wird.

## Gemeinsame Wissensquellen

Diese Reihenfolge gilt fuer Projektwissen:

1. Aktuelle Anweisung des Users.
2. GitHub Issues und GitHub Project Board fuer Planung, Prioritaet und Status.
3. `AGENTS.md` und `CLAUDE.md` fuer Agenten-Regeln.
4. `docs/agent-status.md` fuer aktuelle Handoffs und Arbeitsstand.
5. README, `docs/`, Tests und Git-Historie fuer technische Fakten.
6. Lokale Knowledgebases unter `.claude/` oder `.snapshots/` nur als private
   Zusatzhilfe.

Wenn diese Quellen widersprechen, muss der Agent den Widerspruch benennen und
nicht still raten.

## Was ins Repo gehoert

Ins Repo gehoeren stabile, projektweite Informationen:

- Architektur- und Produktentscheidungen.
- Issue- und PR-Bezuege.
- Akzeptanzkriterien, Tests und Qualitaetsregeln.
- Kurze Handoffs, die ein anderer Agent spaeter fortsetzen kann.
- Agentenregeln, die fuer alle gelten.

Nicht ins Repo gehoeren:

- API-Keys, Tokens, Billing-Informationen oder lokale Login-Daten.
- `.env`, `.claude/settings.local.json`, `.claude/` und private Snapshots.
- Rohkopien lokaler Knowledgebases, solange der User sie privat halten will.
- Ungepruefte Recherche als Fakt.

## Start-Checkliste fuer jeden Agenten

Vor jeder Umsetzung muss der Agent einen Session Intake ausfuehren:

1. `git status --short --branch` pruefen.
2. `docs/agent-status.md` lesen.
3. Offene GitHub PRs pruefen, damit kein bestehender Branch doppelt bearbeitet
   wird.
4. Offene GitHub Issues pruefen.
5. Klaeren, welches Issue oder welcher Task bearbeitet wird.
6. Wenn der User kein Issue genannt hat: das naechste Issue nach der
   Auswahlregel unten bestimmen.
7. Issue claimen oder dokumentieren, warum kein Claim moeglich war.
8. Einen eigenen Branch verwenden, z.B. `feat/issue-25-mobile-layout` oder
   `fix/ci-catalog-checks`.
9. Bestehende Aenderungen anderer Agenten nicht zuruecksetzen.

Der Intake muss in `docs/agent-status.md` oder im GitHub Issue nachvollziehbar
sein. Nur reine Antwort-Aufgaben ohne Code-/GitHub-Aenderung duerfen ohne
persistierten Intake erledigt werden.

## Session-Intake-Schema

Jeder Agent verarbeitet den Projektstand nach diesem Schema:

```text
### YYYY-MM-DD HH:MM Europe/Berlin - <Agent> - Intake
- Repo-Branch:
- Worktree clean: yes/no
- GitHub PRs geprueft:
- Offene Issues geprueft:
- Gewaehltes Issue:
- Warum dieses Issue:
- Claim-Status:
- Branch:
- Erwartete Dateien:
- Erste Checks:
- Blocker/Unsicherheit:
```

Wenn ein Agent nur liest oder analysiert, wird `Gewaehltes Issue: none` gesetzt
und kurz begruendet.

## Naechstes GitHub Issue automatisch waehlen

Wenn der User kein konkretes Issue nennt, nimmt der Agent das naechste
bearbeitbare Issue nach dieser Reihenfolge:

1. Offene Issues mit `[P0]` im Titel oder `P0`-Label.
2. Offene Issues mit `[P1]` im Titel oder `P1`-Label.
3. Offene Issues mit `[P2]` im Titel oder `P2`-Label.
4. Innerhalb gleicher Prioritaet: Story-Issues (`[Story]`) vor Board-, Epic-
   oder Sammelissues.
5. Nicht zugewiesene Issues vor bereits zugewiesenen Issues.
6. Issues mit vorhandenen Akzeptanzkriterien vor vagen Recherche- oder
   Sammelthemen.
7. Wenn mehrere gleichwertig sind: das aelteste laenger offene Issue zuerst.

Ein Agent darf ein bereits zugewiesenes Issue nur nehmen, wenn:

- der User es explizit nennt,
- der Assignee der gleiche Mensch/Agent ist,
- oder der aktuelle Handoff klar sagt, dass die Arbeit frei ist.

Board-/Epic-Issues wie `P0 MVP-Grundlage` dienen als Kontext und werden nicht
als erstes Implementierungsziel genommen, solange darunter konkrete Storys offen
sind.

## Issue Claim

Vor Implementierungsbeginn soll der Agent das Issue claimen. Bevorzugt wird ein
GitHub-Issue-Kommentar:

```text
### Agent Claim
- Agent: <Codex|Claude Code|...>
- Branch: <branch>
- Scope: <kurzer Arbeitsumfang>
- Started: <YYYY-MM-DD HH:MM Europe/Berlin>
- Status: in_progress
```

Wenn GitHub-Rechte fehlen oder der User keine GitHub-Aenderung will, wird der
Claim in `docs/agent-status.md` eingetragen. Der Agent muss dann im Chat
erwaehnen, dass GitHub nicht aktualisiert wurde.

## Wissensaustausch zwischen Agenten

Wissen darf nicht nur im Chat eines einzelnen Agenten bleiben. Der Agent muss
neue belastbare Erkenntnisse an mindestens einer gemeinsamen Stelle ablegen:

- `docs/agent-status.md` fuer aktuellen Arbeitsstand, Claim, Handoff und
  naechsten Schritt.
- Relevantes GitHub Issue fuer fachliche Entscheidungen, Blocker und
  Testergebnisse.
- PR-Beschreibung fuer Implementierungsumfang, Tests und Restrisiko.
- Dauerhafte `docs/`-Datei, wenn die Erkenntnis ein Produkt-, Architektur-,
  Datenquellen- oder Betriebsentscheid ist.

Nicht gesicherte Annahmen muessen als Annahmen markiert werden. Lokale
Knowledgebase-Regeln duerfen genutzt, aber nicht als Projektfakt behauptet
werden, solange sie nicht in Repo-Doku, Issue oder PR destilliert sind.

## Arbeitsregeln

- Ein Agent bearbeitet genau einen klaren Task pro Branch.
- Zwei Agenten sollen nicht gleichzeitig dieselben Dateien oder dasselbe Issue
  bearbeiten, ausser der User hat das bewusst so entschieden.
- Wenn ein Task unklar, veraltet, doppelt oder blockiert ist, zuerst klaeren.
- Issue-Texte nicht gross umschreiben, Labels nicht entfernen und Issues nicht
  schliessen, ohne dass der User das freigegeben hat.
- Kleine GitHub-Kommentare sind ok, wenn sie verifizierte lokale Fakten oder
  Testergebnisse knapp zusammenfassen.
- Nach relevanten Aenderungen Tests ausfuehren und Ergebnis dokumentieren.
- Nach GitHub-Arbeit Project Board / Issue-Status pruefen und, falls moeglich,
  aktualisieren.

## Handoff-Regel

Bevor ein Agent stoppt oder einen Branch uebergibt, muss er in
`docs/agent-status.md` eine kurze Handoff-Notiz ergaenzen oder aktualisieren.

Format:

```text
### YYYY-MM-DD HH:MM Europe/Berlin - <Agent> - <Branch oder PR>
- Ziel:
- GitHub-Bezug:
- Status:
- Claim/Issue-Status:
- Geaenderte Dateien:
- Tests:
- Neu gewonnenes Wissen:
- Offene Risiken:
- Naechster sinnvoller Schritt:
```

Wenn die Aenderung nur lokal bleiben soll, wird das ausdruecklich in der
Handoff-Notiz markiert.

## GitHub Board Workflow

GitHub ist die Planungsquelle:

1. Issue lesen.
2. Lokalen Code gegen Issue pruefen.
3. Branch erstellen.
4. Umsetzung in kleinen Commits.
5. Tests laufen lassen.
6. PR mit Issue-Bezug erstellen.
7. Board/Issue-Status aktualisieren oder den User informieren, wenn Rechte
   fehlen.
8. Handoff eintragen.

## Gemeinsamer Sprachgebrauch

- "Fertig" heisst: Code ist committed, relevante Tests sind dokumentiert, PR
  oder Merge-Status ist bekannt, und offene Risiken sind genannt.
- "Gruen" heisst: Die relevanten GitHub Checks sind erfolgreich. Lokale Tests
  allein sind noch kein Beweis fuer gruenes GitHub CI.
- "Geplant" heisst: im Produkt sichtbar oder im Issue beschrieben, aber noch
  ohne produktive Datenquelle oder Implementierung.

## Claude Code Startup Prompt

Dieser Prompt kann Claude Code gegeben werden, damit er denselben Arbeitsmodus
wie Codex nutzt:

```text
Lies zuerst AGENTS.md, CLAUDE.md, docs/agent-collaboration.md und docs/agent-status.md.
Fuehre danach den Session Intake aus: Git-Status, offene PRs, offene Issues und docs/agent-status.md pruefen.
Wenn ich kein Issue nenne, waehle automatisch das naechste bearbeitbare GitHub Issue nach der dokumentierten Prioritaetsregel und claime es.
Nutze GitHub Issues und das GitHub Project Board als Planungsquelle fuer DNMedia1/YourCalendar.
Private Knowledgebase-Dateien unter .claude/ oder .snapshots/ darfst du lesen, wenn sie lokal existieren, aber nicht committen.
Arbeite nur auf einem eigenen Branch, verwende Conventional Commits und aktualisiere vor dem Stoppen docs/agent-status.md mit Intake, Wissen und Handoff.
Setze keine fremden lokalen Aenderungen zurueck. Wenn ein Issue unklar, veraltet, doppelt oder riskant ist, frage zuerst nach.
```
