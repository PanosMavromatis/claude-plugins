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
- [x] Write a held-out validation set before any fix is written
  > **Note:** a side agent pointed out that goal 2 writes each sharper line from the
  > answer key's own cases, and the same author grades them. 40/40 could then mean "fits
  > these 20 repositories" rather than "works". Grading by another agent was set aside as
  > too involved for now. The user: "let's add a few broken repos the fixes weren't
  > designed for — or even measure entirely on new broken repos, like a validation set".
  > The training cases stay as well: only they have wrapper scores to compare against.
  > The set is held out, not blind, because the same author writes and grades it. Three
  > rules narrow that gap. It is committed before goal 2's first change to the script. It
  > is not run against the script until goal 4. If a case fails there and is then fixed,
  > both results are recorded and the set is marked spent.
  > **Q:** How should the validation set count toward acceptance?
  > **A:** As a gate on wrong advice: every validation case must score 1 or 2, so no 0
  > and no −1. How many reach 2 is recorded but not required, because requiring 2 on
  > held-out cases invites tuning to them after the first look.
  > **Q:** What should it contain?
  > **A:** For each of goal 2's twelve items, a variant of the same problem in a
  > different form: other names, depth, rung or goal numbers. Where a rule could fire
  > without its evidence, add a counter-case that needs a different fix. About 15–20
  > cases.
  - [x] A variant for each of goal 2's twelve items
  - [x] Counter-cases for every rule that reads evidence, for example:
        - a `_TODO.md` that was committed and then deleted: restore it, not create it;
        - a misspelt `**Layout**` on a plan that really is per-goal (numbered items and
          a `TODO/` directory): correct it, not remove it
    > **Done:** 22 cases, v01–v22, in their own fixture, `fx-val`; the user approved the
    > list as proposed.
    > - **Variants (13):** v01, v03, v05, v07, v10, v11, v13, v15, v17, v18, v19, v21,
    >   v22.
    > - **Counter-cases (9):** v02 and v04 (deleted in history: restore, not create or
    >   `git mv`), v06 (a near-miss file name: rename), v08 (an existing unclaimed goal
    >   file: number to match), v09 (plans one level down: list them), v12 and v14 (a
    >   misspelt header on a real per-goal plan or revisions index: correct, not remove),
    >   v16 (`## Revision` singular: rename), v20 (an active plan exists: name it).
  - [x] An answer key in `KEY`'s form (full fix, weaker fix, over-reach). Each mechanical
        full fix is verified on a clone, and the cases live apart from the training cases
        in the suite
    > **Done:** `VKEY` in `answer-key.py`. Its third field names the answer that scores 0
    > or −1. 19 cases have a mechanical full fix, and all 19 clear their case on a clone
    > (`answer-key.py --validation`). v10, v21 and v22 have none, because their fixes are
    > a judgement or an environment change. Some full fixes are a different invocation
    > (v03, v09, v13, v19, v20), so `verify()` gained an optional model and arguments.
  - [x] Committed before goal 2 changes `locate-plan.sh`. Until goal 4, the suite skips
        the validation cases by default
    > **Done:** `suite.py --validation` runs the v-cases alone, and a training run never
    > includes them. The training suite is unchanged: 71/71, identical output. The commit
    > that carries this line is the one that registers the set. It changes nothing in
    > `plugins/`, and goal 2 starts after it.
    > **Note:** building the set exposed two defects in today's script, which goal 2 now
    > covers through new training cases:
    > - **v17:** `- [~] 10 delta — y` is read as revision `10`. `index_open` takes the
    >   first word after the marker as the label and never checks that ` — ` or the end
    >   of the line follows, so the script asks for `docs/plan/10/_TODO.md`. The spec says
    >   a label has no space, so this is E6.
    > - **v21:** with `git` missing (127), line 137 reports "not inside a git
    >   repository". Any failure of `git rev-parse` reads as E13, though only 128 means
    >   that. This is a failed command taken as an answer, which goal 11's
    >   fail-loudly rule forbids. It should exit 3.
    >
    > Both cases now expect the correct behaviour, so `--validation` fails on them today
    > (2 of 22). Their mechanical checks have been seen and are no longer held out; their
    > `fix:` text still is.
