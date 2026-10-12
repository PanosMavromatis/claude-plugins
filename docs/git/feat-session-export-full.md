# feat/session-export-full

**Created**: 2026-10-12
**Base**: main at bbd046f
**Status**: active

## Purpose

Add `/workflow-coding:session-export-full`, which exports a session's whole JSONL log as readable Markdown, compactions included, because `/export` writes only what is in context and loses everything before a compaction. The rendering moves from `tmp/export_session.py` into the plugin as `scripts/export-session.py`, with a no-model suite, and a thin command drives it. Subagent transcripts are optional, and the output goes outside the repository. This is R1a subgoal 3, and it ships in `workflow-coding` 0.10.1.

## Scope

- `plugins/workflow-coding/scripts/export-session.py`, started from `tmp/export_session.py` (untracked, 114 lines).
- Its suite under `dev/export-session/`, with a case for each of the four measured defects.
- Resolving a session by its current name through `<uuid>/custom-title.json`, and subagent transcripts (`<uuid>/subagents/`) only on request.
- `plugins/workflow-coding/commands/session-export-full.md` (new), stating the verified `cleanupPeriodDays` default.
- An acceptance run: a real session exported to a path outside the repository.
- Not in scope: documenting the command in the READMEs (R1a subgoal 4, the release).

## Context

- R1a subgoal 3 is at `docs/plan/07-subagent-refactor-R1a/_TODO.md:62`, with its settled decisions at `:34`–`44` and `:47`.
- The four defects, measured 2026-10-11 on the R1 session's log (55 MB, 16 compactions, 0.28 s): double-encoded em dashes, the `/compact` instructions never captured, a title hard-coded to `m2-tier-1a` (all three fixed that day), and a renamed session carrying several `custom-title` records (still open).
- `cleanupPeriodDays`: Claude Code's costs page (fetched 2026-10-12) says session data older than it is removed at startup, "30 days by default".
- The export script stays Python (settled 2026-10-12, `_TODO.md:47`).

## Notes

- 2026-10-12: the goal files are written with their subgoals, by hand from the subgoal's Acceptance line, until R1a subgoal 5 ships in 0.10.1.
- 2026-10-12, goal 01: `scripts/export-session.py` is ported, byte-identical in output to `tmp/export_session.py` on a real 15 MB log, with UTF-8 named on both ends: under a Latin-1 locale the original crashes and the port does not. For R1a subgoal 4: `plugins/workflow-coding/README.md:11` says every script but the two agent-docs ones serves the plan workflow and is read-only, and `export-session.py` is neither.
