# feat/goal-file-subgoals

**Created**: 2026-10-12
**Base**: main at 8d7dd0e
**Status**: active

## Purpose

Make `/new-branch` write each per-goal goal file with its subgoals, never a stub. Today it writes `**Goal**: [ ]` and nothing under it, so a goal's acceptance criteria exist only if someone writes them by hand, as the last two branches did. `propose-branch-plan.sh` gains a `scope:` key reporting the master-plan subgoal's `Scope: … Acceptance: …` lines; the command drafts each goal's subgoals from them and the scope discussion; `locate-plan.sh` warns when the selected goal file has none; and `/step` and `/hitl-step` propose subgoals for such a goal before work starts. This is R1a subgoal 5, and it ships in `workflow-coding` 0.10.1.

## Scope

- `plugins/workflow-coding/scripts/propose-branch-plan.sh`: a `scope:` report key, the subgoal's continuation lines, or `—` for a standalone plan; cases in `dev/propose-branch-plan/`, and its spec.
- `plugins/workflow-coding/scripts/locate-plan.sh`: a warning on a selected goal file with no subgoals; a case in `dev/locate-plan/`, and its spec.
- `commands/new-branch.md`: step 7's per-goal template drafts each goal's subgoals, and a rule never to write a goal file with none; the plugin's `CLAUDE.md` on `/new-branch`.
- Step 2 of `commands/step.md` and `commands/hitl-step.md`: a goal with no subgoals gets them proposed before work starts.
- `dev/per-goal-e2e/check.py`: a real `/new-branch` run's goal files each hold a `- [ ]` subgoal.
- Every suite of a script that sources `lib/plan-rules.sh` still passes.
- Not committed: §4.2's "stub goal file" wording in `tmp/subagent-refactor-plan.md`, which is untracked.

## Context

- R1a subgoal 5 is at `docs/plan/07-subagent-refactor-R1a/_TODO.md:69`, settled at `:48`.
- The two scripts' specs sit in closed R1's branch plans, under `docs/plan/06-subagent-refactor-R1/`: `propose-branch-plan.sh`'s is `per-goal-layout-spec.md` in `feat-per-goal-layout`, and `locate-plan.sh`'s is `locate-plan-spec.md` in `feat-plan-locator`. A closed revision is a record, so where the new rules are written down is decided in goal 01.
- `dev/per-goal-e2e/` runs the real commands headless, at a cost ($4.18 for e1, e3 and e4 in r5); `check.py:137` already checks that `/new-branch` committed the doc, the index, the goal files and the backlink.
- `/step` and `/hitl-step` keep Step 1 byte-identical apart from the file name (the plugin's `CLAUDE.md`, "Plan-file lockstep"), so Step 2 changes go to both.

## Notes

- 2026-10-12: the goal files are written with their subgoals, by hand from the subgoal's Acceptance line, the last branch to need it.
- 2026-10-12, goal 01: `propose-branch-plan.sh` reports `scope:` after `subgoal:`: the rest of the subgoal's block, each line without its indent, and `—` when there is no subgoal; on R1a subgoal 5 it reports the `Scope: … Acceptance: …` line. The suite has 33 cases and 23 mutants; `b05` was rebuilt, since the scope block moved its context.
- 2026-10-12, goal 01 closed: the new rules go into the existing specs, amended in place and marked as added by this branch, though they sit in closed R1: `per-goal-layout-spec.md` gains `scope:` in its report and rules, and goal 02's warning goes into `locate-plan-spec.md` the same way.
- 2026-10-12, goal 02: `locate-plan.sh` warns, W12, when the selected goal file holds no subgoals, in the TODO model only, since R1's spec makes a DO goal file with no tasks the task itself. `w12` and `w12b` pin it, with mutants `r01` and `r02`; the suite has 85 cases and 29 mutants, and `locate-plan-spec.md` records W12 as an amendment.
- 2026-10-13, goal 02 closed: all six suites of the scripts that source `lib/plan-rules.sh` pass in place, 331 cases, with every mutant caught but `locate-plan`'s known equivalent `n05`; W12 changed no other suite's output.
- 2026-10-13, goal 03: `/new-branch` shows `scope:` in step 4 and drafts each goal file's subgoals from it in step 7, never writing a stub in the TODO model; a DO goal file gets tasks only when the scope splits the goal. Nothing parses the command's text, so goal 05's real e1 run is its check.
- 2026-10-13, goal 03 closed: the plugin's `CLAUDE.md` says `/new-branch` writes each goal file with its subgoals, and `per-goal-layout-spec.md`'s goal-file template shows them, under a rule marked as added by this branch.
- 2026-10-13, goal 04 closed: `/hitl-step`'s Step 2 proposes subgoals for a branch plan's goal with none, never for a master plan's item; `/step` is unchanged, since a DO goal with no tasks is its own task, and Step 1 stays in lockstep. `per-goal-layout-spec.md` records the rule as an amendment.