- [x] Sharpen the `fix:` lines in `scripts/locate-plan.sh`, so that every case in the
      goal-10 answer key scores 2. Each item names its cases; today's script scores 1 on
      all twelve listed here.
  > **Note:** the first draft listed five items and covered only seven of the twelve
  > cases. A side agent checked it against the re-grade and found e05, e06, e11, e14
  > and f02 missing. The user added them: "Now is the time to do a thorough job, before
  > we hit production."
  > **Q:** The design, item by item: each sharper line fires only on evidence the script
  > reads, and otherwise falls back to a generic line that is still correct. Implement it
  > this way?
  > **A:** Yes.
  > **Note:** `open-revision.sh` still writes the old layout (`## Subgoals — revision
  > <label>`); nothing writes `- [m] <label> — <note>` revision lines yet. So the label
  > rule can be tightened without breaking any index a tool wrote. And E14 must not point
  > at `/open-revision`, which today would write the wrong format into a revisions index.
  - [x] Create, not restore, a file that was never committed (e07b, both revisions)
  - [x] `git mv` a plan written under the other model (e07: `_DO.md` beside a missing
        `_TODO.md`)
    > **Done:** E7 now reads HEAD's history (`history_of`):
    > - in HEAD but deleted in the working tree → `git checkout HEAD -- <p>` (new case x16);
    > - deleted in a commit → `git checkout <sha>^ -- <p>`, naming the commit (new case
    >   e07c);
    > - never committed, with `_F′` beside it → `git mv` (e07);
    > - never committed → create it (e07b).
    >
    > Every branch keeps "or mark line n `[x]`". History is HEAD's alone, so a commit on
    > another fixture branch is never offered, which was Haiku's artefact in the trial.
  - [x] Name the exact goal file: `TODO/02-two.md` from the index line's title (e10)
    > **Done:** the slug is the title lowercased, with each run of other characters as `-`,
    > at most 40 characters. A file with the goal's number in another form is offered as a
    > `git mv` rather than a create (new case e10b, `2-two.md`).
  - [x] An unnumbered goal line: give it the next free number (`02`) and name the goal
        file to create, `TODO/02-<slug>.md` (e09)
    > **Done:** the next free number is one past the highest claimed or on file, padded
    > like the widest. An unclaimed goal file whose slug matches the title takes
    > precedence: "number it 03 to match its goal file" (new case e09b). Several
    > unnumbered lines are numbered in order.
  - [x] Say that the directory holds no plan at all, naming what it does hold (e02b)
    > **Done:** "holds no TODO.md (and no DO.md), only: README.md", with up to 10 entries.
    > If plans sit further down, they are listed instead (new case e02c).
  - [x] Remove a `**Layout**` header that no file justifies: no `TODO/` directory and
        unnumbered items (e08); `per-goal` on the root plan (e08b)
    > **Done:** `layout_fix` decides by evidence. On a branch plan, every item numbered or
    > goal files present → correct it to `per-goal` (new case e08c, `per goal`). On the
    > root plan, a `## Revisions` section → correct it to `revisions` (new case e08d,
    > `Revisions`). Otherwise remove the line, saying why.
  - [x] Name the exact header line to remove, or the section to add, for a revisions
        index without `## Revisions` (e05)
    > **Done:** the problem names the header's line. A near-miss heading is offered as a
    > rename (new case e05b, `## revisions`).
  - [x] Give each malformed revision line corrected (line 8's missing space). Leave a
        line's unknown marker to the user, listing the five. Warn that a revision made
        valid as `[~]` then needs its `_TODO.md` (e06)
  - [x] Name both duplicate goal files, and say that which is stale is the user's call
        (e11)
  - [x] When no revision is open and no plan file exists, say so, and offer to open a
        revision or create a plan. Never suggest reopening a closed revision that has no
        directory (e14)
    > **Done:** the fix says how to open a revision (its line and its `_F`), or points to
    > `/new-branch`, and never names a closed revision. If other active plans exist, it
    > lists them instead (new case e14b).
  - [x] When a tool fails (exit 3), add a hint to the stderr message: for `awk` or
        `git` not found (127), check `PATH` and say which binary was found first (f02)
    > **Done:** `die()` captures the failed command's status. For `awk`, `find`, `sort` and
    > `git` it adds a `hint:` line naming `command -v`'s binary and the status, with 127
    > read as not found. x13, x14 and x15 now assert the hint.
  - [x] A revision line whose label has a space (`- [~] 10 delta — y`) is E6, not
        revision `10`: after the label, require ` — ` or the end of the line. Add a new
        training case for it, not v17 (found while building the validation set)
    > **Done:** new case e06b, `- [x] 06 old — closed`: a closed revision, so the fix
    > rewrites the line and does not ask for a `_TODO.md`.
  - [x] `git` failing other than with 128 (missing: 127) exits 3 naming `git`, not E13
        "not inside a git repository". Add a new training shim case for it, not v21
        (found while building the validation set)
    > **Done:** new case x17, a `git` that exits 126. Only 128 is E13.
  - [x] The suite and mutants still pass, with new cases asserting each sharper line, and
        the spec is updated to match
    > **Result:**
    > - **Suite:** 82/82 (71 plus 11 new), twice under Bash 3.2 and 5, byte-identical, in
    >   about 30 s. It gains `nofix` and `noprob`, which assert that a counter-case's trap
    >   text is absent.
    > - **Training answer key:** 10/10.
    > - **Mutants:** 26. The three whose lines moved (m02, m05, n06) were reported stale,
    >   as designed, and re-anchored to the same rule; m02 now strips fences from all six
    >   readers. The ten new ones (q01–q10) each revert one new rule to the old blind line.
    >   25 are killed, each by the case built for its rule, and n05 is still equivalent.
    >   The run takes about 3 min.
    > - **Validation set:** not run, as the plan holds it back until goal 4.
    > - **Spec:** the E-table states each fix's evidence, alongside the label rule, the
    >   exit-3 hint, and the read-only and deterministic guarantees (which now name the
    >   history read).
    > **Note:** cost. The happy path went from 64 to 75 ms median, from parsing a larger
    > file; the E7 path from 68 to 121 ms, from the three `git` calls only it makes. Size
    > went from 23.5 KB to 38.1 KB. None of this reaches the model's context: Step 1 runs
    > the script and reads only its report.
- [ ] `/step` and `/hitl-step` offer a read-only investigation in the main session on an
      `error` or a failed run, and run it only when the user asks. The lockstep `sed`
      diff stays empty.
- [ ] Re-grade against the goal-10 answer key: 40/40. On every case, at least the best
      wrapper run; the full fix on e07, e08, e08b and e09; no case lower than today. The
      user runs the headless sessions. f03 is scored through the real `/hitl-step` and
      `/step`, whose Step 1 refuses a cut-short report (goal 12), and not through a probe
      that paraphrases Step 1. Then run the validation set once: every case must score 1
      or 2, and the number at 2 is recorded. If a case fails and is then fixed, both
      results are recorded and the set is marked spent.
