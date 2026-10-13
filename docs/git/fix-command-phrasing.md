# fix/command-phrasing

**Created**: 2026-10-13
**Base**: main at bf0c263
**Status**: active

## Purpose

Have sessions phrase each command so the command's `allowed-tools` matches it: `git` run from the repository as `git <subcommand>`, never `git -C <path>`, and every command alone, never chained or piped. In `feat/goal-file-subgoals`' e2e runs, r9 and r10, sessions were refused commands their command grants: `git -C … status` where `git status` is allowed, `ls -R … | grep … | head`, `git log …; grep …`. The commands state the run-alone rule where they run their scripts, not where a session does its work, and say nothing of `-C`. It predates 0.10.1 (e5 in r8) but shows more often now that richer subgoals take more checking. This is R1a subgoal 6, and it ships in `workflow-coding` 0.10.1.

## Scope

- `commands/hitl-step.md` and `commands/step.md`: the rule where a session does its work and checks its subgoals, Step 1 left in lockstep.
- `commands/new-branch.md`.
- Every other command whose `allowed-tools` grants a `git` subcommand: `smart-merge`, `smart-commit`, `master-plan`, `close-revision`, `clean-gone`, `agents-docs-update`, `agents-docs-init`, `agents-docs-codex-init`; and the plugin's `CLAUDE.md` "Scoped `allowed-tools`" convention.
- A dev check that fails any command granting a `git` subcommand without stating the rule.
- `dev/per-goal-e2e/check.py`: `alone()` and a `git -C` check on the `/new-branch` and step sessions; a real run of e1, e3, e4 and e5.
- Not by granting `Bash(git -C:*)`: a permission rule matches by prefix, so it would also match `git -C <path> push`, which the gates exist to stop.

## Context

- R1a subgoal 6 is at `docs/plan/07-subagent-refactor-R1a/_TODO.md:74`, settled at `:52`; it was added on `feat/goal-file-subgoals` (PR #18), whose goal 05 records the evidence.
- The denials, r9 and r10, against r7 and r8 with the same model and Claude Code (2.1.296): `git -C` in e4-step and e5, a pipe in e1-step, a chain in e3; e5's identical denial in r8 shows it predates subgoal 5.
- `/smart-merge`'s Guidelines already state the rule in full ("Run every command alone … `allowed-tools` matches a single command, so a chain matches none of its entries"), as do `/master-plan` and `/close-revision`; `/hitl-step`, `/step` and `/new-branch` state it only for their scripts.
- `dev/per-goal-e2e/check.py`'s `alone()` already grades the merge and revision sessions, not the `/new-branch` or step sessions.
- This branch runs on the installed 0.10.0, so its goal files' subgoals are drafted by hand from the Acceptance line, as on the last three branches.

## Notes

- 2026-10-13: the goal files are written with their subgoals, by hand, since the installed `/new-branch` is still 0.10.0.
