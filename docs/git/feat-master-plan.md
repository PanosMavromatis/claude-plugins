# feat/master-plan

**Created**: 2026-10-10
**Base**: main at 808c9e4
**Status**: active

## Purpose

Revisions are opened by hand today. `/open-revision` inserts a section whose preamble
and subgoals are typed in, and nothing turns a design document into the ordered,
branch-sized subgoals `/new-branch` and `/hitl-step` then execute. This branch adds
`/master-plan`, which drafts a revision master plan from an informal spec through a new
`plan-drafter` agent (so the spec stays out of the main context), following the
subdivision rules in `references/subdividing.md`, and has a `--dry-run` form that writes to
a given path; R2 step 0 runs it on the agreed plan. It also moves the rest of the
revision lifecycle onto the per-goal layout: `/close-revision` becomes a stamp, its legacy
path takes over filing so `/file-plans` is removed, and `/open-revision` becomes an alias. And it fixes the
reopen guard, which never matches the closed-index line `/close-revision` writes.

## Scope

- Measure what exists: `open-revision.sh`, `close-revision.sh`, `file-plans.sh` and their
  commands, in the legacy and revisions layouts. Reproduce the reopen-guard miss.
- Fix the reopen guard so it matches `**Revision <label>** — closed`, with a test.
- `references/subdividing.md` and `agents/plan-drafter.md`, written with plugin-dev's
  `agent-development` and checked by `plugin-validator`.
- `/master-plan <label> [spec] [--dry-run <path>]`; `/open-revision` becomes its alias.
- `/close-revision` stamps `_TODO.md` and flips the index line, keeping the legacy path,
  since R1 itself is still in the old form. The legacy close files the revision's merged
  branch plans, so `/file-plans` is removed (goal 5, Q3).
- Verify end to end. The user runs it; I grade.

## Context

- Master plan `docs/plan/TODO.md`, revision `06-subagent-refactor-R1`, the subgoal at
  line 96.
- Agreed plan `tmp/subagent-refactor-plan.md`: §4.5 (`/master-plan`, subdivision
  principles, the version field), §4.2 (`/close-revision` as a stamp, `/file-plans`
  retired, `/open-revision` folded in; D-N2, D-N3), the agent table row for
  `plan-drafter`, and R1 step 6. R2 step 0 is the first real run.
- The reopen-guard bug was found in R0, on `chore/move-plan-history`.

## Notes
