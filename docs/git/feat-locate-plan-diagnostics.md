# feat/locate-plan-diagnostics

**Created**: 2026-10-09
**Base**: main at 804463f
**Status**: active

## Purpose

Make `scripts/locate-plan.sh` say what the repository already shows. Today its `fix:`
lines are correct but generic. In the goal-10 trial, the subagent wrappers scored higher
only by reading repository state the script could read itself. This branch puts that
reading into the script, adds an investigation that runs in the main session only when
the user asks, and moves the test suite that measures all of this out of a session
scratchpad into the repository.

## Scope

- Bring the goal-10 suite, fixtures and answer key into the repo. Name the fault wrappers
  neutrally.
- A held-out validation set, written and committed before any fix: a variant of each
  fixed problem, plus counter-cases where a rule could fire without its evidence.
- Sharper `fix:` lines on all twelve cases below 2. Among them: create rather than
  restore a file that was never committed; `git mv` a plan written under the other model;
  name the exact goal file; say a directory holds no plan; remove a header that no file
  justifies. The full list, case by case, is in the branch plan.
- `/step` and `/hitl-step` offer a read-only investigation on an `error` or a failed run,
  and only run it when the user asks.
- Re-grade against the goal-10 answer key. Acceptance is 40/40, and no validation case
  may score below 1.

## Context

- Master plan `docs/plan/TODO.md`, revision `06-subagent-refactor-R1`, subgoal 2.
- `feat-plan-locator`, goal 10 (the 246-session trial and its decision) and goal 12 (the
  `message:` check), PR #5.
- Spec: `docs/plan/feat-plan-locator/locate-plan-spec.md`.

## Notes
