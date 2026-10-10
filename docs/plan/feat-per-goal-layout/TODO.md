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
- [x] `scripts/check-plan-index.sh`: a read-only drift report, on the shared rules
  > **Q:** What does `check-plan-index.sh` take as input?
  > **A:** The index, required. Every caller already holds a resolved plan: Step 6 has
  > Step 1's `plan:`, and `/smart-merge` step 2 has its resolved path. Resolving again
  > would make a second resolver to keep in step with `locate-plan.sh`. This narrows the
  > spec's "or nothing, resolving as `locate-plan.sh` does", and the spec is updated to
  > match.
  > **Q:** Is the rest of the design right? The report is `result: clean | drift |
  > error`, `plan`, `goals`, `open`, `warnings`, `problem`, `fix` and `message`. The
  > exit codes are 0 clean, 1 drift or error, 2 usage, 3 tool failure. The findings are:
  > D1 marker mismatch; D2, D3 and D5 as E10, E11 and E9 over every goal; D4 orphan goal
  > file; D6 duplicate number; D7 no `**Goal**:` line; D8 `[x]` with open items. The
  > suite goes in `dev/check-plan-index/`, beside `dev/locate-plan/` rather than renaming
  > it, since records point at that name.
  > **A:** Approve as proposed.
  > **Done:** `scripts/check-plan-index.sh`, read-only, on the shared library. Its
  > contract is the spec's `check-plan-index.sh` section: report keys, exit codes,
  > D1–D8 with their fixes, and which overlaps go to whom. It was smoke-tested on one
  > plan holding every fault at once, then by its suite.
  - [x] Index marker against `**Goal**:`, a missing, duplicate or orphan goal file,
        numbering, open items; each finding with a `fix:` line read from the evidence
    > **Note:** the library gained two additive fields for it. `SELECT_AWK` prints an
    > `IDX` record (line, marker, number, text) for each numbered index line, and
    > `GOALFILE_AWK`'s `SUB` record gains the marker and the line after the line number.
    > `locate-plan.sh` reads only the first field of `SUB` and has no case for `IDX`, so
    > its output is unchanged, as its suite confirms.
    > **Note:** vetting the first smoke run found four defects of mine, each of which
    > would have misled a caller:
    > - D8 listed its open items on continuation lines, so `problem:` had more lines
    >   than `fix:`, and every later fix sat beside the wrong problem. Findings are now
    >   one line each, naming line numbers. Paths can carry commas, line numbers cannot.
    > - A duplicated number was checked against its file twice, giving a double D7 and
    >   double open items. Only the first line with a number is checked now.
    > - D6's free numbers ignored goal files and E9's assignments, so the two
    >   suggestions could collide (E9 said 10, D6 said 06). D6 now starts past both.
    > - D4 also offered a new index line for a file E9 was already numbering a line
    >   to match: two conflicting fixes for one fact. D4 now leaves E9's files alone.
    >
    > The suite then found three more: the problem line echoed an absolute path; D6
    > named a number by its last spelling (`2`) rather than its first (`02`); and an
    > awk `NR > 1` tripped the static check's redirect rule. That third one was rewritten
    > as `NR == 1 ? … : …` rather than loosening the check.
  - [x] A suite under `dev/`, with mutants, as `dev/locate-plan/` has
    > **Note:** `dev/check-plan-index/` has 33 cases on one fixture repository, one plan
    > directory per case, and passes under both shells. Each report is graded for key
    > order, exit code, text, one fix per problem, the exact `open:` list, no absolute
    > paths, an untouched fixture and determinism. 18 mutants, all killed, each checked
    > to die for the rule it breaks. The first `c03` died of a crash it caused (an empty
    > loop record), not of missing orphan logic, so it was rewritten. It now fails k07,
    > k08 and k27.
    > **Note:** the library change made `locate-plan`'s `m02-no-fences` stale, since it
    > disables fences in `GOALFILE_AWK`, whose `SUB` line changed. It was rebuilt with
    > all six hunks, and an assertion shows no fence handling survives. Afterwards the
    > locate-plan suite, validation set and answer key all pass, with 26 mutants killed
    > and n05 equivalent.
  - [x] Its callers: Step 6 of both step commands now; `/smart-merge` step 2 later
    > **Note:** decided and recorded in the spec. The wiring itself is goal 5's Step 6
    > subgoal and the merge subgoal's step 2; nothing calls the script yet.
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
