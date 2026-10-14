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
- The e2e merge sessions allow `Bash(rm /tmp/pr-body-:*)` by `--allowedTools`, but `:*` is a trailing ` *`, so the rule never matched `rm /tmp/pr-body-<branch>.md`; that is why r4 saw it denied "even when allowed"
- The e2e run is paid; the user runs it

## Notes

- 2026-10-14, goal 01: a command's `allowed-tools` grant lasts one turn, clearing with the user's next message, measured with `dev/grant-lifetime/` headless (run2) and interactively; so a write made after the user replies to a CONFIRM FIRST step runs under the user's own settings, not the command's grant. Recorded in the plugin's `CLAUDE.md` beside the convention, with the `:*` trap
- 2026-10-14, goal 02: the convention now scopes a grant to what a command does before it waits for the user: additive grants stay for one-turn runs, destructive verbs stay off since they prompt in any turn, a write confirmed in a later turn is gated by the CONFIRM FIRST prose and the user's own settings, and a grant the command never runs is removed. No command was rewritten; confirming through `AskUserQuestion`, which would keep the grant, was weighed and left aside
- 2026-10-14, goal 03: `Glob` and `Grep` are gone from `new-branch.md`, `step.md`, `hitl-step.md` and `smart-commit.md`, and `Bash(find:*)` and `Bash(cat:*)` from `smart-commit.md`: read-only tools need no grant inside the repository, and no command's own text runs those shell reads. `/smart-merge`'s `gh` fallback now writes the PR body to the scratchpad, or else `/tmp/pr-body-<repository>-<flattened-branch>.md`, reads any leftover first, and never deletes it, so no `rm` is left to prompt; goal 04 drops the e2e harness's allowance for it
