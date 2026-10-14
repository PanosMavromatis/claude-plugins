# refactor/agents-override-pair

**Created**: 2026-10-14
**Base**: main at b720144
**Status**: active

## Purpose

R2 subgoal 7. Under §4.3 a consumer's `AGENTS.md` becomes hand-authored, the one file every agent loads, and only `AGENTS.override.md` stays generated, from the Codex reviewer's guide at `docs/agents/codex-review/AGENTS.md`. This branch shrinks the build to that pair; keeps the check's in-sync test and adds two lints that warn on an `AGENTS.md` over 200 lines or carrying a dated sentence; and narrows the hook to protect the generated `AGENTS.override.md` only, so `AGENTS.md` and `CLAUDE.md` can be edited.

## Scope

- `plugins/workflow-coding/scripts/build-agents-md.sh` and `check-agents-md.sh`, for root and component paths
- `hooks/protect-agent-docs.py`, its sentinel becoming `docs/agents/codex-review/AGENTS.md`
- a suite under `dev/agents-docs/`, on fixtures in the §4.3 layout
- `commands/agents-docs-build.md` and `agents-docs-check.md`, and the plugin's README and `CLAUDE.md`

## Context

- R2 subgoal 7: `docs/plan/08-subagent-refactor-R2/_TODO.md:63`
- Design: §4.3 of `tmp/subagent-refactor-plan.md`
- Subgoals 8 (`docs-sync`) and 9 (`/agents-docs-migrate`, which removes `/agents-docs-init` and `/agents-docs-codex-init`) build on it. Until 9 lands, a consumer in the dispatcher layout has no way into the new one, so none of this is released before subgoal 14
- This repository has no `docs/agents/`, so the change is tested on fixtures only

## Notes

- 2026-10-14, goal 01: `build-agents-md.sh` now builds only `AGENTS.override.md`, from every `codex-review/AGENTS.md` under `docs/agents/`: the root's from `docs/agents/codex-review/`, a component's from `docs/agents/<path>/codex-review/`, so the other guide directories produce nothing. In the dispatcher layout it exits 1 naming the move, and it warns on old sources left beside the guides. The commands and the plugin's docs describe the old build until goal 05
- 2026-10-14, goal 02: `check-agents-md.sh` keeps its in-sync check, which since goal 01 compares only the pair, and lints every `AGENTS.md` git lists outside `docs/agents/`, tracked or new and not ignored: one over 200 lines, and each dated line (`20\d\d-\d\d-\d\d`, up to five line numbers). Warnings go to stderr and are counted in the last line; the exit status still means only the pair's sync, and the lints run even when the pair has drifted
