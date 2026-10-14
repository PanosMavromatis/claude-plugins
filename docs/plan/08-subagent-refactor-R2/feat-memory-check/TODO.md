# feat/memory-check

**Status**: active
**Created**: 2026-10-14
**Revision**: 08-subagent-refactor-R2
**Subgoal**: 6. `/memory-check` per §4.8: a read-only `scripts/memory-check.sh` reports the size of each plan file a command reads whole, against a threshold. It comes with a suite and a thin command.
**Layout**: per-goal

## Goals

- [x] 01 — memory-check.sh reports each plan file's size and the totals
- [ ] 02 — A suite under dev/memory-check passes
- [ ] 03 — The token ratio and the threshold are calibrated and recorded
- [ ] 04 — /memory-check runs the script, diagnostic only
