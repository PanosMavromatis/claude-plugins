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

- 2026-10-14, goal 01: `scripts/memory-check.sh` classes plan files by how the commands read them, not as §4.8 lists them: `/hitl-step` and `/smart-merge` read a branch plan's index whole, so it is measured against the threshold like the goal files, while `_TODO.md` and the root plan are only reported. Each `branches:` line names its plan's layout. On R2 the largest file read whole is ≈1112 tokens; R1's `feat-plan-locator`, single-file, is ≈16588
- 2026-10-14, goal 02: `dev/memory-check/` runs 29 cases on seven fixture repositories, checking each measured report line for line against sizes it computes from the files' own bytes, and kills all 26 mutants. Two of them, a report with warnings that exits 1 and one that `touch`es a file, show that the "gates nothing" and "writes nothing" checks can fail. The suite's static check required the script's awk comparisons to be written with `<`
- 2026-10-14, goal 03: `dev/memory-check/calibrate.py` (run c1, 20 one-turn sessions on claude-opus-5-5) found 2.34 bytes a token as `Read` returns a plan file, so bytes / 4 was 42% low; the script now estimates bytes × 3 / 7, and its default threshold is 2000, about twice the median of R2's merged goal files, above every one and below every R1 plan. `feat-plan-locator`, quoted above as ≈ 16.6k, is ≈28.4k calibrated. `dev/measure-context.sh` still divides by 4
