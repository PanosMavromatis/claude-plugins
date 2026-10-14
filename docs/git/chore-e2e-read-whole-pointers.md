# chore/e2e-read-whole-pointers

**Created**: 2026-10-13
**Base**: main at d83bb1f
**Status**: active

## Purpose

R2 subgoal 1. `fix/command-phrasing` (PR #19) reworded five pointers so `/new-branch`, `/smart-merge` (twice), `/master-plan` and `/close-revision` tell a session to `Read` `smart-commit.md` whole and never `grep` or `ls` it, since in a real install the plugin cache is outside the repository and a shell read there prompts. Run r11 came before that wording. This branch runs the e2e suite once on the 0.10.1 command text, rewords any pointer a session still searches around, and records the run.

## Scope

- Make `check.py` fail a session that reads or searches the plugin copy's directory from the shell; today it only prints commands starting `grep`, `rg` or `find`
- A run of every scenario that commits and so reaches a pointer (the user runs it; ≈ $8, from r11's $5.96 and r6's $2.39)
- Reword any pointer a session searched around, with `dev/command-phrasing` passing
- Record the run in `dev/per-goal-e2e/README.md`

## Context

- R2 subgoal 1: `docs/plan/08-subagent-refactor-R2/_TODO.md:39`; R1a subgoal 6's Done line; PR #19; run r11 in `fix-command-phrasing`'s goal 05
- The pointers: `plugins/workflow-coding/commands/master-plan.md:145`, `new-branch.md:206`, `smart-merge.md:137` and `:236`, `close-revision.md:115`
- Merge sessions run with `--add-dir /tmp` (`dev/per-goal-e2e/run.sh:73`), and the plugin copy sits under `$LOCATE_PLAN_WORK`, so a shell read of it there is not denied: only `check.py` can show it
- m3 (`--dry-run`) and c3 (refused) never commit, so they reach no pointer

## Notes
