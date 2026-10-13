# 01 — Report the subgoal's scope from propose-branch-plan.sh

**Goal**: [ ]

- [ ] `propose-branch-plan.sh` reports `scope:`: the selected subgoal's continuation lines (`Scope: … Acceptance: …`), in the report's two-space continuation form, and `—` for a standalone plan
- [ ] `dev/propose-branch-plan/` has a case for each, a subgoal with its scope and a standalone plan, and a mutant each case kills
- [ ] The `scope:` key is recorded in the script's contract: `per-goal-layout-spec.md` sits in closed R1's `feat-per-goal-layout`, so decide where the new rule is written, and log the decision here
