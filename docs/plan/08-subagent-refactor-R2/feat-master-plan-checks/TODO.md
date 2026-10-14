# feat/master-plan-checks

**Status**: active
**Created**: 2026-10-14
**Revision**: 08-subagent-refactor-R2
**Subgoal**: 4. `/master-plan` checks a draft's fidelity and form within its grants: `plan-drafter` returns, beside the draft, a trace tagging each subgoal with the spec item it carries, and a read-only script checks the draft's form.
**Layout**: per-goal

## Goals

- [x] 01 — plan-drafter returns a trace beside the draft
- [x] 02 — A read-only script checks a draft's form
- [x] 03 — /master-plan runs the form check and judges fidelity from the trace
- [x] 04 — The e2e grader checks the trace, and an m1-m3 run is clean
