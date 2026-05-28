# YourCalendar Agent Guide

This file is the shared entry point for all coding agents working in this
repository. Claude Code should also read `CLAUDE.md`; both files point to the
same repo-owned collaboration protocol.

## Required Reading

1. Current user instructions in the active chat.
2. This `AGENTS.md`.
3. `docs/agent-collaboration.md`.
4. `docs/agent-status.md`.
5. Relevant README, docs, tests, GitHub issues and pull requests for the task.

Local/private knowledge bases may exist under `.claude/` or
`.snapshots/.claude/knowledge_base/`. They can be used as personal workflow
support when present, but they are not the shared source of truth and must not
be committed.

## Project Rules

- Be explicit about uncertainty. Do not invent APIs, issue state, data sources
  or implementation status.
- Keep the Yobsti/Core connection untouched unless the user explicitly asks for
  changes there.
- Treat GitHub Issues and the GitHub project board as the shared planning state.
- Work on a task branch, not directly on `main`, unless the user explicitly
  asks for a fast-forward sync or emergency fix.
- Use Conventional Commits.
- Keep private files, tokens, `.env`, `.claude/` and local knowledge-base
  snapshots out of Git.
- At the start of every task, run the session intake workflow from
  `docs/agent-collaboration.md`.
- If the user has not named a task or issue, select the next GitHub issue using
  the priority rules in `docs/agent-collaboration.md` and claim it before
  implementation.
- Before stopping, update the handoff state described in
  `docs/agent-collaboration.md`.

## Default Checks

Run the smallest relevant checks for the change. For broad repo changes, prefer:

```bash
python3 -B -m py_compile web_app.py yourcalendar_poc.py
python3 -B -m unittest discover -s tests -p 'test_*.py'
npm test
npm run build-storybook
```
