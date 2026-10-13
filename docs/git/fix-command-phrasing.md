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
- 2026-10-13, goal 01 closed: `/hitl-step` and `/step` open Step 3 with the phrasing rule, and grant `git show` and `git ls-files`, read-only: two of the r8–r10 `git -C` denials (e5's `show`, e4-step's `ls-files`) used subcommands neither command granted even plainly, so the rule alone would not have cleared them. Step 1 stays in lockstep.
- 2026-10-13, goal 02 closed: `/new-branch` states the rule for every step in its Guidelines, and "each alone" at steps 3 and 8. Its r9 denials (e3, e4) were not `git -C`: each session searched the plugin's directory with chained `ls` and `grep` for a command `/new-branch` points at, `/smart-commit` Step 3 or `/hitl-step`'s form. So step 8 now gives `smart-commit.md`'s path to `Read`, and step 7 says its block is the whole form; goal 03 changes the other four `/smart-commit` pointers the same way.
- 2026-10-13, goal 03 closed: every command that grants `git` states both halves of the rule in two fixed phrases, "never `git -C <path>`" and "every command alone", each whole on one line, the form goal 04's check will look for; `/session-handoff` gains the `-C` half though it grants no `git`. The four `/smart-commit` pointers take `/new-branch`'s `Read`-the-path wording, and the plugin's `CLAUDE.md` records the convention and why `Bash(git -C:*)` is never granted. A prototype of the check passes on all 11 commands that grant `git`; before this goal, 8 lacked the `-C` phrase.
- 2026-10-13, goal 04 closed: `dev/command-phrasing/check.py` fails any command whose `allowed-tools` grants `git` without both phrases, naming the command and the phrase; its suite has 35 cases, 22 of them generated from the plugin by removing each phrase from each command in turn, and 13 mutants, all killed. The root `README.md` lists it, and the plugin's `CLAUDE.md` names it as the check the one-line rule is for.
- 2026-10-13, goal 05, before the run: the e2e grader's `alone()` now runs on the `/new-branch` and step sessions, with a new `git -C` check. Graded on the old logs, it showed that e1 and e3 (r9) and e4 (r10) chained granted commands with no denial: Claude Code checks a chain part by part, and refuses the whole command if any part is not granted. The reason the commands gave, that a chain matches none of the entries, was wrong; 14 places now give the measured one, the rule and its two phrases unchanged.
