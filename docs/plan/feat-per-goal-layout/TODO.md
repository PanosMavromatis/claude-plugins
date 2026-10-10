# feat/per-goal-layout

**Status**: merged — PR #7 — 2026-10-10
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
- [x] `scripts/propose-branch-plan.sh` and `/new-branch`: per-goal inside the open
      revision, the legacy path kept
  > **Note:** `/new-branch` has no `Edit` in `allowed-tools`. So its backlink, a one-line
  > insert, is a whole-file `Write` of the master plan: the access pattern the plugin's
  > `CLAUDE.md` records `/step` once had, on the one file that grows without bound.
  > **Q:** When should `/new-branch` run the script: before or after `git checkout -b`?
  > **A:** Before the branch: once the name is agreed, after step 2 and before step 4.
  > A collision, a broken index or an `ask` then happens while nothing exists yet. The
  > script never reads the current branch, so either order would work.
  > **Q:** Approve the rest? `SUBGOALS_AWK` goes in the library, since `/smart-merge`
  > step 7 needs the same block and backlink lookup. The report gives the legacy
  > `## Subgoals — revision <label>` heading. Branch names are validated. `/new-branch`
  > gains `Edit`. The suite goes in `dev/propose-branch-plan/`.
  > **A:** Approve as proposed.
  > **Done:** `scripts/propose-branch-plan.sh` and `SUBGOALS_AWK` in the library, with
  > the spec updated. `/new-branch` was rewritten into nine steps around them.
  - [x] The script, to the spec's report and rules, with a suite and mutants
    > **Note:** smoke-tested read-only on this repository's real master plan. `ask`
    > listed the five open subgoals and left out subgoal 3, which has its branch.
    > `--subgoal` read the revision from the `##` heading and put the backlink after
    > line 69, the end of subgoal 4's block. Reusing `feat/plan-locator` was refused,
    > with that plan named.
    > **Note:** the suite found the script dying with no report and no stderr on every
    > standalone proposal. The cause was `R_MSG="…$( [ -n "$R_BACK" ] && printf … )"`:
    > an assignment takes its last substitution's status, so `set -e` ended the script
    > whenever there was no backlink. It is now a plain `if`. A scan of every plan
    > script finds no other such substitution outside a here-document.
    > **Note:** `dev/propose-branch-plan/` has 32 cases, one orphan branch each, and
    > passes under both shells. p24 writes what a proposal lists, then checks that
    > `locate-plan.sh` resolves it at rung 2 with the right goal file, that
    > `check-plan-index.sh` finds it clean, that a second proposal is refused, and that
    > the subgoal is no longer a candidate. 18 mutants, all killed by the rule each
    > breaks. Adding `SUBGOALS_AWK` shifted the library, so a scratchpad tool rebased
    > every mutant (fuzz 0, offset only) and rewrote the 3 that moved. All three
    > suites, both mutant sets, the validation set and the answer key then pass.
  - [x] `/new-branch` runs it, asks on `ask`, and writes exactly the paths it lists: the
        index, one goal-file stub per Scope title, the backlink
    > **Note:** the command text is written, not yet run. Step 4 proposes before
    > `git checkout -b`. Step 7 writes only `index:`, the `goals:` paths and the
    > backlink, the backlink by an anchored `Edit` (now allow-listed). The legacy
    > templates are unchanged. Running it through the real command is goal 6's
    > end-to-end check, with the user running the sessions.
  - [x] Picking the subgoal replaces the hand lookup on a legacy master plan too
    > **Note:** cases p02–p05 and the smoke test on this repository's master plan show
    > it. `/new-branch` no longer greps for the item: the script lists the candidates,
    > and the user picks one.
