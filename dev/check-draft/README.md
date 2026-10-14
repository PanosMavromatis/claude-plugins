# check-draft.sh test suite

These are the tests for `plugins/workflow-coding/scripts/check-draft.sh`, the read-only
check of a revision's master plan before it is committed: `plan-drafter`'s reply before
the user reviews it (the draft's form, the trace, and with `--spec` its tags), and with
`--plan` the plan file as written, after the review's edits. They live here, outside the
plugin, so they don't ship with it. The contract they test is the script's header
comment, and the reasoning is in goal 02 of the `feat-master-plan-checks` branch plan.

The script reads subgoal blocks with `SUBGOALS_AWK` from `scripts/lib/plan-rules.sh`, so
a change to the library means running this suite with the other library suites.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite            # outside this repository, as dev/locate-plan/ requires
python3 -I dev/check-draft/suite.py              # 121 cases, twice under each Bash found (~10 s)
python3 -I dev/check-draft/suite.py --mutants    # 82 mutants, every one must be caught (~2 min)
```

`-v` prints each report, and case ids select cases. `--script PATH` tests another copy,
which must have `lib/plan-rules.sh` beside it. `/opt/homebrew/bin/bash` is skipped if
absent. Only BSD userland has been tested.

- **The fixture** is a directory, `$LOCATE_PLAN_WORK/cd`, with one subdirectory per case
  and the spec the tags are checked against, in LF and CRLF. The script takes its paths as
  given and runs no `git`, so there is no repository. It is rebuilt on every run. Three
  cases set up their conditions at run time:
  - `u09`: a reply made unreadable, then restored;
  - `u10`, `u10b`: an `awk` that exits 127, first on `PATH`.
- **The cases** come in five groups:
  - `s`: the reply's sections, its fence and its trace, and a reply copied inside the frame
    Claude Code puts around a subagent's report (a note before it, an agent id and usage
    after it, every line indented two spaces), as the session sees it;
  - `t`: the trace's tags, against the spec, and the window of the spec each points to;
  - `f`: the draft's form. Each runs on both inputs: as a reply (its id ends `r`), the draft
    in its fence with a trace that covers it, and as a plan file (`p`), the draft alone. A
    draft's line k is line k of the plan and line k + 3 of the reply;
  - `p`: a plan file after a review's edits, and an input given the wrong way;
  - `u`: usage, and files that cannot be checked.
- **Every report is checked** for:
  - key order and exit code;
  - the `problem:` and `fix:` text;
  - **one fix per problem**, since a command relays them in pairs;
  - the `where:` window of each resolved tag, and no `where:` without a spec;
  - the message its input calls for: a fresh reply from `plan-drafter`, questions for the
    user when the only problems are tags that name nothing in the spec, the reply file
    written again when it was copied in its frame, or a corrected plan file;
  - nothing on stderr beside a report, and no absolute paths;
  - that no file was changed;
  - the same output across runs and shells.
- **The static checks** look for Bash 3.2 hazards in the script and the library. A `>`
  inside awk code reads as a redirect to them, so write `fc <= NR`, not `NR >= fc`.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the script and its library. Each patch names its file
  relative to `scripts/`. A patch that no longer applies is reported as `STALE`.
  Re-anchor it, or drop it if its rule has gone. A mutant must be caught by the rule it
  breaks, not by a crash it causes on the way: check the `FAIL` line each one prints.
  Six fail by a crash that is that rule's symptom: `d04` and `d06` (an unchecked file
  reaches `awk`), `d16` (an unclosed fence reaches the draft's checks), and `d14`, `d43`
  and `d57` (a `\r` left in the report).
