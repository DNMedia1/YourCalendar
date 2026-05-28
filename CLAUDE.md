# Claude Code Project Guide

Claude Code must use the same shared project context as Codex.

## Required Reading

1. Current user instructions.
2. `AGENTS.md`.
3. `docs/agent-collaboration.md`.
4. `docs/agent-status.md`.
5. Relevant README/docs/tests/GitHub issues for the task.

## Local Knowledgebase

Local/private workflow knowledge may exist here:

- `.snapshots/.claude/knowledge_base/CLAUDE.md`
- `.snapshots/.claude/knowledge_base/00_Start/How-To-Use-This-Knowledge-Base.md`
- `.claude/`

Read these files when they exist and are useful, but treat them as private
workflow support. Do not stage or commit them. Durable project knowledge must
be distilled into tracked docs, GitHub issues or PR descriptions.

## Guardrails

- Do not invent missing APIs, files, data sources, costs or implementation
  status.
- Mark assumptions clearly.
- Keep the Yobsti/Core connection untouched unless explicitly asked.
- Run the session intake workflow from `docs/agent-collaboration.md` before
  choosing work.
- If no task is named by the user, pick and claim the next GitHub issue using
  the documented priority rules.
- Work on a task branch.
- Use Conventional Commits.
- Update `docs/agent-status.md` before stopping or handing work to another
  agent.
