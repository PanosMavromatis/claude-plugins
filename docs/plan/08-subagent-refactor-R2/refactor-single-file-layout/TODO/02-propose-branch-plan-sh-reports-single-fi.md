# 02 — propose-branch-plan.sh reports single-file

**Goal**: [x]
> **Done:** `propose-branch-plan.sh` proposes a single-file branch plan as `layout: single-file`, under a legacy root plan or none, matching what `locate-plan.sh` reports once the plan exists; two new mutants, one per arm.

- [x] `propose-branch-plan.sh` reports `layout: single-file` for a branch plan under a legacy root plan and under no root plan
  > **Note:** Both arms of the root plan's layout, `legacy` and `none`, now give `R_LAYOUT=single-file`; a revisions index still gives `per-goal`. `p01` (no root plan), `p02` and `p03` (a legacy root plan) report it.
- [x] The propose-branch-plan suite passes with both cases, and `--mutants` catches every mutant
  > **Note:** 33 of 33 cases pass; `--mutants` kills 25 of 25, none stale. `b24` (a legacy root plan says `legacy`) dies at `p02`, `b25` (no root plan) at `p01`; `b18`, whose context held the edited lines, was refreshed with its mutation unchanged and still dies at `p21`.
