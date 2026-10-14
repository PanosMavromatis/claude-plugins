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
