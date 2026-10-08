# chore/move-plan-history

**Created**: 2026-10-08
**Base**: main at 954f67e
**Status**: active

## Purpose

Executes subgoal 2 of revision `05-subagent-refactor-R0`: move `workflow-claude`'s
historical plan tree out of the plugin and into the repository's own plan tree at
`docs/plan/workflow-claude/`, so the marketplace has one plan tree and the plugin
directory ships only what the plugin runs.

## Scope

- `git mv plugins/workflow-claude/docs/plan/ docs/plan/workflow-claude/`
- Stamp the moved master plan closed and confirm every moved branch plan is stamped
  `merged`, so the old driver's glob rung offers none of them as active.
- Repoint references to the old location, and confirm nothing the plugin runs reads its
  own `docs/`.
- Index revisions 02–04 under the root master plan's `## Closed revisions`.
- Carry goal 1's held closing notes and the CLI-layout `.claude/settings.json`.

## Context

- Root master plan: `docs/plan/TODO.md`, revision `05-subagent-refactor-R0`, subgoal 2.
- Goal 1 landed as PR #1.
- `dp-compile` has no plan tree, so nothing moves for it.

## Notes
