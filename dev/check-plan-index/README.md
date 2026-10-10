# check-plan-index.sh test suite

These are the tests for `plugins/workflow-claude/scripts/check-plan-index.sh`, the
read-only drift report for a per-goal plan: does each index line agree with its goal
file? They live here, outside the plugin, so they don't ship with it. The contract they
test is `per-goal-layout-spec.md` in the `feat-per-goal-layout` branch plan, and the
reasoning is in that plan's goal 3.

The script shares its rules with `locate-plan.sh` through `scripts/lib/plan-rules.sh`,
so a change to the library means running both this suite and `dev/locate-plan/`'s.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite            # outside this repository, as dev/locate-plan/ requires
python3 -I dev/check-plan-index/suite.py              # 33 cases, twice under each Bash found (~10 s)
python3 -I dev/check-plan-index/suite.py --mutants    # 18 mutants, every one must be caught (~1 min)
```

`-v` prints each report. `--script PATH` tests another copy, which must have
`lib/plan-rules.sh` beside it. `/opt/homebrew/bin/bash` is skipped if absent. Only BSD
userland has been tested.

- **The fixture** is one repository, `$LOCATE_PLAN_WORK/cpi`, with one plan directory
  per case, all on one commit. The script takes the index as an explicit path, so the
  cases don't need branches. It is rebuilt on every run. Three cases set up their
  conditions at run time:
  - `k18`: outside any repository, in `cpi-nogit`;
  - `k19`: a goal file made unreadable, then restored;
  - `k21`: an `awk` that exits 127, first on `PATH`.
- **Every report is checked** for:
  - key order and exit code;
  - the `problem:` and `fix:` text;
  - **one fix per problem**, since a command relays them in pairs;
  - the exact `open:` list where a case gives one;
  - no absolute paths;
  - that the fixture is left untouched;
  - the same output across runs and shells.
- **The static checks** look for Bash 3.2 hazards in the script and the library. A `>`
  inside awk code reads as a redirect to them, so write `NR == 1 ? … : …`, not `NR > 1`.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the script and its library. Each patch names its file
  relative to `scripts/`. A patch that no longer applies is reported as `STALE`.
  Re-anchor it, or drop it if its rule has gone. A mutant must be caught by the rule it
  breaks, not by a crash it causes on the way: check the `FAIL` line each one prints.
