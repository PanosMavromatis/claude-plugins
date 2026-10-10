# fix/disallowed-tool-steps

**Created**: 2026-10-10
**Base**: main at 5b150d2
**Status**: active

## Purpose

Some command steps rely on a tool that their command does not grant in practice. On
Claude Code 2.1.296, `Grep` and `Glob` were missing from both the interactive driver
session and the headless trial runs. Steps written around those tools fell back to shell
`grep`, which `allowed-tools` doesn't cover, so the user got a prompt. `/hitl-step`'s
legacy Step 6 runs `awk`, which is not allow-listed at all. This branch measures which
steps are affected, then moves each one onto a tool its command does grant, mostly the
plugin's own scripts, so that no run stops for a prompt nobody expected.

## Scope

- Measure when `Grep` and `Glob` are missing, and list every step across the 11 command
  files that relies on a tool its command does not allow.
- `check-plan-index.sh` reports a legacy plan's open items, so Step 6 runs one script for
  both layouts.
- Rewrite `/close-revision`'s pointer check. In `/step` and `/hitl-step`, rewrite the
  out-of-order lookup, Step 4's subgoal check, Step 5's re-Grep and the investigation
  paragraph.
- Verify: the three script suites pass, and the user re-runs per-goal-e2e `e4`.
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
