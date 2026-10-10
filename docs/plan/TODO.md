# Master plan — claude-plugins

**Status**: active

The marketplace's master plan, covering both plugins. Each revision below is a
milestone whose subgoals each spawn a branch; `/close-revision` moves a finished
revision into `docs/plan/<label>/`.

## Subgoals — revision 06-subagent-refactor-R1

The second step of the subagent refactor; R0 (`05-subagent-refactor-R0`) set up versions,
the marketplace install and the context baseline. R1 moves two jobs out of the main
session. Finding the plan and goal a command is working on goes to a deterministic
script, `scripts/locate-plan.sh`: it was first built as an agent, `plan-locator`, and
that agent's test suite showed a job made only of rules belongs in a script
(`feat-plan-locator`). Writing a master plan from a design document goes to an agent,
`plan-drafter`, which the new `/master-plan` command runs. R1 also adds the per-goal
plan layout.
The installed 0.9.0 driver does the work, on the old layout. This revision **builds**
the new layout but does not **adopt** it. This repository's own plans stay in the
old form until the first step of R2, which runs on the 0.10.0 release this revision
ends with. Settled, and not to be reopened:
- Legacy single-file branch plans stay readable through 1.x.
- `/file-plans` becomes legacy-only and `/open-revision` becomes an alias. Neither is removed.
- Every agent is written with plugin-dev's `agent-development` and checked by
  `plugin-validator` before the bump.

- [x] `scripts/locate-plan.sh` resolves the plan for `/step` and `/hitl-step`: Step 1 of
      both runs it, the shared Step 1 text shrinks, and the lockstep `sed` check is
      updated to match. (Built first as the agent `agents/plan-locator.md`, which the
      branch's test suite replaced.)
  > **Branch:** feat/plan-locator
  > **Done:** `locate-plan.sh` resolves the plan, and Step 1 of both commands runs it alone,
  > relays its diagnostics and refuses a report cut short. A 246-session trial found a
  > subagent wrapping the script adds cost but no correctness, so none ships — PR #5
- [ ] Sharper diagnostics from `scripts/locate-plan.sh`. Its `fix:` lines say what the
      repository already shows:
      - create a file that was never committed, rather than restore it;
      - `git mv` a plan written under the other model;
      - name the exact goal file;
      - say that a directory holds no plan at all;
      - remove a header that no file justifies.
      `/step` and `/hitl-step` also offer, on an `error` or a failed run, to investigate
      read-only in the main session, if the user asks. First bring the test suite,
      fixtures and answer key from `feat-plan-locator` goal 10 into the repository: today
      they exist only in a session scratchpad. Accepted at 40 of 40, re-graded against
      that answer key. On every case the script must score at least the best wrapper run,
      and reach the full fix on e07, e08, e08b and e09, where no arm reached one, with no
      case lower than today. A held-out validation set, written before the fixes, must
      also show no wrong advice: no case below 1. Required: decided in
      `feat-plan-locator` goal 10; the validation gate was added on
      `feat-locate-plan-diagnostics`.
  > **Branch:** feat/locate-plan-diagnostics
- [ ] Per-goal layout. `/new-branch` writes it inside the revision directory, and
      `/step` and `/hitl-step` read and write it. It adds a `**Layout**:` header and
      `scripts/check-plan-index.sh`, and keeps the legacy path.
- [ ] `Grep` and `Glob` can be missing from a session whose `allowed-tools` grants them.
      On Claude Code 2.1.296, both the interactive driver session and the headless trial
      runs lacked them, and the model fell back to shell `grep`, which `allowed-tools`
      doesn't cover, so the user gets a prompt. Measure when they are missing, then rewrite
      every step that relies on them, across the 11 command files that declare them:
      `/smart-merge` step 7, `/close-revision`'s pointer check, and in `/step` and
      `/hitl-step` the out-of-order lookup, Step 4's subgoal check, Step 5's re-Grep and
      the investigation paragraph. Found on `feat-locate-plan-diagnostics` goal 4.
- [ ] `/smart-merge` step 7 goes through `scripts/locate-plan.sh`, stamps the branch
      index and edits `_TODO.md`.
- [ ] `/master-plan`, `agents/plan-drafter.md` and `references/subdividing.md`, with a
      `--dry-run` that writes to a given path. `/close-revision` stamps, `/file-plans`
      becomes legacy-only and `/open-revision` becomes an alias. Fix the reopen guard:
      it must match `**Revision <label>** — closed`, which is what `/close-revision`
      writes, and today it never does.
- [ ] Rewrite the plan-convention sections of the plugin's `CLAUDE.md` and README. The
      "do not reintroduce the split" paragraph gains the §4.2 distinction.
- [ ] Release `0.10.0` and update the install. Confirm with `claude --debug` that 0.10.0
      is the driver and that the old-layout root plan still resolves under it.

## Closed revisions

Extracted by `/close-revision` once finished.

Revisions 02–04 are `workflow-claude`'s, from before it joined this marketplace. They
sit under `docs/plan/workflow-claude/` with the rest of its history — the master plan
that indexed them (revision 1 predates labels and lives in it) and two standalone
branch plans — and their PR numbers refer to the archived
`PanosMavromatis/workflow-claude`, not this repository.

- **Revision 02-mcp-github-access** — closed. See `docs/plan/workflow-claude/02-mcp-github-access/_DO.md`.
- **Revision 03-subgoal-plan-management** — plan layout at scale — closed. See `docs/plan/workflow-claude/03-subgoal-plan-management/_DO.md`.
- **Revision 04-revision-lifecycle** — closed. See `docs/plan/workflow-claude/04-revision-lifecycle/_DO.md`.
- **Revision 05-subagent-refactor-R0** — closed. See `docs/plan/05-subagent-refactor-R0/_TODO.md`.
