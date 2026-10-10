# feat/smart-merge-locate-plan

**Status**: active
**Created**: 2026-10-10
**Subgoal**: revision 06-subagent-refactor-R1 — `/smart-merge` step 7 through `locate-plan.sh`

## Tasks

- [x] Measure what `/smart-merge` steps 2 and 7 need in each layout
  > **Done:** Step 2 needs only the existing scripts plus a model-choice rule; step 7 gets
  > a new proposal script, option A.
  - [x] What `locate-plan.sh`, `check-plan-index.sh` and `SUBGOALS_AWK` already report
    > **Note:** Step 2 is covered. On the per-goal e2e fixture `r1`, `locate-plan.sh TODO.md
    > --` reports rung 2, `kind: branch`, `layout: per-goal`, and `plan:` is the index, which
    > is what step 7 stamps (its `**Status**:` is line 3). `check-plan-index.sh` reports
    > `open:` for both layouts, goal files included, so step 2's unfinished-items warning
    > needs nothing new. A per-goal plan's Q&A lives in its goal files, so step 2 reads those
    > too. With the wrong model `locate-plan.sh` refuses with E2, whose fix text ("run
    > /hitl-step instead") is written for the step commands: `/smart-merge` needs its own
    > rule for choosing the model.
    > **Note:** Nothing reports the backlink today, and PR #8's `grep -n -F` workaround has a
    > false positive: `'> **Branch:** feat/locate-plan'` matches line 53 of the master plan,
    > `feat/locate-plan-diagnostics`. `SUBGOALS_AWK` matches whole branch values, reads only
    > an item's indented block (so prose never matches), and reports the block's last line,
    > which is where `> **Done:**` goes; Q&A lines can follow the backlink, so that is not
    > always the `Branch:` line. On this repo it gives `ITEM 87 ~ 90 [feat/smart-merge-locate-plan]`.
  - [x] Where the backlinked item lives: root `TODO.md`, or a revision's `_TODO.md`
    > **Note:** `propose-branch-plan.sh` lines 143–170 already choose the master files: the
    > root plan when it is legacy, or every open revision's `_TODO.md` (`index_open`) under
    > a revisions index. On `r1` that is `docs/plan/07-rev/_TODO.md`, backlink on line 11
    > under item 9.
  - [x] Whether locating the backlink needs a new script mode
    > **Q:** How should step 7 locate the backlink: (A) a new read-only
    > `scripts/propose-merge-record.sh <model> <branch> --`, with the master-file selection
    > moved into `lib/plan-rules.sh`; (B) a `--merged` mode on `propose-branch-plan.sh`; or
    > (C) shell `grep` with an exact-line match?
    > **A:** A. It reports the master file, the item's `file:line`, marker, text and block
    > end; `result:` is `found`, `none` (standalone, or a lost backlink) or `error`
    > (duplicates, with their lines). A fourth suite with mutants joins goal 4.
- [x] Step 2 resolves the branch plan through `locate-plan.sh`
  > **Note:** `locate-plan.sh` falls through: on a branch with no plan it returns the master
  > plan (rung 3) or another branch's active plan (rung 4) rather than a miss. Only a rung-2
  > result, or rung 1 after a rung-2 `ask`, is this branch's plan; anything else means it has
  > none, or step 7 would stamp the wrong file `merged`.
  > **Q:** Which model does `/smart-merge` pass: (A) `TODO.md` if `docs/plan/TODO.md` exists,
  > else `DO.md`, re-running once with the other model on E2; (B) always `TODO.md` then
  > `DO.md`; or (C) a model-agnostic mode in `locate-plan.sh`?
  > **A:** A. E2's `fix:` names a step command, so `/smart-merge` ignores it and re-runs.
  > **Done:** Step 2 runs `locate-plan.sh`, accepting only a rung-2 (or rung-1-after-ask)
  > result as the branch plan, reads a per-goal plan's goal files, and takes the unfinished
  > items from `check-plan-index.sh`.
- [x] Write `scripts/propose-merge-record.sh`, with the master-file selection moved into
      `lib/plan-rules.sh`
  > **Q:** The report contract: `propose-merge-record.sh <model> <branch> [--item f:l] --
  > [plan]`, eleven keys (`result layout masters stamp item after subgoal candidates
  > warnings problem fix message`), `result:` one of `propose`, `ask` (duplicate
  > backlinks), `none` (no plan, no backlink) or `error`. A missing backlink is a warning
  > unless the plan says `standalone`. And a plan with no `**Status**:` line: (A) `error`,
  > fix "add `**Status**: active` under the title"; (B) a warning and `stamp: —`; or (C)
  > propose inserting one?
  > **A:** The contract as proposed, and A: a plan with no stamp counts as active forever,
  > which is the silent failure the stamp exists to prevent.
  > **Note:** Smoke-checked in 14 throwaway repositories plus this one, and under
  > `/bin/bash` 3.2. Review caught two bugs before any run (the message's "and close" join,
  > and the candidates' text cut at an item's last tab), and the run caught a third: with
  > no master file to search, the script claimed the backlink was "lost or misspelled";
  > it now gives only the real reason. `feat/locate-plan` gets `result: none`, where the
  > `grep -F` workaround found `feat/locate-plan-diagnostics`'s item.
  > **Note:** Mutants `b02` and `b18` of `propose-branch-plan` patched the moved lines, so
  > they were regenerated against `master_files` and the new `none)` branch, with the same
  > change. `b02` now lives in the library. All three suites then passed with 0 failing;
  > every mutant was killed but `locate-plan`'s known-equivalent `n05`.
  > **Done:** `propose-merge-record.sh` reports the stamp line, the backlinked item and the
  > line its Done goes after, or `ask`/`none`/`error`; `master_files` and `master_items`
  > in the library serve it and `propose-branch-plan.sh`.
- [x] Step 7 stamps the resolved index and edits the backlinked item in the right master file
  > **Done:** Step 7 runs `propose-merge-record.sh`, stamps the `stamp:` line, closes the
  > `item:` block with the Done line after `after:`, and stages exactly those files; `Glob`
  > and `Grep` are gone from `/smart-merge`.
  - [x] Zero or several backlinks are reported, never guessed
    > **Note:** The script decides each case (`ask` with candidates, `none`, or a warning
    > naming the lost subgoal) and step 7 says what to show for each; the e2e run in goal 6
    > checks a real merge against it.
- [ ] The four `dev/` suites and their mutant passes pass, `propose-merge-record`'s new
- [ ] Verify end to end: the user runs it, `check.py` grades
