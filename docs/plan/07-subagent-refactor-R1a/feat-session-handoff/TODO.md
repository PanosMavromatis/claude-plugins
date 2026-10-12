# feat/session-handoff

**Status**: merged — PR #16 — 2026-10-12
**Created**: 2026-10-12
**Revision**: 07-subagent-refactor-R1a
**Subgoal**: 2. `/workflow-coding:session-handoff` writes `tmp/session-handoff.md` in three parts (Keep / Drop / Say where), and its text works when followed as a plain file. A new root `CLAUDE.md` holds the one conditional line that makes the next session read the handoff first and archive it once the user confirms, and the workflow's `# Compact instructions`.
**Layout**: per-goal

## Goals

- [x] 01 — Write the session-handoff command
- [x] 02 — Create the root CLAUDE.md
- [x] 03 — Dogfood the handoff as a plain file
