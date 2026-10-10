# feat/per-goal-layout

**Status**: active
**Created**: 2026-10-10
**Subgoal**: revision 06-subagent-refactor-R1 — per-goal layout

## Tasks

- [x] Write the per-goal layout's write-side spec, beside this plan
  > **Q:** When should `/new-branch` write the per-goal layout instead of today's
  > single-file plan?
  > **A:** Follow the root. Per-goal only when `docs/plan/TODO.md` (or `DO.md`) is a
  > `**Layout**: revisions` index: inside `docs/plan/<label>/` for a subgoal of the open
  > revision, flat under `docs/plan/` for a standalone branch. A legacy master plan, or
  > none, keeps today's flat single file. One switch per project: upgrading to 0.10.0
  > changes nothing until the project adopts the index.
  > **Q:** Who decides where a new branch plan goes and what its goal files are named?
  > **A:** A new read-only proposing script. Given the branch and the Scope titles, it
  > prints a fixed report: the layout, the revision, the target directory, each file to
  > write with its slug-derived name, the `_TODO.md` backlink line, and `problem:`/`fix:`
  > on a collision or a broken index. `/new-branch` shows it, confirms, and writes exactly
  > what it lists. The slug and numbering rules move into one sourced file shared with
  > `locate-plan.sh` and `check-plan-index.sh`, so the three cannot drift, and the
  > `locate-plan` suite re-runs. Rejected: `locate-plan.sh` plus prose, which keys on
  > E14's wording and leaves the model applying rules by hand; a second report shape
  > inside `locate-plan.sh`.
  > **Q:** The draft spec also proposes five things neither answer settled. First,
  > `propose-branch-plan.sh` lists the open subgoals that have no branch yet, and
  > `/new-branch` asks which one; this applies to legacy master plans too. Second, a
  > `<flat>` directory already under `docs/plan/` is an error. Third, the shared rules
  > go in `scripts/lib/plan-rules.sh`. Fourth, Step 5 re-runs `locate-plan.sh` and
  > Step 6 runs `check-plan-index.sh`. Fifth, in the DO model the unit is one task in
  > the goal file. It also restructures the branch plan into six goals. Approve?
  > **A:** Go ahead.
  > **Done:** `per-goal-layout-spec.md`, beside this plan. It covers which layout a new
  > plan gets, what is written (index, goal files, backlink), `propose-branch-plan.sh`'s
  > report and rules, the shared rules file, Steps 1–6 on a per-goal plan, and
  > `check-plan-index.sh`'s scope.
  - [x] When `/new-branch` writes per-goal inside `docs/plan/<label>/`, and when it stays
        flat and legacy: a `revisions` root index, a legacy master plan, none, several
        open revisions, a standalone branch
  - [x] Goal-file form and stubs: `TODO/0n-<slug>.md`, the `**Goal**:` line, and the slug
        and numbering rules `locate-plan.sh` already checks
  - [x] Steps 2–6 of `/step` and `/hitl-step` on a per-goal plan, from the fields
        `locate-plan.sh` reports; the goal file is edited before the index (D2)
- [x] Move the rules more than one script applies into `scripts/lib/plan-rules.sh`,
      sourced by `locate-plan.sh`
  > **Q:** The plan: move the code verbatim, with `die`'s prefix as `$PROG`; teach
  > `suite.py` a script-plus-library tree; re-anchor the 26 mutants mechanically; add a
  > slug-cap mutant; copy the library beside `core.sh` in `build-arms.py`. Go ahead?
  > **A:** Go ahead.
  > **Done:** `locate-plan.sh` is 487 lines and `lib/plan-rules.sh` 419. A scratchpad
  > splitter moved exact line ranges and checked that every original line landed once.
  > The script sources the library behind a guard: a lone copy exits 3 with
  > `cannot read …/lib/plan-rules.sh`.
  - [x] `slug()`, `title()`, `num()`, the revision-line and `**Layout**:` checks, the
        goal-file reading and the status read, each defined once
    > **Note:** the library also holds what those rules call: `die`, `warn`,
    > `violation`, `emit`, `need_file`, `scan_dirs`, `list_named`, `count_items`,
    > `history_of` and `SELECT_AWK`. The script keeps only the report shape, the
    > arguments and the rungs. The library's header names the caller's side of the
    > interface: `PROG`, `MODEL`, `OTHER`, `ROOT_PLAN`, the report accumulators and
    > `fail <rung>`.
  - [x] The `locate-plan` suite passes unchanged, and the mutants cover the shared file
    > **Note:** the baseline before the move was 82/82, with 25 mutants killed and n05
    > equivalent. After the move, the suite passes under both shells, the validation
    > set passes, and so does the answer key on both sets. The static checks now scan
    > both files. A scratchpad tool re-anchored every mutant: it applied each one to
    > the old script, placed its region uniquely in the new tree, and regenerated it
    > against that file, so 12 now target the library. All 27 apply with no offset and
    > no fuzz.
    > **Note:** the new `q11-slug-cap` (cap 40 → 30) **survived** at first: no case had a
    > title long enough for the cap to matter, so the rule three scripts are about to
    > share was untested. The new `e10c` gives a 64-character title whose cut at 40
    > ends on a `-` that must be trimmed, and kills it. The final count is 27 mutants:
    > 26 killed, n05 equivalent, 0 stale.
  - [x] `dev/locate-plan/trial/build-arms.py`'s fault copies carry the shared file
    > **Note:** every arm and fault copy was built in a separate scratch directory, and
    > each wrapper ran on `fx` `case/r2-flat`. f03 cuts the report to 5 lines with no
    > `message:`, f04 lands on the legacy root at rung 3, and f05 swaps the path. None
    > exits 3, and lockstep is empty in every arm. No headless sessions were run,
    > since the goal changes no behaviour.
- [ ] `scripts/check-plan-index.sh`: a read-only drift report, on the shared rules
  - [ ] Index marker against `**Goal**:`, a missing, duplicate or orphan goal file,
        numbering, open items; each finding with a `fix:` line read from the evidence
  - [ ] A suite under `dev/`, with mutants, as `dev/locate-plan/` has
  - [ ] Its callers: Step 6 of both step commands now; `/smart-merge` step 2 later
- [ ] `scripts/propose-branch-plan.sh` and `/new-branch`: per-goal inside the open
      revision, the legacy path kept
  - [ ] The script, to the spec's report and rules, with a suite and mutants
  - [ ] `/new-branch` runs it, asks on `ask`, and writes exactly the paths it lists: the
        index, one goal-file stub per Scope title, the backlink
  - [ ] Picking the subgoal replaces the hand lookup on a legacy master plan too
- [ ] `/step` and `/hitl-step` read and write goal files
  - [ ] Drop the "cannot yet edit goal files" stop in Step 1, and offer to repair W11 on
        the selected goal
  - [ ] Steps 2–4 work on the goal file, goal file before index; Step 5 re-runs
        `locate-plan.sh`; Step 6 runs `check-plan-index.sh`
  - [ ] `/step`'s DO-model unit is one task in the goal file
  - [ ] No new step depends on `Grep` or `Glob`
  - [ ] The lockstep `sed` diff stays empty, and the `locate-plan` suite stays green
- [ ] End-to-end through the real commands: `/new-branch` inside a revision, then
      `/hitl-step` and `/step` over goal files, then the same on a legacy plan. The user
      runs the headless sessions.
