# Master plan — claude-plugins

**Status**: active

The marketplace's master plan, covering both plugins. Each revision below is a
milestone whose subgoals each spawn a branch; `/close-revision` moves a finished
revision into `docs/plan/<label>/`.

## Subgoals — revision 05-subagent-refactor-R0

Opens the refactor of `workflow-claude` and `dp-compile` onto subagents. It was
prompted by context cost measured in a consumer repository: an agent-docs file of
about 31k tokens loaded into every session, and branch plans of 5–16k tokens read
whole on every `/hitl-step` iteration. The refactor moves reads into
context-isolated subagents, splits plans into one file per goal, replaces
`CLAUDE.md` with `AGENTS.md`, and is tried out on this repository first. R0 only
sets up that trial so it can run safely, and changes no plugin behaviour. Settled,
not to be reopened: the *driver* is the last released `workflow-claude`, installed
from the marketplace at project scope. The *subject* is the working tree. The two
are never loaded in one session, and edited code is exercised only in a separate
scratch session or under `claude plugin eval`. `dp-compile` is not enabled here,
because nothing in this repository is a DP kernel. R0 and R1 run on the current
plan layout, and a new layout is adopted only after the release that reads it is
installed.

- [ ] Add `version` fields to both `plugin.json`s (`workflow-claude` `0.9.0`,
  `dp-compile` `0.2.0`). Commit `.claude/settings.json` declaring the
  `mavromatis-ai-labs` marketplace and enabling `workflow-claude` only. Push,
  update the install, and confirm with `claude --debug` that exactly one
  `workflow-claude` loads, at `0.9.0`.
- [ ] Move `plugins/workflow-claude/docs/plan/` to `docs/plan/workflow-claude/`
  with `git mv`, link it from this file, and stamp the moved master plan closed.
  `dp-compile` has no plan tree to move.
- [ ] Add `dev/measure-context.sh`, which measures what a session and each command
  load, and record its baseline here as the figure later revisions are judged
  against.

## Closed revisions

Extracted by `/close-revision` once finished.
