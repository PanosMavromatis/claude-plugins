# chore/rename-workflow-coding

**Created**: 2026-10-11
**Base**: main at 01863f0
**Status**: active

## Purpose

Rename `workflow-claude` to `workflow-coding`, so the name no longer reads as one of
Anthropic's own plugins, and release `0.10.0` in the same PR. This is R1's last subgoal. The
marketplace is fetched from GitHub `main`, so a rename merged without the release would leave
`main` not listing the installed plugin. Renaming before R2 means R2's agents, R3's skills and
R4's contract file are each written once, under the new name (D-N8).

## Scope

- Move the Python bytecode ignore rule from `plugins/dp-compile/.gitignore` to the root, as its
  own commit
- Rename the plugin directory, `plugin.json`, `marketplace.json`, command and agent names, both
  READMEs and `CLAUDE.md`s, the hook messages, and `dev/` (`build.py`'s plugin path, `check.py`,
  the `run.sh` prompts); `version` `0.10.0`
- `dp-compile`: `"dependencies"`, its `/workflow-claude:*` references,
  `commands/references/workflow-claude.md` → `workflow-coding.md`; `version` `0.4.1`
- The one-step `/plugin install` line in the plugin README, and the expected-validate-warnings
  entry in the plugin `CLAUDE.md` (the name warning goes)
- The six script suites and a full e2e run pass; `.claude/settings.json` switches in the last
  commit before the merge

## Context

- Master-plan subgoal: revision 06-subagent-refactor-R1, `docs/plan/TODO.md`
- Agreed plan D-N8 and R1 step "Rename", `tmp/subagent-refactor-plan.md` (untracked):
  measured 2026-10-10 at 54 tracked paths and about 160 live references, 56 of them in
  `dp-compile`
- Records keep the old name: merged plans, `Done` lines, commits and PR bodies
- After the merge: `tmp/plugin-migration-runbook.md` (replace the install, `claude --debug`
  shows exactly one plugin, `workflow-coding` `0.10.0`, and the legacy root plan resolves)
- What follows: R1 closes via `/close-revision`, then revision `07-subagent-refactor-R1a`
  (`0.10.1`, `/session-handoff` and `/session-export-full`) opens in a new session

## Notes
