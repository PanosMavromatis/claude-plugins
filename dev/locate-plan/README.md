# locate-plan.sh test suite

These are the tests for `plugins/workflow-claude/scripts/locate-plan.sh`, the script that
`/step` and `/hitl-step` run in Step 1 to find the plan. They live here, outside the
plugin, so they don't ship with it. They were built on the `feat/plan-locator` branch,
and the reasoning behind them is in that branch's plan, `docs/plan/feat-plan-locator/`
(goals 7–12). The spec they test is that directory's `locate-plan-spec.md`.

## Work directory

Everything is built and written under `$LOCATE_PLAN_WORK`, which must lie outside this
repository; every tool refuses a directory inside it. The fixtures are git repositories,
so building them inside the working tree would nest repositories in it.

**Don't name the work directory after this repository.** Claude Code stores a session's
transcript under a name derived from its working directory. In the goal-10 trial, a Haiku
agent decoded that name back into this repository's path, then read its real
`docs/plan/TODO.md` and used it as evidence. A neutral name such as `/tmp/lp-suite` gives
it nothing to decode.

## Direct tests: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite
python3 -I dev/locate-plan/suite.py              # 82 cases, twice under each Bash found (~30 s)
python3 -I dev/locate-plan/suite.py --mutants    # 26 mutants: 25 must be caught, n05 is equivalent (~3 min)
python3 -I dev/locate-plan/answer-key.py         # each mechanical full fix clears its case
```

**The validation set** (`v01`–`v22`) is held out: it was written and committed before any
`fix:` line was sharpened, so the fixes are not written to fit it.
- **Variants and counter-cases.** For each training problem there is a variant in another
  form, and where a sharper rule could fire without its evidence, a counter-case that
  needs a different fix. One example: a `_TODO.md` committed and then deleted is
  restored, not created.
- **Run on its own.** `suite.py --validation` runs these cases alone, checking what holds
  today; `answer-key.py --validation` checks `VKEY`'s mechanical fixes.
- **Graded once.** The fix lines are graded against `VKEY` at the final re-grade of
  `feat/locate-plan-diagnostics`. The gate there is no wrong advice: every case scores 1
  or 2.
- **Two cases are no longer held out:** v17 and v21 failed when the set was built, and
  exposed two defects, so their mechanical checks have been seen.

```bash
python3 -I dev/locate-plan/suite.py --validation          # builds fx-val on first use
python3 -I dev/locate-plan/answer-key.py --validation
```

- **`build-fixtures.sh`** builds `fx`, with one branch per c-case. It also builds the
  tool shims in `bin/<hash>/`: an `awk` that exits 127, an `awk` that fails only on the
  `**Layout**` read, a `git` whose `symbolic-ref` fails, and for the validation set a
  missing `git` (127) and an `awk` that fails every call. `suite.py` runs it if `fx` is
  missing; rerun it with `--rebuild` after adding a shim.
- **`suite.py`** builds `fx-diag`, the error, warning and edge cases, on first use. It
  runs every case directly and grades each report: key order, exit code, `problem:` and
  `fix:` text, determinism across runs and shells, no absolute paths, and that the
  fixtures are left untouched. It also checks the script statically for Bash 3.2
  hazards. `-v` prints each report; `--script PATH` tests another copy.
  `/opt/homebrew/bin/bash` is skipped if absent. Only BSD userland has been tested.
- **`mutants/`** holds one unified diff per mutant, applied fresh to today's script with
  fuzz 0. If an edit to the script stops a patch applying, it is reported as `STALE`
  rather than quietly testing old code. Re-anchor it, or drop it if its rule has gone.
- **`answer-key.py`** holds `KEY`: for every error and fault case, the full fix (scores
  2), the weaker fix (1), and the over-reach to watch for (−1). It was written before
  any trial arm ran. `verify()` applies each mechanical full fix to a clone of its
  fixture branch and confirms that it clears the case.

## The trial: headless sessions, which cost money

`trial/` reruns the goal-10 comparison of Step 1 as shipped (the baseline) against a
subagent, `plan-resolver.md`, that wraps the script on Haiku or Sonnet. It also reruns
goal 12's check that Step 1 refuses a report cut short. The person running it starts
these sessions; Claude does not.

```bash
python3 -I dev/locate-plan/trial/build-arms.py           # arms and fault copies in p/<hash>/
ARM=baseline RUN=t1 dev/locate-plan/trial/run.sh all     # c01–c20, e01–e14, f01–f05, t-hitl, t-step
python3 -I dev/locate-plan/trial/grade.py extract        # transcripts -> $LOCATE_PLAN_WORK/trial.json
python3 -I dev/locate-plan/trial/grade.py table          # truth, honesty, vetting, next-check, writes
python3 -I dev/locate-plan/trial/grade.py diag e07 e10   # what each arm said, side by side
python3 -I dev/locate-plan/trial/show-session.py baseline t1 e07
```

- **Hashed names.** Each arm, and each fault copy (f03 cut short, f04 a wrong answer,
  f05 a swapped path), sits at `p/<8 hex>/workflow-claude`. The fault wrappers carry no
  comments, and the real script sits outside the plugin root. In the trial the copies
  were named `-trunc`, `-wrong` and `-swap`, and sessions noticed: a baseline f03 reply
  said "this is the `-trunc` baseline script". Some hints remain, from fixture names the
  cases depend on: branch names such as `d/e07`, and `nogit` for e13.
- **Fix scores.** These are graded by hand, against `KEY`, in `trial/hand-grades.tsv`,
  one row per session with its reason. `grade.py evidence` combines them with
  `trial.json` into `trial-evidence.json`, and `grade.py scores` derives `scores.json`.

## What is tracked

- **`trial-evidence.json`**: the goal-10 trial, one record per session (246). Each
  holds the mechanical grades, cost and timing, the agent's tool calls, and, for the
  120 graded sessions, the text that was graded with its score. The script's direct
  output is stored once per case. Paths are rewritten as `$WORK`, `$REPO`, `$SCRATCH`
  and `$USER`.
- **`scores.json`**: per case, each arm-run's score, the best wrapper's score, today's
  script, and the requirement.
  - The per-session grades were regenerated on 2026-10-09, because the originals had
    not been kept. The per-case bar reproduces exactly. Three arm-run totals land one
    point from those recorded in goal 10, each on a borderline call that the TSV
    explains.
- **Not tracked:** transcripts, `claude -p` output and `trial.json`. They live in the
  work directory and hold absolute paths and session content.

`feat/locate-plan-diagnostics` is accepted when every scored case reaches 2 (40 of 40).
At its start, today's script scored 28.
