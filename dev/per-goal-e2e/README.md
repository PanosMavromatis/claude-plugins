# Per-goal layout: end-to-end sessions

These run the real `/new-branch`, `/hitl-step` and `/step` headless on fresh consumer
repositories, and grade what they leave behind. The script suites (`dev/locate-plan/`,
`dev/check-plan-index/`, `dev/propose-branch-plan/`) test the scripts. This tests the
command text that drives them. The reasoning is in the `feat-per-goal-layout` branch plan,
goal 6.

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite           # outside this repository, as the suites require
RUN=r1 dev/per-goal-e2e/run.sh [e1 e3 e4 e5]    # real sessions, which cost money (~$2.75 for all)
RUN=r1 python3 -I dev/per-goal-e2e/check.py [e1 e3 e4 e5]
```

| Scenario | Fixture | Sessions |
|---|---|---|
| e1 | a revisions index with `07-rev` open | `/new-branch` for subgoal 2, then `/hitl-step 2` |
| e3 | the same, on the DO model | `/new-branch`, then `/step 2` |
| e4 | a legacy master plan | `/new-branch`, then `/hitl-step 1` |
| e5 | an index line behind its goal file | `/hitl-step 1`, which should offer the repair |

- **`build.py`** rebuilds the fixtures and a copy of the working tree's plugin, at a
  path that names nothing. Earlier runs' `out-*/` are kept. Each fixture's `CLAUDE.md`
  gives, in advance, the approvals the commands wait for. Sessions obey a fixture's
  `CLAUDE.md`, so the commands run unmodified.
- **`run.sh`** runs each session with only the copy loaded (`--plugin-dir`). It writes
  stream-json, which records every tool call and the result with its permission denials.
  `workflow-claude@mavromatis-ai-labs` is enabled only in this repository's project
  settings, so a fixture elsewhere loads no second copy. `check.py` confirms each run
  used the copy.
- **`check.py`** grades each fixture's end state, using the plugin's own read-only
  scripts. It also grades each session's sequence of tool calls, so ordering claims can
  fail:
  - the proposal ran before `git checkout -b`;
  - each goal file was edited before its index line;
  - the master plan was edited, not rewritten;
  - every script ran from the copy.

  It reports `Grep`, `Glob` and shell searches for reading. On fixtures no session has
  touched, it passes nothing.

Run `r1`, 2026-10-10:
- e1, e3 and e5 passed every check, with no `Grep`, `Glob` or shell searches.
- e4 found that `/hitl-step`'s legacy Step 6 awk was refused by Claude Code's safety
  check, because of a `|` inside an awk string. Once fixed (run `r2`), the awk is still
  not allow-listed. That is recorded in the master plan's next subgoal.
