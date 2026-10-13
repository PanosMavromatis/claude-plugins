# 05 — Check a real /new-branch run's goal files

**Goal**: [~]

- [x] `dev/per-goal-e2e/check.py` fails a `/new-branch` run that leaves a goal file with no `- [ ]` subgoal
  > **Note:** `per_goal()` gains a check, TODO model only, that reads each goal file from the branch's first commit, as `/new-branch` wrote it, since the step session ticks the subgoals afterwards and goal 04's Step 2 could fill a stub in. Tried on a scratchpad clone of the fresh `r1` fixture, outside the repository: two stub goal files fail it, naming both; one `- [ ]` subgoal in each passes it, and no other check's result changes.
- [ ] A real run of e1, e3, e4 and e5 passes `check.py`: e1 for the subgoals `/new-branch` writes, e3 and e4 for its changed step 7 in the DO and legacy models, and e5 for `/hitl-step`'s new Step 2 on a stub goal file; the user runs it, since it costs money
  > **Note:** Widened from e1 alone after a side agent's review: every fixture's `CLAUDE.md` pre-approves each step, so no session stalls on a proposal, but e5's goal files are 0.10.0-style stubs (`build.py`'s `GOAL()`), so its `/hitl-step 1` now runs the new Step 2, and `/new-branch`'s step 7 changed for the e3 and e4 models too.
