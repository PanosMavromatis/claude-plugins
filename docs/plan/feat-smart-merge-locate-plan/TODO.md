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
- [ ] Step 2 resolves the branch plan through `locate-plan.sh`
- [ ] Write `scripts/propose-merge-record.sh`, with the master-file selection moved into
      `lib/plan-rules.sh`
- [ ] Step 7 stamps the resolved index and edits the backlinked item in the right master file
  - [ ] Zero or several backlinks are reported, never guessed
- [ ] The four `dev/` suites and their mutant passes pass, `propose-merge-record`'s new
- [ ] Verify end to end: the user runs it, `check.py` grades
