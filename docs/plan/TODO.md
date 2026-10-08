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

- [~] Add `version` fields to both `plugin.json`s (`workflow-claude` `0.9.0`,
  `dp-compile` `0.4.0`). Commit `.claude/settings.json` declaring the
  `mavromatis-ai-labs` marketplace and enabling `workflow-claude` only. Push,
  update the install, and confirm with `claude --debug` that exactly one
  `workflow-claude` loads, at `0.9.0`.
  > **Note:** both manifests did carry versions before this repository existed —
  > `workflow-claude` `0.2.0` (4cca98a) and `dp-compile` `0.3.0` (233a311) — and the
  > "Normalize … for marketplace layout" commits (eb3b966, d71706d) removed them
  > without a stated reason. Without a `version`, the install is keyed on the commit
  > SHA, so every push to `main` is an update; that is what this subgoal ends.
  > **Q:** `dp-compile` last shipped as `0.3.0`, so the planned `0.2.0` would go
  > backwards. What version should it get now?
  > **A:** `0.4.0` — the next minor after the last release, since the import changed
  > its files after `0.3.0`. Its R4 release moves from `0.3.0` to `0.5.0`.
  > **Q:** `workflow-claude` last shipped as `0.2.0`. Keep the jump to `0.9.0`, which
  > leaves room for `0.10.0` and `0.11.0` before `1.0.0`?
  > **A:** Yes, `0.9.0` as planned.
  > **Done (on the branch):** both `version` fields added; the stale `0.2.0` in
  > `dp-compile`'s `CLAUDE.md` example manifest updated; `.claude/settings.json`
  > now declares the marketplace (`extraKnownMarketplaces`) as well as enabling
  > `workflow-claude`. `claude plugin validate` passes for both plugins.
  > **Note:** the validator's three warnings predate this change: the name
  > `workflow-claude` "reads as one of Anthropic's own"; a root `CLAUDE.md` is not
  > loaded as plugin context (the `AGENTS.md` work in R3 answers this one); and the
  > README lacks a one-line `/plugin install … --marketplace` form.
  > **Q:** the root `README.md` records a 2026-09-09 decision to omit `version` so
  > every push reaches consumers — the reason the import dropped the fields. Keep
  > them and rewrite that paragraph, or back them out?
  > **A:** Keep them; the README now records the reversal and its reason (the
  > installed driver must move only on a release), and the freeze risk is answered
  > by a bump at the end of every revision that changes a plugin.
  > **Remaining:** the install follows `main`, so pushing, updating the install and
  > the `claude --debug` check wait until this branch is merged.
- [ ] Move `plugins/workflow-claude/docs/plan/` to `docs/plan/workflow-claude/`
  with `git mv`, link it from this file, and stamp the moved master plan closed.
  `dp-compile` has no plan tree to move.
- [ ] Add `dev/measure-context.sh`, which measures what a session and each command
  load, and record its baseline here as the figure later revisions are judged
  against.

## Closed revisions

Extracted by `/close-revision` once finished.
