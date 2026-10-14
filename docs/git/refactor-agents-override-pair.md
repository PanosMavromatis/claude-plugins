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
- 2026-10-14, goal 03: `protect-agent-docs.py` blocks a Write, Edit or MultiEdit only of a generated `AGENTS.override.md`, at the root or in a component, and only when its guide exists: `docs/agents/codex-review/AGENTS.md`, or `docs/agents/<path>/codex-review/AGENTS.md` for `<path>/AGENTS.override.md`. `AGENTS.md` and `CLAUDE.md` pass everywhere; the `CLAUDE.md` rule went with its comment-edit exception, and the hook is about 100 lines, from 220. `_meta/plugin-conflict-report.md` §4 still describes the old scope, for R2 subgoal 12
- 2026-10-14, goal 04: `dev/agents-docs/suite.py` tests the build, the check and the hook together on ten fixture repositories: 43 cases, the scripts twice under each Bash and the hook twice under each `python3`, run by its shebang as `hooks.json` runs it; 45 mutants, all killed, with `--first` stopping each run at its first failure (925 s down to 170 s). A check's temporary directory is found by a logging `mktemp`, since macOS's prefers its own temporary directory to `TMPDIR`. `c08` pins that the check counts only its own lints, not the build's warnings on dispatcher-layout sources
- 2026-10-14, goal 05: `/agents-docs-build` and `/agents-docs-check` describe only the `AGENTS.override.md` pair and the two lints, the check with a third outcome, the build's `error:` relayed. The plugin's README and `CLAUDE.md` describe the build, the check and the hook as goals 01–03 left them, and each agent-docs section says the dispatcher layout `/agents-docs-init` still writes is the one the build refuses. The old claims remain in `/agents-docs-update`, for subgoal 8, and in the two init commands, which subgoal 9 removes
