# feat/docs-sync-agent

**Created**: 2026-10-14
**Base**: main at ad4e000
**Status**: active

## Purpose

R2 subgoal 8. `/agents-docs-update`'s work moves into a subagent, `agents/docs-sync.md`, so the doc sync runs outside the main session's context: `/agents-docs-update` thins to a wrapper around it, and `/smart-commit` spawns it with the `Agent` tool. Two things are tested before the agent is built: whether `protect-agent-docs.py` fires on a subagent's `Edit`, and whether `dp-compile`'s gate still sees the docs the agent stages.

## Scope

- the two tests, run and recorded before any agent text is written
- `plugins/workflow-coding/agents/docs-sync.md` (new): §4.1's row and conventions, §4.3's routing, a rebuild of `AGENTS.override.md` only on a `codex-review/` change, `memory: project`
- `commands/agents-docs-update.md` and `commands/smart-commit.md`
- `.claude/agent-memory/`, committed
- §7.7's cases, end to end

## Context

- R2 subgoal 8: `docs/plan/08-subagent-refactor-R2/_TODO.md:67`
- Design: §4.1, §4.3, §7.7 and §8 of `tmp/subagent-refactor-plan.md`; D-N7 for the agent's memory
- Builds on subgoal 7 (PR #29): the build writes only `AGENTS.override.md`, and the hook protects only that file. `/agents-docs-update` still describes the dispatcher layout and calls the build on a `core.md` or `codex.md` change, which the new build refuses; this branch replaces that
- The `dp-compile` test and §7.7's cases need real sessions, which cost money: the user runs them
- A hook changed here is not live in this repository until 0.11.0 is installed (subgoal 14)

## Notes

- 2026-10-14, goal 01: `dev/subagent-hooks/` runs four headless haiku sessions on fixtures with this repository's plugins loaded by `--plugin-dir`. In run `s2`, `protect-agent-docs.py` fires on a subagent's `Edit`, between a blocked main-session control and a subagent edit of `AGENTS.md` that lands, so `/agents-docs-update` needs no `check-agents-md.sh` re-run; and `dp-compile`'s gate blocks the main session's commit, naming the kernel, having seen the `AGENTS.md` a subagent staged. Run `s1`'s gate case was void: `dp-compile` loaded alone by `--plugin-dir` is dropped silently for its missing dependency, left for R4. The `Agent` tool ran each subagent in the background, so `/smart-commit` must commit after `docs-sync` hands back. A note under R2 subgoal 14 records that until 0.11.0 a fresh install gets `main` labelled 0.10.1
