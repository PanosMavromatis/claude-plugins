# 02 — Warn on a goal file with no subgoals

**Goal**: [~]
> **Q:** Which model's goal files get the warning: the TODO model only, since R1's spec makes a DO goal file with no tasks the task itself (A), or both models (B)?
> **A:** A.

- [x] `locate-plan.sh` warns when the selected goal file, `goal-file:`, holds no subgoal, naming the file
  > **Note:** W12 follows W11 in `resolved()`: when the goal file holds no item line, at any indent and outside fences, and the model is TODO, it warns `<goal file> has no subgoals, so goal NN has no acceptance criteria: propose them before work starts`. The DO model is left alone, as decided.
- [x] `dev/locate-plan/` has a case for it, and a mutant it kills
  > **Note:** `w12` selects a TODO goal file holding only a fenced example and must warn, with `subgoals: —`; `w12b` is the same goal file in the DO model and must not. Mutants `r01` (no W12) and `r02` (W12 in the DO model) are each killed by one of them, and `m02`, which stops skipping fences, is now killed by `w12` first. 85 cases pass; 28 of 29 mutants are caught in 3 min 46 s, `n05` equivalent as before. No existing case selected a stub goal file, so none started to warn.
- [x] The warning is recorded in `locate-plan-spec.md`'s place, as goal 01 decided
  > **Note:** `locate-plan-spec.md`, in closed R1's `feat-plan-locator`, gains W12 in its warnings table and a sentence in its per-goal reading rule, both marked as added by this branch.
- [ ] Every suite of a script that sources `lib/plan-rules.sh` still passes, mutants included
