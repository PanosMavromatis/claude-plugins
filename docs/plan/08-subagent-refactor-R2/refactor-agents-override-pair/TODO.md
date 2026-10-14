# refactor/agents-override-pair

**Status**: merged — PR #29 — 2026-10-14
**Created**: 2026-10-14
**Revision**: 08-subagent-refactor-R2
**Subgoal**: 7. The generated agent docs shrink to the `AGENTS.override.md` pair (§4.3). The build script builds only that pair, from `docs/agents/codex-review/AGENTS.md`. The check script keeps its in-sync check and gains two lints. The hook protects `AGENTS.override.md` only.
**Layout**: per-goal

## Goals

- [x] 01 — build-agents-md.sh builds only the AGENTS.override.md pair
- [x] 02 — check-agents-md.sh keeps its in-sync check and gains two lints
- [x] 03 — protect-agent-docs.py protects AGENTS.override.md only
- [x] 04 — A suite under dev/agents-docs checks the build, the check and the hook
- [x] 05 — The two commands and the docs describe the pair
