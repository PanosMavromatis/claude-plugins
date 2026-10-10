# propose-branch-plan.sh test suite

These are the tests for `plugins/workflow-claude/scripts/propose-branch-plan.sh`, which
`/new-branch` runs to decide where a new branch's plan goes, what its goal files are
called, and where its master-plan backlink is inserted. They live here, outside the
plugin, so they don't ship with it. The contract they test is `per-goal-layout-spec.md`
in the `feat-per-goal-layout` branch plan, and the reasoning is in that plan's goal 4.

The script shares its rules with `locate-plan.sh` and `check-plan-index.sh` through
`scripts/lib/plan-rules.sh`, and with `propose-merge-record.sh`, which finds the backlinks
this one places. After a change to the library, run all four suites.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite              # outside this repository, as dev/locate-plan/ requires
python3 -I dev/propose-branch-plan/suite.py              # 32 cases, twice under each Bash found (~20 s)
python3 -I dev/propose-branch-plan/suite.py --mutants    # 18 mutants, every one must be caught (~2 min)
```

`-v` prints each report. `--script PATH` tests another copy, which must have
`lib/plan-rules.sh` beside it. `/opt/homebrew/bin/bash` is skipped if absent. Only BSD
userland has been tested.

- **The fixture** is one repository, `$LOCATE_PLAN_WORK/pbp`, with one orphan branch per
  case, since each case needs its own root plan. The script never reads the current
  branch, so checking a case out changes nothing but the files. It is rebuilt on every
  run.
- **Every report is checked** for:
  - key order and exit code;
  - the listed values (`layout:`, `revision:`, `subgoal:`, `dir:`, `index:`, `goals:`,
    `backlink:`, the candidates, the warnings);
  - one fix per problem;
  - no absolute paths;
  - that the fixture is left untouched;
  - the same output across runs and shells.
- **p24 checks the writer against the readers.** In a clone, it writes exactly what a
  proposal lists, as `/new-branch` does: the index, the goal files and the backlink. It
  then checks four things:
  - `locate-plan.sh` resolves the plan at rung 2 as per-goal, with the first goal file;
  - `check-plan-index.sh` finds it clean;
  - a second proposal for the same branch is refused;
  - the backlinked subgoal is no longer a candidate.

  If the slug rule or the index-line form drifted between writer and reader, this case
  is where it would show.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the script and its library. Each patch names its file
  relative to `scripts/`. A patch that no longer applies is reported as `STALE`. A
  mutant must be caught by the rule it breaks, so check the `FAIL` line each one prints.
