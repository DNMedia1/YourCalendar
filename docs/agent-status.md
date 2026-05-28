# Agent Status And Handoffs

Dieses Dokument ist der gemeinsame Arbeitsstand fuer Codex, Claude Code und
weitere Agenten. Es ersetzt nicht GitHub Issues, sondern gibt schnellen Kontext,
damit Agenten nicht gegeneinander arbeiten.

## Aktueller Repo-Stand

- Stand: 2026-05-28 17:58 Europe/Berlin.
- `main` ist auf GitHub nach PR #43 wieder gruen.
- Letzter bekannter `main`-Commit: `2d49322 fix(ci): restore merged catalog checks`.
- App Checks und Import Feeds waren nach diesem Stand erfolgreich.
- Private Knowledgebase-Dateien bleiben lokal und duerfen nicht committed
  werden.

## Aktive Arbeitsregeln

- Vor neuer Arbeit GitHub Issues/Project Board pruefen.
- Wenn der User kein konkretes Issue nennt, naechstes Issue nach
  `docs/agent-collaboration.md` automatisch auswaehlen.
- Ausgewaehltes Issue claimen oder fehlende GitHub-Rechte dokumentieren.
- Pro Task eigenen Branch nutzen.
- Keine fremden lokalen Aenderungen zuruecksetzen.
- Vor PR relevante Tests dokumentieren.
- Vor dem Stoppen unten eine Handoff-Notiz ergaenzen.

## Aktueller Intake-Snapshot

### 2026-05-28 17:58 Europe/Berlin - Codex - Intake
- Repo-Branch: `feat/agent-intake-workflow`
- Worktree clean: yes, vor Branch-Erstellung.
- GitHub PRs geprueft: keine PR-Doppelarbeit fuer diese reine Workflow-Doku geprueft.
- Offene Issues geprueft: `gh issue list --repo DNMedia1/YourCalendar --state open --limit 20`.
- Gewaehltes Issue: none.
- Warum dieses Issue: Der User fragte nach Prozess-/Wissensaustausch-Regeln, nicht nach Umsetzung eines bestehenden Produkt-Issues.
- Claim-Status: kein GitHub-Issue-Claim, weil kein konkretes Issue betroffen ist.
- Branch: `feat/agent-intake-workflow`
- Erwartete Dateien: `AGENTS.md`, `CLAUDE.md`, `docs/agent-collaboration.md`, `docs/agent-status.md`.
- Erste Checks: `git status --short --branch`, offene GitHub Issues gelesen.
- Blocker/Unsicherheit: Kein gesondertes GitHub-Label-Schema vorhanden; Auswahlregel nutzt daher Titel-Prioritaeten wie `[P0]`, `[P1]`, `[P2]`.

## Handoff Log

### 2026-05-28 17:58 Europe/Berlin - Codex - feat/agent-intake-workflow
- Ziel: Verbindliches Intake-, Issue-Pickup- und Wissensaustausch-Schema fuer Agenten ergaenzen.
- GitHub-Bezug: Kein Produkt-Issue; Prozessanforderung aus User-Chat.
- Status: Lokale Doku-Aenderung fertig, bereit fuer PR.
- Claim/Issue-Status: Kein Issue geclaimt, da Workflow-Doku selbst betroffen ist.
- Geaenderte Dateien: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/agent-collaboration.md`, `docs/agent-status.md`.
- Tests: `git diff --check`.
- Neu gewonnenes Wissen: Offene Issues nutzen aktuell hauptsaechlich Titel-Prioritaeten (`[P1]`, `[P2]`) und kaum Labels; die Auswahlregel muss deshalb Titel und Labels auswerten.
- Offene Risiken: Project-Board-Felder koennen ohne passende GitHub-Rechte eventuell nicht automatisch aktualisiert werden.
- Naechster sinnvoller Schritt: Committen, PR erstellen, GitHub Checks pruefen und nach gruenem CI mergen.

### 2026-05-27 18:40 Europe/Berlin - Codex - feat/agent-collaboration-protocol
- Ziel: Gemeinsamen Wissens- und Handoff-Standard fuer Codex, Claude Code und weitere Agenten im Repo anlegen.
- GitHub-Bezug: Noch kein Issue; reine Workflow-/Dokumentationsverbesserung.
- Status: Lokale Dokumentation angelegt, Branch aktiv.
- Geaenderte Dateien: `AGENTS.md`, `CLAUDE.md`, `docs/agent-collaboration.md`, `docs/agent-status.md`, `.gitignore`, `README.md`.
- Tests: `git diff --check`.
- Offene Risiken: GitHub Project Board wurde fuer diese reine Workflow-Doku nicht geaendert.
- Naechster sinnvoller Schritt: Branch committen, PR erstellen und nach gruenen Checks in `main` bringen, damit beide Agenten dieselbe Basis lesen.

### 2026-05-27 11:05 Europe/Berlin - Codex - main / PR #43
- Ziel: Rote GitHub Actions nach Merge von `feat/sync-worktree` reparieren.
- GitHub-Bezug: PR #43, App Checks Run `26501676358`, Import Feeds Run `26505331364`.
- Status: Gemerged; `main` ist laut GitHub wieder gruen.
- Geaenderte Dateien: `web_app.py`, `web/app.js`, `import_jobs.py`, Tests und Performance-Doku.
- Tests: `python3 -B -m py_compile web_app.py yourcalendar_poc.py`, `python3 -B -m unittest discover -s tests -p 'test_*.py'`, `npm test`, `npm run build-storybook`, lokaler Server-Smoke-Test.
- Offene Risiken: Keine bekannten roten Checks. Alte fehlgeschlagene Runs bleiben in der Historie sichtbar, sind aber durch spaetere erfolgreiche Runs ueberholt.
- Naechster sinnvoller Schritt: Naechstes GitHub Issue/Board-Todo pruefen und auf eigenem Branch starten.
