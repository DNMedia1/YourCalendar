# Agent Collaboration Protocol

Stand: 2026-05-27.

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

Vor jeder Umsetzung:

1. `git status --short --branch` pruefen.
2. `docs/agent-status.md` lesen.
3. Offene GitHub Issues/PRs pruefen, wenn die Aufgabe Planung, Board oder
   Prioritaet betrifft.
4. Klaeren, welches Issue oder welcher Task bearbeitet wird.
5. Einen eigenen Branch verwenden, z.B. `feat/issue-25-mobile-layout` oder
   `fix/ci-catalog-checks`.
6. Bestehende Aenderungen anderer Agenten nicht zuruecksetzen.

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
- Geaenderte Dateien:
- Tests:
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
Nutze GitHub Issues und das GitHub Project Board als Planungsquelle fuer DNMedia1/YourCalendar.
Private Knowledgebase-Dateien unter .claude/ oder .snapshots/ darfst du lesen, wenn sie lokal existieren, aber nicht committen.
Arbeite nur auf einem eigenen Branch, verwende Conventional Commits und aktualisiere vor dem Stoppen docs/agent-status.md.
Setze keine fremden lokalen Aenderungen zurueck. Wenn ein Issue unklar, veraltet, doppelt oder riskant ist, frage zuerst nach.
```
