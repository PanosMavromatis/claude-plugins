# memory-check.sh test suite

These are the tests for `plugins/workflow-coding/scripts/memory-check.sh`, the read-only
report of each plan file's size, classed by how the commands read it: bytes, words, lines
and ≈ tokens, with totals per branch and overall, and a warning for each file read whole
that is over the threshold. They live here, outside the plugin, so they don't ship with it.
The interface they test was settled in goal 01 of the `feat-memory-check` branch plan, and
the suite's shape in its goal 02.

The script shares its rules with the other plan scripts through `scripts/lib/plan-rules.sh`,
so a change to the library means running this suite with theirs.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite          # outside this repository, as dev/locate-plan/ requires
python3 -I dev/memory-check/suite.py            # 29 cases, twice under each Bash found (~20 s)
python3 -I dev/memory-check/suite.py --mutants  # 26 mutants, every one must be caught (~2 min)
```

`-v` prints each report. `--script PATH` tests another copy, which must have
`lib/plan-rules.sh` beside it. `/opt/homebrew/bin/bash` is skipped if absent. Only BSD
userland has been tested: `mc21-wc-padding` is caught because BSD `wc` pads its count, so
on GNU it would survive.

- **The fixtures** are seven small repositories under `$LOCATE_PLAN_WORK/mc`, one per kind
  of root plan, since the script reads the root before anything else. All are rebuilt on
  every run.
  - `rev`: a revisions root, with `07-rev` open and `05-old` closed. Its files are built to
    exact sizes. `01-alpha.md` is 1716 tokens, for the threshold's boundary; `chore-bad`
    and `02-beta.md` tie at 300 bytes, for the order of a tie; `fix-one` is over the
    default threshold. A spec, a `TODO/README.md` and a stray `DO.md` are there to be
    ignored, and `chore-bad`'s `**Layout**: revisions` to be measured as one file.
  - `leg`: a legacy root, with branch plans flat, grouped, and filed into a closed
    revision's directory, whose `_TODO.md` the tree does not count.
  - `two`, `zero`, `broken` and `noroot`: two revisions open, none open, one open with no
    `_TODO.md`, and no root plan.
  - `do`: the DO model, with TODO-model files beside it to be ignored.

  Three cases set up their conditions at run time: `m20` makes a goal file unreadable,
  `m21` runs outside any repository, and `m22` puts an `awk` that exits 127 first on
  `PATH`.
- **A measured report is checked line for line** against sizes the suite computes from the
  fixture's own bytes: each file's bytes, words, lines and ≈ tokens, their order, each
  branch's layout and totals, the total, every warning and the message.
- **Every report is checked** for:
  - key order and exit code;
  - no absolute paths;
  - one fix per problem, and no problem unless the result is an error;
  - the same output across runs and shells;
  - a fixture left untouched: `git status --porcelain`, untracked files included, and
    `HEAD`, as they were before the run.

  With exit 0 at thresholds on both sides of a file (`m02`–`m04`), that last check is the
  script's promise to write nothing and gate nothing.
- **The static checks** look for Bash 3.2 hazards in the script and the library. A `>`
  inside awk code reads as a redirect to them, so write `th < t`, not `t > th`.
- **`mutants/`** holds one unified diff per mutant, each one or more exact substitutions,
  applied fresh with fuzz 0 to a copy of the script and its library. Each patch names its
  file relative to `scripts/`. A patch that no longer applies is reported as `STALE`.
  Re-anchor it, or drop it if its rule has gone. A mutant must be caught by the rule it
  breaks, not by a crash it causes on the way: check the `FAIL` line each one prints.
  `mc26-writes` is caught only by the untouched-fixture check, which is what it is for.

## Calibration: the token ratio and the threshold

`memory-check.sh` estimates tokens as bytes × 3 / 7, and its threshold defaults to 2000 of
them. Both were set by measurement, in goal 03 of the `feat-memory-check` branch plan.

```bash
RUN=c2 python3 -I dev/memory-check/calibrate.py run      # 20 headless sessions on claude-opus-5-5, ~$1: run it yourself
RUN=c2 python3 -I dev/memory-check/calibrate.py report   # free
```

`calibrate.py` sends each of nine plan files in a one-turn session, raw and as `Read`
returns it, each line numbered in `cat -n` form, and subtracts the input tokens of a
baseline turn, run first and last, which must agree. Run it again after a Claude release
that changes the tokenizer, and change the ratio in the script, the suite's oracle and
`mc01-bytes-by-4` together.

- **Run `c1`, 2026-10-14.** The baseline was 29,803 tokens both times. Over the nine
  files, a token is 2.52 bytes raw and 2.34 as `Read` returns the file, from 2.06 for an
  index, whose short lines carry the most line numbers, to 2.74. bytes / 4, the rule
  `dev/measure-context.sh` uses and this script began with, was 42% low against the tokens
  as read; 3 / 7 is 2.33 bytes a token.
- **The default threshold** is about twice the median of R2's first goal files. In
  calibrated tokens its 17 merged goal files run from ≈219 to ≈1,906, median ≈963: 2000
  is above every one of them, and below all eight of R1's single-file plans.
- **The first baseline**, `-- 06-subagent-refactor-R1`: eight single-file plans, from
  ≈3,579 to ≈28,437 tokens (`feat-plan-locator`, the ≈16.6k of §4.8 in bytes / 4), ≈76k
  read whole in all. A `/hitl-step` on R2 reads an index and one goal file, ≈2.2k at most,
  where one on `feat-plan-locator` read ≈28.4k.
