# propose-revision.sh test suite

These are the tests for `plugins/workflow-claude/scripts/propose-revision.sh`, the read-only
proposal `/master-plan` runs before it drafts a revision, and again with `--render` for the
root plan it writes. They live here, outside the plugin, so they don't ship with it. The
contract is `propose-revision-spec.md` in the `feat-master-plan` branch plan, and the
reasoning is that plan's goal 4.

The suite tests every layout the root plan can be in:

- **none**: a revisions index is created;
- **a revisions index**: the new line is appended after the last revision line, and a label
  listed under any marker, or whose directory exists, is refused;
- **legacy, with a revision still open**: refused, naming the open section;
- **legacy, with nothing open**: converted, byte for byte, including a CRLF plan, a missing
  `**Status**:` line, an existing `**Layout**:` line, and a missing `## Closed revisions`.

Labels are compared **whole**: `07-rev-2` does not refuse `07-rev`. The cases `l01`–`l12`
are `dev/open-revision/`'s `o01`–`o11` and `o15`, ported (its `o12`–`o14` became `n01` and
the usage cases), and its nine mutants are `v01`–`v09`: the matchers they pin moved from
`open-revision.sh` into `scripts/lib/plan-rules.sh` as `section_line` and `pointer_line`.

The script uses the library, so run this suite after a change to either.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite                 # outside this repository, as dev/locate-plan/ requires
python3 -I dev/propose-revision/suite.py              # 72 cases, twice under each Bash found (~30 s)
python3 -I dev/propose-revision/suite.py --mutants    # 36 mutants, every one must be caught (~7 min)
```

`-v` prints each output. `--script PATH` tests another copy, with the library beside it.
`/opt/homebrew/bin/bash` is skipped if absent. Only BSD userland has been tested.

- **The fixture** is one repository, `$LOCATE_PLAN_WORK/prv`, with one orphan branch per
  case, since the script reads the repository's own `docs/plan/`. It is rebuilt on every
  run. `l12` puts an `awk` that exits 127 first on `PATH`. `l14` and `l15` put one that
  fails only for `section_line` or `pointer_line`, found by the label passed in `$L`, so
  each matcher's own failure is reached. `d07` uses a symlink into the fixture's
  `docs/plan/`, and `g01` runs in a directory no repository contains.
- **Every run is checked** for:
  - the exit code;
  - the ten report keys, in order, each value exact, or `—` where the case names none;
  - a render, byte for byte: output is read as bytes, since `text=True` would turn `\r\n`
    into `\n` and hide a carriage return the render kept;
  - nothing on stderr with a report or a render, except a refused render's report;
  - no absolute paths, except in a tool failure's `PATH` hint;
  - that the fixture and the dry-run directory are left untouched;
  - the same output across runs and shells.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the script and the library. Each patch names its file
  relative to `scripts/`. A patch that no longer applies is reported as `STALE`. Re-anchor
  it, or drop it if its rule has gone. A mutant must be caught by the case aimed at its
  rule, not by a crash: check the `FAIL` line each one prints.
