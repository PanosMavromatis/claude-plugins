# feat/locate-plan-diagnostics

**Status**: active
**Created**: 2026-10-09
**Subgoal**: revision 06-subagent-refactor-R1 — sharper diagnostics from `scripts/locate-plan.sh`

## Tasks

- [x] Bring the goal-10 test suite, fixtures and answer key into the repository
  > **Note:** Inventory from the scratchpad. `probe-run.sh` builds `fx`, the 21-branch
  > fixture, and its agent cases are dead. `script-suite.py` builds `fx-diag` and runs the
  > 71 direct cases. `build-faults.py` builds the shims and fault copies. Grading is
  > `answer-key.py` and `trial-grade.py`/`trial-show.py`. The trial harness is
  > `resolver-run.sh`, `resolver-show.py`, `build-resolver.py` and `plan-resolver.md`.
  > Results are `trial.json` (246 sessions, 1.4 MB) and `out-r-*` (about 4 MB of
  > transcripts). Every file hardcodes the scratchpad or `/Users/…` path. The 16
  > mutants in `mutants2/` are full copies of today's script, each one line different,
  > so they go stale at goal 2's first edit.
  > **Q:** Where should the suite live?
  > **A:** `dev/locate-plan/`, next to `dev/measure-context.sh`. The marketplace ships
  > `plugins/workflow-claude/` whole, so a suite placed there would reach every install.
  > **Q:** What gets tracked?
  > **A:** Builders, suite, answer key, grader, the wrapper harness, and a compact per-case
  > score table. Fixtures are rebuilt deterministically.
  > **Note:** corrected the same day. The options as offered left the wrappers' replies
  > out, which would have left the scores without their evidence. Worse, the per-session
  > fix grades had never been saved, only the arm totals; a side agent caught it. The user:
  > "If we have missing data, don't blame me, just re-generate it."
  > - All 120 graded sessions were re-graded by hand, from the stored replies, against
  >   `KEY` (`trial/hand-grades.tsv`, with a reason for each).
  > - A trimmed `trial-evidence.json` keeps one record per session (246), with the graded
  >   text. Paths are rewritten, and the script's output is stored once per case.
  > - Transcripts and the raw `trial.json` still stay out.
  > **Q:** How should the mutants be stored?
  > **A:** As patches applied fresh to the current script at run time. A patch that no
  > longer applies is reported as stale, not silently run against old code.
  - [x] Choose where it lives (`dev/` or inside the plugin) and what is tracked:
        generators, answer key and grader, or also built fixtures and results
    > **Done:** `dev/locate-plan/`, which has a README. No path is hardcoded: every tool
    > writes under `$LOCATE_PLAN_WORK`, and refuses a directory inside the repository.
  - [x] Name the fault wrappers neutrally: the `-trunc` path leaked a hint
    > **Done:** every arm and fault copy sits at `p/<8 hex>/workflow-claude`, and every
    > shim at `bin/<8 hex>/`. The hash is fixed, so builds reproduce, and `bash` and
    > Python derive the same names. The wrappers carry no comments, and the real script
    > is outside the plugin root (`core.sh`).
    > **Note:** the evidence confirms the leak: a baseline f03 reply said "this is the
    > `-trunc` baseline script". Some hints remain, from fixture names the cases depend on:
    > `d/eNN` branch names and the `nogit` directory. The README lists them.
  - [x] Run the suite from the repo against today's script and get today's pass count.
        Re-grading the stored baseline runs gives the goal-10 scores unchanged.
    > **Result:** each check run against the scratchpad originals:
    > - **fixtures:** all 59 branch trees are hash-identical (21 in `fx`, 38 in
    >   `fx-diag`);
    > - **suite:** 71/71, output byte-identical to the old suite's, about 20 s;
    > - **mutants:** 15 of 16 killed, each by its own case, and n05 equivalent, about
    >   90 s;
    > - **answer key:** 10/10 mechanical fixes clear their cases;
    > - **grader:** `grade.py` `table` and `stats` byte-identical to the old grader's on the
    >   stored `trial.json`;
    > - **arms:** the three base arms are identical to the copies the trial ran. The fault
    >   copies differ only in the wrapper's new form, plus goal 12's later Step 1 change in
    >   two of them.
    >
    > The fix scores were graded by hand, so they can only be re-graded, not reproduced.
    > The per-case bar reproduces exactly:
    > - best wrapper: 33, or 36 with f03 fixed;
    > - today's script: 2 on 7 cases and 1 on 8, which is 28 of 40 now that goal 12
    >   handles f03 (provisional until goal 4 reruns it under neutral names).
    >
    > Three arm-run totals land one point from the recorded ones: baseline t2 25 against
    > 26 (f02), Haiku t1 31 against 30 (e14), and Haiku t2 25 against 26 (e02). Each is a
    > borderline call, explained in `hand-grades.tsv`, and none moves the bar.
- [ ] Sharpen the `fix:` lines in `scripts/locate-plan.sh`, so that every case in the
      goal-10 answer key scores 2. Each item names its cases; today's script scores 1 on
      all twelve listed here.
  > **Note:** the first draft listed five items and covered only seven of the twelve
  > cases. A side agent checked it against the re-grade and found e05, e06, e11, e14
  > and f02 missing. The user added them: "Now is the time to do a thorough job, before
  > we hit production."
  - [ ] Create, not restore, a file that was never committed (e07b, both revisions)
  - [ ] `git mv` a plan written under the other model (e07: `_DO.md` beside a missing
        `_TODO.md`)
  - [ ] Name the exact goal file: `TODO/02-two.md` from the index line's title (e10)
  - [ ] An unnumbered goal line: give it the next free number (`02`) and name the goal
        file to create, `TODO/02-<slug>.md` (e09)
  - [ ] Say that the directory holds no plan at all, naming what it does hold (e02b)
  - [ ] Remove a `**Layout**` header that no file justifies: no `TODO/` directory and
        unnumbered items (e08); `per-goal` on the root plan (e08b)
  - [ ] Name the exact header line to remove, or the section to add, for a revisions
        index without `## Revisions` (e05)
  - [ ] Give each malformed revision line corrected (line 8's missing space). Leave a
        line's unknown marker to the user, listing the five. Warn that a revision made
        valid as `[~]` then needs its `_TODO.md` (e06)
  - [ ] Name both duplicate goal files, and say that which is stale is the user's call
        (e11)
  - [ ] When no revision is open and no plan file exists, say so, and offer to open a
        revision or create a plan. Never suggest reopening a closed revision that has no
        directory (e14)
  - [ ] When a tool fails (exit 3), add a hint to the stderr message: for `awk` or
        `git` not found (127), check `PATH` and say which binary was found first (f02)
  - [ ] The suite and mutants still pass, with new cases asserting each sharper line, and
        the spec is updated to match
- [ ] `/step` and `/hitl-step` offer a read-only investigation in the main session on an
      `error` or a failed run, and run it only when the user asks. The lockstep `sed`
      diff stays empty.
- [ ] Re-grade against the goal-10 answer key: 40/40. On every case, at least the best
      wrapper run; the full fix on e07, e08, e08b and e09; no case lower than today. The
      user runs the headless sessions. f03 is scored through the real `/hitl-step` and
      `/step`, whose Step 1 refuses a cut-short report (goal 12), and not through a probe
      that paraphrases Step 1.
