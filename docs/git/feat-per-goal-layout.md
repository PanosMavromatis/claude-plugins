# feat/per-goal-layout

**Created**: 2026-10-10
**Base**: main at 5404aba
**Status**: active

## Purpose

Build the per-goal plan layout's writers. `scripts/locate-plan.sh` already reads a
`**Layout**: revisions` root index and a `**Layout**: per-goal` branch index with goal
files under `TODO/` (or `DO/`), but nothing writes them, and `/step` and `/hitl-step`
stop on a per-goal plan. This branch makes `/new-branch` create the layout inside the open
revision's directory, makes the step commands work on one goal file at a time, and adds
`scripts/check-plan-index.sh` to report drift between an index and its goal files. The
legacy single-file path stays. This revision builds the layout but does not adopt it: this
repository's own plans stay legacy until R2 step 0.

## Scope

- A write-side spec: when `/new-branch` goes per-goal and when it stays flat, the goal-file
  stubs and numbering, the edit order (goal file, then index), and Steps 2–6 on a
  per-goal plan.
- `scripts/lib/plan-rules.sh`: the rules more than one script applies, defined once and
  sourced by `locate-plan.sh` and the two new scripts.
- `scripts/check-plan-index.sh`, read-only, with a test suite under `dev/`.
- `scripts/propose-branch-plan.sh`, read-only: where a new plan goes, its goal-file names
  and the backlink line. `/new-branch` writes exactly what it proposes: the index, the
  goal-file stubs and the backlink in `_TODO.md`.
- `/step` and `/hitl-step` read and write goal files; the lockstep `sed` diff stays empty.
- An end-to-end check through the real commands, per-goal and legacy. The user runs the
  headless sessions.

## Context

- Master plan `docs/plan/TODO.md`, revision `06-subagent-refactor-R1`, subgoal 3.
- The agreed plan's §4.2 (layout, root index, revision master plan, branch index, goal
  file, rules) and decisions D2 and D3, in `tmp/subagent-refactor-plan.md`.
- `locate-plan.sh`'s reader side: `docs/plan/feat-plan-locator/locate-plan-spec.md`; its
  suite: `dev/locate-plan/`.
- `feat-locate-plan-diagnostics` goal 4: `Grep` and `Glob` can be missing from a session,
  so new steps should not depend on them.

## Notes

- 2026-10-10: goal 1 wrote the write-side spec (`per-goal-layout-spec.md`, beside the
  plan). The root plan decides the layout, and a proposing script decides placement,
  which added the shared rules file and `propose-branch-plan.sh` to the scope.
- 2026-10-10: goal 2 moved the shared rules into `scripts/lib/plan-rules.sh`, verbatim.
  The suite now has 83 cases (`e10c` is new, for the slug cap), and the mutants were
  re-anchored to the two-file tree. A new `q11-slug-cap` mutant survived until `e10c`
  existed. The final count is 27 mutants: 26 killed, n05 equivalent.
- 2026-10-10: goal 3 added `scripts/check-plan-index.sh`, a read-only drift report (D1–D8)
  on the shared library. Its suite, `dev/check-plan-index/`, has 33 cases and 18
  mutants. Vetting found that findings interact: problems must pair one-to-one with
  fixes, and E9, D4 and D6 must not give conflicting advice. Nothing calls it yet; Step
  6 does, from goal 5.
