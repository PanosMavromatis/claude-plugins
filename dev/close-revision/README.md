# close-revision.sh test suite

These are the tests for `plugins/workflow-claude/scripts/close-revision.sh`, the read-only
proposal `/close-revision` runs before it closes a revision, and again with `--check` before
it commits. They live here, outside the plugin, so they don't ship with it. The contract is
`close-revision-spec.md` in the `feat-master-plan` branch plan, and the reasoning is that
plan's goal 5.

The suite tests both kinds of close:

- **a stamp, under a revisions index**: the two edits, every refusal (a label not listed, or
  not `[~]`; a `**Status**:` missing or not `open`; an open item at any indent), and the
  warning for a branch plan inside the revision still stamped `active`;
- **a cut, under a legacy root plan**: the section, the pointer, and the moves that file the
  revision's merged branch plans (the job `/file-plans` did), with `--render archive` and
  `--render root` byte for byte, including CRLF plans and every place the pointer can go,
  and a backlink holding shell syntax, for which no move is printed (`x20`): the command
  runs each move as printed;
- **`--check`**: a correct close verifies, and a changed word, a skipped move, an uncut root
  plan, or an extra edit does not; a check run after the commit is an error.

Labels are compared **whole**: `07-rev` does not close `07-rev-2`.

The script uses `scripts/lib/plan-rules.sh`, so run this suite after a change to either.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite              # outside this repository, as dev/locate-plan/ requires
python3 -I dev/close-revision/suite.py             # 56 cases, twice under each Bash found (~40 s)
python3 -I dev/close-revision/suite.py --mutants   # 38 mutants, every one must be caught (~8 min)
```

`-v` prints each output. `--script PATH` tests another copy, with the library beside it.
`/opt/homebrew/bin/bash` is skipped if absent. Only BSD userland has been tested.

- **The fixture** is one repository, `$LOCATE_PLAN_WORK/crv`, with one orphan branch per
  case, since the script reads the repository's own `docs/plan/`. It is rebuilt on every
  run. `t01` puts an `awk` that exits 127 first on `PATH`; `t02` and `t03` put one that fails
  only for `section_line` or `pointer_line`, found by the label passed in `$L`, so each
  matcher's own failure is reached. `g01` runs in a directory no repository contains.
- **A `--check` case** (`k01`–`k07`) first writes what the close would write, by hand, from
  strings in the suite and never from the script's own `--render`: a wrong render would
  otherwise produce the very file a wrong check approves. The runner records the working
  tree's state, runs the script, requires the state unchanged, and resets. `k08` and `k09`
  commit the closed state instead, so `HEAD` already holds it.
- **Every run is checked** for:
  - the exit code;
  - the twelve report keys, in order, each value exact, or `—` where the case names none;
  - a render, byte for byte: output is read as bytes, since `text=True` would turn `\r\n`
    into `\n` and hide a carriage return the render kept;
  - nothing on stderr with a report or a render;
  - no absolute paths, except in a tool failure's `PATH` hint;
  - that the fixture is left untouched;
  - the same output across runs and shells.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the script and the library. Each patch names its file
  relative to `scripts/`. A patch that no longer applies is reported as `STALE`. Re-anchor
  it, or drop it if its rule has gone. A mutant must be caught by the case aimed at its
  rule, not by a crash: check the `FAIL` line each one prints. Two are caught through an
  exit 3 that is the mutant's own consequence: `c05` and `c06` let an unlisted label
  through, and the script then fails reading the `_TODO.md` it does not have.
