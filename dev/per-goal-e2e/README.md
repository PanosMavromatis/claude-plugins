# Per-goal layout: end-to-end sessions

These run the real `/new-branch`, `/hitl-step`, `/step`, `/smart-merge`, `/master-plan`,
`/open-revision` and `/close-revision` headless on fresh consumer repositories, and grade what
they leave behind. The script suites
(`dev/locate-plan/`, `dev/check-plan-index/`, `dev/propose-branch-plan/`,
`dev/propose-merge-record/`) test the scripts. This tests the command text that drives
them. The reasoning is in the `feat-per-goal-layout` branch plan, goal 6, and for the
merge sessions in the `feat-smart-merge-locate-plan` branch plan, goal 6, and for the
revision sessions in the `feat-master-plan` branch plan, goal 6.

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite           # outside this repository, as the suites require
RUN=r1 dev/per-goal-e2e/run.sh [e1 … c3]         # real sessions, which cost money ($5.55 for e1, e3, e4 and $2.23 for m1, m2, c1, c2 in r12)
RUN=r1 python3 -I dev/per-goal-e2e/check.py [e1 … c3]
```

| Scenario | Fixture | Sessions |
|---|---|---|
| e1 | a revisions index with `07-rev` open | `/new-branch` for subgoal 2, then `/hitl-step 2`, then `/smart-merge` |
| e3 | the same, on the DO model | `/new-branch`, then `/step 2`, then `/smart-merge` |
| e4 | a legacy master plan | `/new-branch`, then `/hitl-step 1`, then `/smart-merge` |
| e5 | an index line behind its goal file | `/hitl-step 1`, which should offer the repair |
| m1 | a revisions index, `07-rev` open, and a spec | `/master-plan 08-next docs/spec/08-next.md`: an appended index line |
| m2 | a legacy root plan with nothing open | `/open-revision 04-next …`, the alias: the root plan converted |
| m3 | a legacy root plan with a revision open | `/master-plan 04-next … --dry-run dry-run`: refused, drafted anyway |
| c1 | a revisions index, `07-rev` finished | `/close-revision 07-rev`: the stamp |
| c2 | a finished legacy section, two merged flat plans and one active | `/close-revision 03-old`: the cut, the archive, the moves |
| c3 | a revisions index, `07-rev` unfinished | `/close-revision 07-rev`: refused |

- **`build.py`** rebuilds the fixtures and a copy of the working tree's plugin, at a
  path that names nothing. Earlier runs' `out-*/` are kept. Each fixture's `CLAUDE.md`
  gives, in advance, the approvals the commands wait for. Sessions obey a fixture's
  `CLAUDE.md`, so the commands run unmodified.
- **`run.sh`** runs each session with only the copy loaded (`--plugin-dir`). It writes
  stream-json, which records every tool call and the result with its permission denials.
  `workflow-coding@mavromatis-ai-labs` is enabled only in this repository's project
  settings, so a fixture elsewhere loads no second copy. `check.py` confirms each run
  used the copy.
- **`check.py`** grades each fixture's end state, using the plugin's own read-only
  scripts. It also grades each session's sequence of tool calls, so ordering claims can
  fail:
  - the proposal ran before `git checkout -b`;
  - each goal file was edited before its index line;
  - the master plan was edited, not rewritten;
  - every script ran from the copy;
  - every command ran alone, and none as `git -C`, in every session, as the commands say:
    `allowed-tools` matches a command's plain form only, and refuses a whole chain for any
    one part it does not grant. A chain of granted commands is not refused, but it still
    fails this check, since the next chain may hold a part that is.
  - no session read or searched the plugin copy's directory from the shell, and one that
    commits `Read` `smart-commit.md` first, as the five pointers to it say: in a real
    install the plugin sits outside the repository, where a shell read prompts, and here a
    merge session's `--add-dir /tmp` would let one through unrefused, so only this check
    sees it.

  It reports `Grep`, `Glob` and shell searches for reading. On fixtures no session has
  touched, it passes nothing. In the TODO model it also checks that `/new-branch` wrote
  each goal file with a `- [ ]` subgoal, reading them from the branch's first commit,
  since the step session ticks them afterwards.
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

- **The revision sessions** (`m*`, `c*`) take what a session should have written from the
  copy's own scripts, run on a clone of the fixture at `main` (`_main/`): the root plan is
  `--render`'s for the note the session chose, the stamp is the proposal's `edits:`, the
  cut is `--render archive` and `root`. Each must also have proposed before `git checkout -b`,
  spawned `workflow-coding:plan-drafter` (the drafter's own calls, `parent_tool_use_id` set,
  are not counted as the session's), left the spec to the drafter, written the root plan
  from `--render`, and run its checks after the last write and before the one commit. `c2`
  alone is allowed `git mv`, the gate `/close-revision` leaves to the prompt.
- **What they do not test: the review.** `/master-plan` step 4 is where a user reads the draft,
  and the fixture's `CLAUDE.md` approves it in advance. So the draft is graded on form
  (`subdividing.md`'s), on the spec's settled decision being copied, and on a tripwire: each
  spec unit names one file, and each must reach a subgoal, in order. That catches a dropped
  unit, never an invented one, since nearly any extra subgoal names `CHANGELOG.md`. Read the
  drafts after a run (`git -C m1 show chore/open-08-next:docs/plan/08-next/_TODO.md`). A
  scenario that spawns an agent needs a content check or a named reader, not a form check
  alone.

Run `r1`, 2026-10-10:
- e1, e3 and e5 passed every check, with no `Grep`, `Glob` or shell searches.
- e4 found that `/hitl-step`'s legacy Step 6 awk was refused by Claude Code's safety
  check, because of a `|` inside an awk string. Once fixed (run `r2`), the awk is still
  not allow-listed. That is recorded in the master plan's next subgoal.

Run `r6`, 2026-10-11, the revision sessions: 102 checks, 0 failing, $2.39. The three drafts,
read by hand, are faithful to the spec. Reading the sessions found what no check had: `c2`'s
first `--check` failed, because tool output drops the section's trailing blank line and the
archive's `Write` came out a line short. The archive now drops trailing blank lines.

Run `r11`, 2026-10-13, e1, e3, e4 and e5 after `fix-command-phrasing`: every check passed,
$5.96. The seven `/new-branch` and step sessions had no permission denials, against 6 in
`r9` and 2 in `r10`, each caused by a `git -C`, a chain with a part not granted, or a
search of the plugin's directory. The chain check now runs on every session, and passes
over a basic regex's `\|`, which it first took for a pipe. Two merge sessions `grep`ped
`smart-commit.md` at its path before reading it, let through only by `--add-dir /tmp`; the
commands now say to `Read` it whole.

Run `r12`, 2026-10-13, e1, e3, e4, m1, m2, c1 and c2 on the 0.10.1 command text, after
`check.py` began failing a shell read or search of the plugin copy: every check passed,
$7.78. Each of the ten sessions that commit `Read` `smart-commit.md` before its first
commit, and none of the 13 touched the plugin's directory from the shell, where `r11`'s
merge sessions had `grep`ped it twice; regraded, `r11` fails the new check on exactly
those two. The five reworded pointers hold.
