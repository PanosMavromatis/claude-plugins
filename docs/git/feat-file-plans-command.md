# feat/file-plans-command

**Created**: 2026-08-30
**Base**: main at 845de84
**Status**: active

## Purpose

Automate the plan-filing sweep. `docs/plan/` gains one flat directory per merged branch, and filing them into revision directories is currently manual. It does not need to be: `/new-branch` writes each plan's `> **Branch:**` backlink beneath a specific `## Subgoals — revision N` heading, so a plan's revision is already recorded at creation time and recoverable mechanically.

Ships as a read-only script plus a command that acts on its output, mirroring the `/agents-docs-build` split already in this plugin.

## Scope

- `scripts/file-plans.sh` — read-only, deterministic, prints proposed `git mv` commands and a report. Never moves anything itself.
- `/file-plans` — runs the script, presents the proposal, confirms, executes, commits on a branch.
- Report rather than guess for the two derivable-failure cases.
- README and `CLAUDE.md`: the sweep section becomes "run `/file-plans`", with the manual `awk` kept as the underlying mechanism.

## Context

The last subgoal of revision 3, and deliberately last: `/smart-merge`'s PR pointer had to stop being a path first (PR #13), or an automated sweep would silently invalidate a batch of permanent records on every run.

Two cases resist derivation and must be reported, never guessed:

- **No backlink** — a branch created without `/new-branch`, or one whose subgoal was never recorded. There is no revision to derive.
- **A heading with no revision number** — this repo's own `## Subgoals` for revision 1, which predates the convention.

Both leave the plan flat, which is the safe outcome: a plan in the wrong revision directory is worse than one that was never filed, because the error is invisible once it is filed.

## Notes

- `git mv` stays off the command's `allowed-tools` per the additive-yes/destructive-no rule, so the harness prompt stands as a second gate behind the command's own confirmation.
- The script must tolerate being run on a repo with no master plan, no plan directories, or a `TODO.md` master plan.
