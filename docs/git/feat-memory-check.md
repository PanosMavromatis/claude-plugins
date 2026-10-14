# feat/memory-check

**Created**: 2026-10-14
**Base**: main at d5fc86a
**Status**: active

## Purpose

R2 subgoal 6. Commands read a branch plan's index and goal files whole, and nothing measures how large they grow; a master plan, read only in windows, already passes the size where a whole-file read truncates. This branch adds `/memory-check`, per §4.8 of the design: a read-only script that reports each plan file's size in bytes, words, lines and approximate tokens, with totals per branch and for the revision, and warns on goal files over a threshold; a suite; and a thin command.

## Scope

- `plugins/workflow-coding/scripts/memory-check.sh`, sourcing `scripts/lib/plan-rules.sh`
- `dev/memory-check/`, the suite
- `plugins/workflow-coding/commands/memory-check.md`, diagnostic only
- the bytes / 4 ratio, calibrated once against a real token count, and the threshold's default, from the first R2 goal files

## Context

- R2 subgoal 6: `docs/plan/08-subagent-refactor-R2/_TODO.md:59`
- Design: §4.8 of `tmp/subagent-refactor-plan.md`
- Builds on subgoal 3 (PR #25), which named a branch's one-file plan layout `single-file`; the root plan's own layout stays `legacy`
- R1's legacy plans give the first baseline: the largest, `feat-plan-locator`, ≈ 16.6k tokens
- Subgoal 14, the 0.11.0 release, runs `/memory-check` on R2's own revision

## Notes
