# Per-goal layout: end-to-end sessions

These run the real `/new-branch`, `/hitl-step`, `/step` and `/smart-merge` headless on
fresh consumer repositories, and grade what they leave behind. The script suites
(`dev/locate-plan/`, `dev/check-plan-index/`, `dev/propose-branch-plan/`,
`dev/propose-merge-record/`) test the scripts. This tests the command text that drives
them. The reasoning is in the `feat-per-goal-layout` branch plan, goal 6, and for the
merge sessions in the `feat-smart-merge-locate-plan` branch plan, goal 6.

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite           # outside this repository, as the suites require
RUN=r1 dev/per-goal-e2e/run.sh [e1 e3 e4 e5]    # real sessions, which cost money (~$2.75 for all, before the merge sessions)
RUN=r1 python3 -I dev/per-goal-e2e/check.py [e1 e3 e4 e5]
```

| Scenario | Fixture | Sessions |
|---|---|---|
| e1 | a revisions index with `07-rev` open | `/new-branch` for subgoal 2, then `/hitl-step 2`, then `/smart-merge` |
| e3 | the same, on the DO model | `/new-branch`, then `/step 2`, then `/smart-merge` |
| e4 | a legacy master plan | `/new-branch`, then `/hitl-step 1`, then `/smart-merge` |
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
- **The merge sessions** (`e1-merge`, `e3-merge`, `e4-merge`) each run in a fresh clone of
  their scenario's fixture (`r1m`, `r3m`, `r4m`), on the branch the step session left, so
  the fixture stays as the other checks grade it. The step session's work is uncommitted
  (the fixture's `CLAUDE.md` says so), so `run.sh` copies the working tree into the clone
  and commits it, as a user would before merging; then it adds a local `main`, marks that
  tip `refs/e2e/pre` for `check.py`, and removes `origin`, so the clone has no remote, as
  its `CLAUDE.md` says. A real `/smart-merge` needs GitHub, so:
  - `gh` is a stub `build.py` writes, put first on `PATH`. `pr create` answers PR #42, with
    no PRs before it and no checks; `pr merge` does nothing. Every call is logged to
    `out-<run>/<session>.gh`, with the body file copied in.
  - MCP is off (`--strict-mcp-config`), and the GitHub server's tools are denied besides,
    since a session that guessed an owner and repository could reach a real one.
    `check.py` fails a session that lists any MCP server at init or calls one.
  - Two operations `/smart-merge` deliberately leaves to the harness prompt, `git rm` and
    `gh pr merge`, are allowed for these sessions only, so "no permission denials" still
    means something. The third, the `rm` of the body file, is denied even when allowed
    (run `r4`), so `check.py` reports that one denial as the gate it is.

  `check.py` checks that every command ran alone, that steps 2 and 7 ran their scripts,
  that no MCP server was loaded or called, that the index is stamped
  merged with PR #42, that the master file changed by exactly the closed subgoal and a
  Done line after its block, in one commit of exactly those two files, and that the PR
  body names the plan.

Run `r1`, 2026-10-10:
- e1, e3 and e5 passed every check, with no `Grep`, `Glob` or shell searches.
- e4 found that `/hitl-step`'s legacy Step 6 awk was refused by Claude Code's safety
  check, because of a `|` inside an awk string. Once fixed (run `r2`), the awk is still
  not allow-listed. That is recorded in the master plan's next subgoal.
