# feat/per-goal-layout

**Status**: active
**Created**: 2026-10-10
**Subgoal**: revision 06-subagent-refactor-R1 — per-goal layout

## Tasks

- [ ] Write the per-goal layout's write-side spec, beside this plan
  - [ ] When `/new-branch` writes per-goal inside `docs/plan/<label>/`, and when it stays
        flat and legacy: a `revisions` root index, a legacy master plan, none, several
        open revisions, a standalone branch
  - [ ] Goal-file form and stubs: `TODO/0n-<slug>.md`, the `**Goal**:` line, and the slug
        and numbering rules `locate-plan.sh` already checks
  - [ ] Steps 2–6 of `/step` and `/hitl-step` on a per-goal plan, from the fields
        `locate-plan.sh` reports; the goal file is edited before the index (D2)
- [ ] `scripts/check-plan-index.sh`: a read-only drift report
  - [ ] Index marker against `**Goal**:`, a missing or orphan goal file, numbering, each
        with a `fix:` line that says what the repository shows
  - [ ] It shares its rules with `locate-plan.sh` without the two drifting
  - [ ] A suite under `dev/`, with mutants, as `dev/locate-plan/` has
  - [ ] Decide which commands run it, and when
- [ ] `/new-branch` writes the per-goal layout: the index with `**Revision**:` and
      `**Layout**: per-goal`, one goal-file stub per Scope item, the backlink in
      `_TODO.md`. The legacy path is kept.
- [ ] `/step` and `/hitl-step` read and write goal files
  - [ ] Drop the "cannot yet edit goal files" stop in Step 1
  - [ ] Step 4 edits the goal file, then the index line; Step 5 re-reads the index;
        Step 6 checks completion across goal files
  - [ ] No new step depends on `Grep` or `Glob`
  - [ ] The lockstep `sed` diff stays empty, and the `locate-plan` suite stays green
- [ ] End-to-end through the real commands: `/new-branch` inside a revision, then
      `/hitl-step` and `/step` over goal files, then the same on a legacy plan. The user
      runs the headless sessions.