- [x] `/step` and `/hitl-step` read and write goal files
  > **Q:** The drafts change `/hitl-step` in 34 lines and `/step` in 23, legacy paths
  > untouched: Step 1's warning repair, the per-goal reads in Step 2, goal file before
  > index in Steps 3–4, a script re-run in Step 5, `check-plan-index.sh` in Step 6.
  > A split goal's slug is applied by hand, and Step 6 confirms it. Write them?
  > **A:** Yes.
  - [x] Drop the "cannot yet edit goal files" stop in Step 1, and offer to repair W11 on
        the selected goal
    > **Note:** a goal named out of order is found in the index, which is small, by `Read`
    > rather than `Grep`.
  - [x] Steps 2–4 work on the goal file, goal file before index; Step 5 re-runs
        `locate-plan.sh`; Step 6 runs `check-plan-index.sh`
    > **Note:** `check-plan-index.sh` is now allow-listed in both commands. Step 2 spells
    > out the one-level outdent, so the model does not carry legacy indents into a goal
    > file.
  - [x] `/step`'s DO-model unit is one task in the goal file
  - [x] No new step depends on `Grep` or `Glob`
    > **Note:** scanned: the only `Grep` on changed lines is legacy text, the frontmatter
    > and Step 5's legacy sentence, which gained a per-goal clause. Removing the legacy
    > dependency is the next subgoal's.
  - [x] The lockstep `sed` diff stays empty, and the `locate-plan` suite stays green
    > **Note:** lockstep is empty in the drafts, in the repository, and in all 12 trial
    > arms, which `build-arms.py` still splices. No script changed in this goal, and
    > the locate-plan suite passes all 83 cases under both shells.
- [x] End-to-end through the real commands: `/new-branch` inside a revision, then
      `/hitl-step` and `/step` over goal files, then the same on a legacy plan. The user
      runs the headless sessions.
  > **Q:** Every write in these commands waits for confirmation, which a headless session
  > cannot give. How should the end-to-end sessions run?
  > **A:** Scripted headless: one `claude -p` per command, from a script the user starts.
  > The decisions come with the prompt, the writes are approved in advance, and a
  > checker grades the result and each session's permission denials. The confirmation
  > pauses themselves are not exercised; this goal does not change them.
  > **Note:** the harness is `dev/per-goal-e2e/` (`build.py`, `run.sh`, `check.py`). Each
  > fixture is a consumer repository whose `CLAUDE.md` gives the approvals in advance,
  > so the commands run unmodified, and only the `--plugin-dir` copy is loaded:
  > `workflow-claude@mavromatis-ai-labs` is enabled in this repository's project
  > settings, not the user's. `check.py` grades each fixture's end state and each
  > session's tool calls (stream-json), which is how ordering claims become checkable:
  > proposed before `git checkout -b`, goal file before index, master plan edited not
  > rewritten, every script from the copy.
  > **Result:** run `r1`, 7 sessions, $2.74. e1 (`/new-branch` in a revision, then
  > `/hitl-step 2`), e3 (DO model, `/step 2`) and e5 (the interrupted-edit repair) pass
  > every check:
  > - the index and goal files are written to the proposal, with a one-line backlink
  >   after the subgoal's block;
  > - every goal file was edited before its index line;
  > - `locate-plan.sh` re-ran between goals, and `check-plan-index.sh` came back clean
  >   with nothing open;
  > - e5 named the mismatch and rewrote the index line from the goal file.
  >
  > The per-goal sessions made no `Grep`, `Glob` or shell-search calls at all.
  > **Note:** two of r1's three failures were the checker's. `/new-branch` writes
  > `docs/git/<branch-name>.md` with the name unflattened (`docs/git/feat/plan-dirs.md`),
  > and `/smart-merge` reads the same path. This repository's own branch docs are
  > flattened, written by hand, so the two disagree. The checker now follows the
  > command.
  > **Note:** the third was real, and older than this branch. `/hitl-step`'s legacy Step 6
  > awk printed `s" | "$0`, and Claude Code's safety check reads a `|` inside an awk
  > string as a pipe to a command, so it refused the check outright. The separator is
  > now ` — `, and the command says why. Run `r2` re-ran e4: the safety refusal is
  > gone, but awk is not in `/hitl-step`'s `allowed-tools`, so the check now needs
  > approval and the model fell back to shell `grep`. Everything else in e4 passes:
  > the flat plan, the one-line backlink, the goal ticked.
  > **Q:** The awk check prompts (interactive) or is refused (headless). Fix it now, in
  > the next subgoal, or allow-list awk?
  > **A:** In the next subgoal, broadened from `Grep` and `Glob` to every step that relies
  > on a tool its command does not allow, this awk included, measured before rewriting.
  > The likely fix there is `check-plan-index.sh` reporting a legacy plan's open items,
  > so Step 6 uses one script for both layouts. `Bash(awk:*)` was rejected: awk can run
  > commands and write files.
  > **Done:** the per-goal layout runs end to end through the real commands, and the
  > legacy path behaves as in 0.9.0, apart from the Step 6 safety fix. The remaining awk
  > prompt is recorded in the master plan's next subgoal.
