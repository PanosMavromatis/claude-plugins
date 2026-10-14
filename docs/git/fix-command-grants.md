# fix/command-grants

**Created**: 2026-10-14
**Base**: main at aa4ac86
**Status**: active

## Purpose

R2 subgoal 5. The plan commands' `allowed-tools` grant tools their sessions never use, and one deletion the `gh` path always runs is refused. The plugin's "additive yes, destructive no" convention also rests on an assumption nobody has measured: that a grant still covers a write made after the user confirms it, though the docs say a grant clears when the user sends the next message. This branch measures how long a grant lasts, revises the convention by the result, and removes or replaces the grants the R1 → R1a handoff lists.

## Scope

- a measurement of whether an `allowed-tools` grant outlives its turn, recorded with its method in the plugin's `CLAUDE.md`
- the "Scoped `allowed-tools`" convention in `plugins/workflow-coding/CLAUDE.md`, revised by the measurement
- `Glob` and `Grep` in `commands/new-branch.md`, `step.md` and `hitl-step.md`; `Bash(find:*)` and `Bash(cat:*)` in `commands/smart-commit.md`; the `rm /tmp/pr-body-<branch>.md` at `smart-merge.md:180`
- an e2e run of e1, e3 and e4

## Context

- R2 subgoal 5: `docs/plan/08-subagent-refactor-R2/_TODO.md:55`
- `/agents-docs-update`, `/agents-docs-init` and `/agents-docs-codex-init` are left to subgoals 8 and 9, which rewrite or remove them
- `smart-commit.md` also grants `Glob` and `Grep`, which the Scope does not list
- The e2e merge sessions allow `Bash(rm /tmp/pr-body-:*)` by `--allowedTools`, yet the `rm` is denied even so (run r4), and `check.py` reports it as a documented gate
- The e2e run is paid; the user runs it

## Notes
