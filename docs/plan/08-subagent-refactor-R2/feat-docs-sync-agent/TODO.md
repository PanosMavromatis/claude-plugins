# feat/docs-sync-agent

**Status**: active
**Created**: 2026-10-14
**Revision**: 08-subagent-refactor-R2
**Subgoal**: 8. `agents/docs-sync.md` does `/agents-docs-update`'s work. `/agents-docs-update` thins to a wrapper around it, and `/smart-commit` spawns it with the `Agent` tool. Two things are tested before the agent is built: that `protect-agent-docs.py` fires on a subagent's `Edit`, and that `dp-compile`'s gate still sees the docs the agent stages.
**Layout**: per-goal

## Goals

- [x] 01 — Hooks inside a subagent and the dp-compile gate are tested before the agent is built
- [x] 02 — agents/docs-sync.md does /agents-docs-update's work
- [x] 03 — /agents-docs-update thins to a wrapper around docs-sync
- [x] 03a — A hook stops docs-sync committing or pushing
- [ ] 04 — /smart-commit spawns docs-sync with the Agent tool
- [ ] 05 — The §7.7 cases pass end to end
