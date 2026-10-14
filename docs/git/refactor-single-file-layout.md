# refactor/single-file-layout

**Created**: 2026-10-13
**Base**: main at 584856d
**Status**: active

## Purpose

R2 subgoal 3. `locate-plan.sh` and `propose-branch-plan.sh` report a single-file branch plan as `layout: legacy`, the word the root plan's own layout uses in `propose-revision.sh`, `close-revision.sh` and `propose-merge-record.sh`, so one word names two things. This branch renames the branch-plan value to `single-file`, beside `per-goal`, and updates every command that reads it; the root plan's `legacy` is unchanged.

## Scope

- `lib/plan-rules.sh`'s `LAYOUT_V`; `locate-plan.sh`, its suite under `dev/locate-plan/`, and `locate-plan-spec.md`; `check-plan-index.sh`, which branches on the value
- `propose-branch-plan.sh` (`:150–151`) and its suite under `dev/propose-branch-plan/`
- the commands that read the value: `smart-merge.md:83`, `new-branch.md:150`, and Step 1 of `/step` and `/hitl-step`, kept byte-identical
- every suite of a script that sources `lib/plan-rules.sh`

## Context

- R2 subgoal 3: `docs/plan/08-subagent-refactor-R2/_TODO.md:47`; R2's review chose `single-file` in both scripts
- `check_layout` defaulted `LAYOUT_V` to `legacy` and accepted a `**Layout**: legacy` header; `master_files` derives the root plan's `MLAYOUT` from it but tests only for `revisions`, so the root plan's `legacy` does not depend on how the default is spelled
- Single-file plans stay supported through 1.x (D9)
- Step 1 of `/step` and `/hitl-step` names `kind: legacy-master`, the root plan's kind, which is not this value

## Notes
