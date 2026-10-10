# propose-merge-record.sh test suite

These are the tests for `plugins/workflow-claude/scripts/propose-merge-record.sh`, which
`/smart-merge` runs in step 7 to find what recording a merge edits: the branch plan's status
line, and the master-plan item that backlinks the branch, with the line its `> **Done:**`
goes after. They live here, outside the plugin, so they don't ship with it. The contract
they test is in the script's header and the `feat-smart-merge-locate-plan` branch plan,
goal 3.

The script shares its rules with `locate-plan.sh`, `check-plan-index.sh` and
`propose-branch-plan.sh` through `scripts/lib/plan-rules.sh`; in particular it chooses its
master files with `master_files`, the function `propose-branch-plan.sh` places backlinks
with. After a change to the library, run all four suites.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite              # outside this repository, as dev/locate-plan/ requires
python3 -I dev/propose-merge-record/suite.py              # 37 cases, twice under each Bash found (~15 s)
python3 -I dev/propose-merge-record/suite.py --mutants    # 18 mutants, every one must be caught (~2 min)
```

`-v` prints each report. `--script PATH` tests another copy, which must have
`lib/plan-rules.sh` beside it. `/opt/homebrew/bin/bash` is skipped if absent. Only BSD
userland has been tested.

- **The fixture** is one repository, `$LOCATE_PLAN_WORK/pmr`, with one orphan branch per
  case, since each case needs its own plans. The script never reads the current branch,
  so checking a case out changes nothing but the files. It is rebuilt on every run.
- **Every report is checked** for:
  - key order and exit code;
  - the listed values (`layout:`, `masters:`, `stamp:`, `item:`, `after:`, `subgoal:`,
    the candidates, the warnings, exactly);
  - one fix per problem, and candidates only on an `ask`;
  - no absolute paths;
  - that the fixture is left untouched;
  - the same output across runs and shells.
- **The cases that guard the reasons the script exists:**
  - m01 and m02: a branch matches only as a whole `> **Branch:**` value, so `feat/x` does
    not find `feat/x-y`'s item. A `grep -F` lookup does.
  - m03: a branch named only in prose or a fenced block matches nothing.
  - m01: `after:` is the block's last line, below the Q&A under the backlink.
  - m04: a duplicated backlink is an `ask`, and a candidate's text arrives whole, tabs
    and all.
  - m17: under a revisions index, a closed revision's `_TODO.md` is not searched.
- **m29 plays a branch's whole life through the scripts.** In a clone, it writes what
  `propose-branch-plan.sh` proposes, as `/new-branch` does, and then checks four things:
  - this script finds exactly that item;
  - once its proposal is applied, as `/smart-merge` does, `locate-plan.sh` sees the plan
    as merged;
  - a second run warns twice that the merge may be recorded already, with `after:` still
    inside the block;
  - `propose-branch-plan.sh` no longer offers the closed subgoal.

  If the writer and the reader of a backlink drifted apart, this case is where it would
  show.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the script and its library. Each patch names its file
  relative to `scripts/`. A patch that no longer applies is reported as `STALE`. A
  mutant must be caught by the rule it breaks, so check the `FAIL` line each one prints.
