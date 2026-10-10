# fix/disallowed-tool-steps

**Created**: 2026-10-10
**Base**: main at 5b150d2
**Status**: active

## Purpose

Some command steps rely on a tool that their command does not grant in practice. Since
2.1.117, native macOS and Linux builds of Claude Code have no `Grep` or `Glob` tools in
the main session, and `allowed-tools` cannot bring them back. Steps written around those
tools fail with "No such tool available", and the model improvises a substitute.
`/hitl-step`'s legacy Step 6 runs `awk`, which is not allow-listed at all, so it prompts
or is refused. `SlashCommand` no longer exists either. This branch measures which steps
are affected, then moves each one onto a tool its command does grant, mostly the
plugin's own scripts, so that no run stops for a missing tool or a prompt nobody
expected.

## Scope

- Measure when `Grep` and `Glob` are missing, and list every step across the 11 command
  files that relies on a tool its command does not allow.
- `check-plan-index.sh` reports a legacy plan's open items, so Step 6 runs one script for
  both layouts.
- Rewrite `/close-revision`'s pointer check. In `/step` and `/hitl-step`, rewrite the
  out-of-order lookup, Step 4's subgoal check, Step 5's re-Grep and the investigation
  paragraph. In `/hitl-step`, also rewrite Step 3a's research list.
- `/smart-merge` allows `git pull --prune`, writes the `gh` fallback's body file with `Write`,
  and says in its Guidelines that its other unlisted writes are deliberate gates. No
  `git push` pattern can be allowed without also allowing `git push origin --delete`.
- `SlashCommand` becomes `Skill(workflow-claude:<name>)` in `/smart-commit`,
  `/agents-docs-update` and `/agents-docs-codex-init`.
- `/agents-docs-init`'s `CLAUDE.md` heredoc turned out to be documented as a deliberate gate
  already, so nothing changed there.
- `/new-branch` marks the master-plan subgoal it executes `[~]` (with a `TODO.md` master
  plan), and the e2e grader expects it. Raised by the user mid-branch.
- Verify: the three script suites pass. The user re-runs per-goal-e2e `e1`, `e3` and `e4`,
  and a headless `/smart-commit` to check its nested `Skill` call.
- In the setup commit, the master plan's R1 release item gains the
  `workflow-claude` → `workflow-coding` rename (D-N8).

## Context

- Master plan `docs/plan/TODO.md`, revision `06-subagent-refactor-R1`, subgoal 4.
- The `Grep`/`Glob` gap was found on `feat-locate-plan-diagnostics` goal 4, and the `awk`
  gap on `feat-per-goal-layout` goal 6, where it was the only failure in e2e `e4`.
- `Bash(awk:*)` is ruled out.

## Notes

- 2026-10-10: `/smart-merge` step 7 is measured here but rewritten by the next subgoal,
  through `scripts/locate-plan.sh`, so that it is written only once.
- 2026-10-10: verified. The e2e run `r3` passed 65 checks with 0 failing. A headless
  `/smart-commit` control on 0.9.0 had its nested `Skill` call denied, because the dead
  `SlashCommand(…)` grant matches nothing, so it silently skipped `/agents-docs-update`.
  With the new `Skill(…)` grant, the call ran.
