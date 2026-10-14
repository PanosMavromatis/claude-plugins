# feat/master-plan-checks

**Created**: 2026-10-14
**Base**: main at 0af57ca
**Status**: active

## Purpose

R2 subgoal 4. `/master-plan` checks a draft against `subdividing.md`'s form by reading it in the session, and has no way to see whether each subgoal carries something the spec said. Runs r8 and r8b also showed its session reaching outside its grants: a `git -C … checkout -b`, since fixed by `fix/command-phrasing`, and a `grep` at an invented `skills/master-plan/references/` path. This branch moves the form check into a read-only script that shares the library's item-block rule, has `plan-drafter` return a trace tagging each subgoal with the spec item it carries, and has the command judge fidelity from that trace.

## Scope

- `agents/plan-drafter.md` and `references/subdividing.md`: the trace, beside the draft, never in `_TODO.md`
- a new read-only form-check script, `scripts/check-draft.sh`, using `lib/plan-rules.sh`'s item-block rule: it checks the drafter's reply, resolving each trace tag against the spec, and with `--plan` the plan file as written; its suite is under `dev/check-draft/`
- `commands/master-plan.md`: step 3 runs the script on the reply and judges fidelity from the trace; the written plan is checked with `--plan`, and again after the commit is approved, so edits made outside the session are caught
- `dev/per-goal-e2e/check.py` for the m scenarios, and an m1–m3 run

## Context

- R2 subgoal 4: `docs/plan/08-subagent-refactor-R2/_TODO.md:51`; R2's review chose a trace in the drafter's output only, in the spec's own terms, with a form-check script
- The design's R2 step 0 note, in `tmp/subagent-refactor-plan.md`
- The library reads subgoal blocks with `SUBGOALS_AWK` (`plan-rules.sh`); `check.py` already has a Python `draft_form` and a spec-unit tripwire (`SPEC_UNITS`), the grader's own checks
- Open for goal 03: the draft is text in the session until step 5 writes it, so step 3's check needs it in a file first; where is goal 03's decision
- The e2e run is paid; the user runs it

## Notes

- 2026-10-14, goal 02: the script also reads the written plan (`--plan`), since the review's edits, a hand edit or a formatter's save would otherwise reach the commit unchecked; tags are checked only in the reply, where the trace matches the draft as returned
- 2026-10-14, goal 02: checking an open revision's plan after later edits is deferred to a new R2 subgoal 13, so the release moves to 14
