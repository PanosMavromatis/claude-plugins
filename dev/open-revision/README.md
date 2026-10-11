# open-revision.sh test suite

These are the tests for `plugins/workflow-claude/scripts/open-revision.sh`, the read-only
proposal `/open-revision` runs before it inserts a revision section into the master plan.
They live here, outside the plugin, so they don't ship with it. The reasoning is in the
`feat-master-plan` branch plan, goals 1 and 2.

The suite tests the script's refusals. A revision that is already open or closed, or whose
directory exists, must be refused, and every other label must get a proposal. All three
checks compare **whole labels**: `07-rev-2` being open does not refuse `07-rev`, and
`05-x-2` being closed does not refuse `05-x`. A closed revision is the pointer
`/close-revision` writes, `- **Revision <label>** — closed`, with or without a subtitle;
the guard used to look for a form that is never written, so it refused nothing.

The script does not use `scripts/lib/plan-rules.sh`, so a change to the library does not
require this suite.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite              # outside this repository, as dev/locate-plan/ requires
python3 -I dev/open-revision/suite.py              # 15 cases, twice under each Bash found (~6 s)
python3 -I dev/open-revision/suite.py --mutants    # 9 mutants, every one must be caught (~20 s)
```

`-v` prints each output. `--script PATH` tests another copy. `/opt/homebrew/bin/bash` is
skipped if absent. Only BSD userland has been tested.

- **The fixture** is one repository, `$LOCATE_PLAN_WORK/orv`, with one orphan branch per
  case, since the script reads the repository's own `docs/plan/`. It is rebuilt on every
  run. `o15` puts an `awk` that exits 127 first on `PATH`.
- **Every run is checked** for:
  - the exit code;
  - the refusal text on stderr, naming the line that caused it;
  - no proposal printed with a refusal, and nothing on stderr with a proposal;
  - the line a proposal would insert at;
  - no absolute paths;
  - that the fixture is left untouched;
  - the same output across runs and shells.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the script. Each patch names its file relative to
  `scripts/`. A patch that no longer applies is reported as `STALE`. Re-anchor it, or
  drop it if its rule has gone. A mutant must be caught by the case aimed at its rule, not
  by a crash: check the `FAIL` line each one prints.
