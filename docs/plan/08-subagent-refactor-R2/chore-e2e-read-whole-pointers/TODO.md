# chore/e2e-read-whole-pointers

**Status**: merged — PR #23 — 2026-10-13
**Created**: 2026-10-13
**Revision**: 08-subagent-refactor-R2
**Subgoal**: 1. A full end-to-end run checks the five pointers `fix/command-phrasing` reworded. Each tells a session to `Read` `smart-commit.md` whole and never `grep` or `ls` it. The run is recorded, and any pointer a session still searches around is reworded.
**Layout**: per-goal

## Goals

- [x] 01 — Run every scenario that reaches a pointer
- [x] 02 — Reword any pointer a session searched around
- [x] 03 — Record the run in the e2e README
