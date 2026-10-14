# 01 — locate-plan.sh reports single-file

**Goal**: [x]
> **Q:** Where should `legacy` become `single-file`: in the library, so `LAYOUT_V` names a file's own layout and `MLAYOUT` the root plan's (A), or at `locate-plan.sh`'s report only (B)?
> **A:** A: in the library; `check-plan-index.sh:128`, which branches on the value, follows.
> **Q:** Which `**Layout**:` header values does a plan accept: `legacy` and `single-file` (A), `legacy` only (B), or `single-file` only (C)?
> **A:** A: both, each meaning the default, so no plan written today changes meaning.
> **Done:** `LAYOUT_V`, a file's own layout, now defaults to `single-file`, and a `legacy` or `single-file` header is accepted; `locate-plan.sh` reports it for every single-file plan, and `check-plan-index.sh` follows. The suite gained `x18` and `x19`, pins the layout of `x06` and `c07`, and has three new mutants; the spec names the value.

- [x] `locate-plan.sh` reports `layout: single-file` for a single-file branch plan, a revision's `_TODO.md` and a legacy root plan, and `per-goal` as before; the root plan's `legacy`, as other scripts read it, is unchanged
  > **Note:** `check_layout` defaults `LAYOUT_V` to `single-file`, and a `legacy` or `single-file` header keeps it; `MLAYOUT`, which tests only for `revisions`, still says `legacy` for the root plan. `x03` (a branch plan), `x06` (a legacy root plan) and `c07` (a revision's `_TODO.md`) report `single-file`, and the per-goal cases are unchanged. `check-plan-index.sh:128` follows the rename, and its 39 cases pass.
- [x] The locate-plan suite passes with a case for each, and `--mutants` catches every mutant
  > **Note:** 87 of 87 cases pass, on a rebuilt `fx-diag`: the suite builds it only when the directory is missing, so `x18` and `x19` needed `/tmp/lp-suite/fx-diag` removed first. `--mutants`: 31 of 32 killed, `n05` equivalent as before, none stale. `s01` (default back to `legacy`) dies at `c07`, `s02` (`single-file` header refused) at `x19`, `s03` (`legacy` header refused) at `x18`. `m02` and check-plan-index's `c07` and `c22` were refreshed for the edited lines, their mutations unchanged; check-plan-index's 24 mutants are all killed.
- [x] `locate-plan-spec.md` names the value `single-file`
  > **Note:** The report's shape (line 49) and the `layout:` rule (lines 130–134), which now names all three plan kinds, accepts both headers, and records that the value was `legacy` until R2.
