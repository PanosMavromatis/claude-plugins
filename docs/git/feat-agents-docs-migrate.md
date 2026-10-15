# feat/agents-docs-migrate

**Created**: 2026-10-15
**Base**: main at 5b9262e
**Status**: active

## Purpose

R2 subgoal 9. One command, `/agents-docs-migrate`, takes a repository from a legacy `CLAUDE.md`, or from this plugin's dispatcher layout, to §4.3's target: a hand-authored `AGENTS.md` of 200 lines or fewer, one guide per subagent at `docs/agents/<guide>/AGENTS.md`, dated history under `docs/agents/_history/`, and no `CLAUDE.md` unless the shim is needed. A new read-only agent, `docs-classifier`, proposes where each section goes; the command makes every write, after the user confirms. It replaces `/agents-docs-init` and `/agents-docs-codex-init`, which are removed. Since PR #29 the build refuses the dispatcher layout those two write, so until this lands a consumer has no supported way into the new layout.

## Scope

- `plugins/workflow-coding/agents/docs-classifier.md`, new, per §4.1's row: sonnet; `Read, Grep, Glob, Bash(find:*)`; returns a destination table with flagged uncertainties.
- `plugins/workflow-coding/commands/agents-docs-migrate.md`, new, per §4.3: it detects the three states; Checkpoint 1 shows the destination table; the moves are verbatim, then Checkpoint 2 shows the results; the one destructive step comes last, CONFIRM FIRST; monorepo components are targets; the Codex sidecar becomes the `codex-review/` guide step.
- The version check and the two-line `@AGENTS.md` shim, per D-N6, with the `CLAUDE.local.md` check.
- `commands/agents-docs-init.md` and `agents-docs-codex-init.md` removed, and their mentions in the plugin's `README.md`, `CLAUDE.md` and `_meta/plugin-conflict-report.md` command list replaced.
- An end-to-end run on a copy of `tmp/pfsmgraph`, the dispatcher entrance, and on a repository with one legacy `CLAUDE.md`.

## Context

- Master plan: R2 subgoal 9, `docs/plan/08-subagent-refactor-R2/_TODO.md:71`. Builds on subgoal 7 (PR #29), after which the build reads only `codex-review/` guides and refuses the dispatcher layout, and follows the agent conventions subgoal 8 set for `docs-sync` (PR #30).
- Design: `tmp/subagent-refactor-plan.md` §4.1 (the agent's row, line 283, and the conventions every agent follows, bodies under 3,000 characters), §4.3 (the target layout and `/agents-docs-migrate`), D-N6 (the shim), §7.7 (the migration's verification) and §8 (the `CLAUDE.local.md` row).
- §4.1 asks of every agent first whether the job needs judgement or only rules. Placing prose needs judgement, so it is the agent's; detecting the state, comparing versions and checking that a move is verbatim are rules, so they belong in scripts with `problem:`/`fix:` diagnostics.
- `tmp/pfsmgraph` holds the dispatcher layout: `CLAUDE.md`, `docs/agents/{core,claude,codex}.md`, a generated `AGENTS.md` and `AGENTS.override.md`.
- Subgoal 12 owns §4 of `_meta/plugin-conflict-report.md`; subgoal 14 owns the release notes.
- The installed plugin is 0.10.1, so this branch's commands reach a session only at 0.11.0 (subgoal 14). End-to-end runs load the branch's plugin with `--plugin-dir`, as `dev/docs-sync-e2e/` does.

## Notes
