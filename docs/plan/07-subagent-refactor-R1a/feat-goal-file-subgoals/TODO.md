# feat/goal-file-subgoals

**Status**: active
**Created**: 2026-10-12
**Revision**: 07-subagent-refactor-R1a
**Subgoal**: 5. `/new-branch` writes each per-goal goal file with its subgoals, never a stub: `propose-branch-plan.sh` reports the master-plan subgoal's `Scope: … Acceptance: …` lines, the command drafts each goal's subgoals from them and the scope discussion, and `locate-plan.sh` warns when the selected goal file has no subgoals.
**Layout**: per-goal

## Goals

- [ ] 01 — Report the subgoal's scope from propose-branch-plan.sh
- [ ] 02 — Warn on a goal file with no subgoals
- [ ] 03 — Draft each goal's subgoals in /new-branch
- [ ] 04 — Propose subgoals in /step and /hitl-step
- [ ] 05 — Check a real /new-branch run's goal files
