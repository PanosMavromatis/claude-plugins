# close-revision.sh test suite

These are the tests for `plugins/workflow-coding/scripts/close-revision.sh`, the read-only
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
  runs each move as printed. The archive drops the section's trailing blank lines and keeps
  those inside it (`x21`), since tool output drops them and a copy would never match;
- **`--check`**: a correct close verifies, and a changed word, an archive keeping the trailing
  blank line (`k10`), a skipped move, an uncut root plan, or an extra edit does not; a check run after the commit is an error;
- **large inputs** (`b01`–`b05`): a root plan, a branch plan, a revision's `_TODO.md` and a
  directory listing, each well past the pipe buffer, read by a close and by its `--check`,
  so that no reader that wants one match stops before the end of its input. One that does
  leaves its writer (`cat`, `git show`, or the `printf` of the directory list) writing into
  a closed pipe, and the script dies of SIGPIPE, or, at the directory search, warns that a
  directory is missing when it is not.

Labels are compared **whole**: `07-rev` does not close `07-rev-2`.

The script uses `scripts/lib/plan-rules.sh`, so run this suite after a change to either.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite              # outside this repository, as dev/locate-plan/ requires
python3 -I dev/close-revision/suite.py             # 65 cases, twice under each Bash found (~60 s)
python3 -I dev/close-revision/suite.py --mutants   # 47 mutants, every one must be caught (~15 min)
```

`-v` prints each output. `--script PATH` tests another copy, with the library beside it.
`/opt/homebrew/bin/bash` is skipped if absent. Only BSD userland has been tested.

- **The fixture** is one repository, `$LOCATE_PLAN_WORK/crv`, with one orphan branch per
  case, since the script reads the repository's own `docs/plan/`. It is rebuilt on every
  run. `t01` puts an `awk` that exits 127 first on `PATH`; `t02` and `t03` put one that fails
  only for `section_line` or `pointer_line`, found by the label passed in `$L`, so each
  matcher's own failure is reached. `t04` and `t05` put a `cat` that kills itself with
  SIGPIPE first, and pin `die`'s two hints that blame neither PATH nor a tool: the writer's
  status 141, then status 3 from the reader's pipeline, which the writer's `die` failed.
  `g01` runs in a directory no repository contains.
- **The large inputs** (`b01`–`b05`) are padded to `BIG`, 512 KB. Measured on 0.10.0, whose
  readers stopped at their first match, every site failed every run from 256 KB, some runs
  at 128 KB, and none at 70 KB, so a case just over 64 KB would pass on the bug. `BIG`
  doubles 256 KB, for a margin on other pipe buffers and `awk` read sizes. The directory
  listing is about a thousand long-named directories below `grp/feat-gone`, the directory
  `feat/gone`'s backlink names, so the search finds it in the listing's first lines.
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
  through, and the script then fails reading the `_TODO.md` it does not have. Seven, `c38`
  to `c42`, `l04` and `l05`, each put `exit` back at one early-exit reader, and only the
  large inputs catch them: through SIGPIPE's exit 3, and for `c42`, whose reader fails
  silently, through `b01`'s false warning.
