# 03 — Draft each goal's subgoals in /new-branch

**Goal**: [x]
> **Done:** `/new-branch` shows `scope:` and drafts each goal file's subgoals from it, never a stub in the TODO model; the plugin's `CLAUDE.md` and `per-goal-layout-spec.md`'s goal-file template say so, the spec's change marked as an amendment.
> **Q:** Does `/new-branch`'s no-stub rule cover the DO model's goal files: the TODO model only, a DO goal file getting tasks when the scope splits it and otherwise standing alone as its own task, as W12 and R1's spec have it (A), or both models, every DO goal file getting at least one task (B)?
> **A:** A.

- [x] `commands/new-branch.md` step 7's per-goal template gives each goal file its subgoals, drafted from `scope:` and the scope discussion, and shows them with the rest of the plan before anything is written
  > **Note:** Step 4 now shows `scope:` and says it is not written; step 7's per-goal template puts the subgoals under `**Goal**:` at indent 0, drafted from `scope:`, its Acceptance shared out among the goals, and from step 1's discussion, and shown with the index and the backlink before the step's one confirmation. Nothing parses the command's text, so no suite covers it; goal 05's real e1 run does.
- [x] `commands/new-branch.md` states the rule: never write a goal file with no subgoals; a standalone plan's come from the scope discussion alone
  > **Note:** The rule is "never write a stub", with its reasons: no acceptance criteria for `/hitl-step` to check or tick, and W12. As answered above, it binds the TODO model; a DO goal file gets tasks only when the scope splits the goal, and is otherwise its own task. A standalone plan's subgoals come from step 1's discussion alone.
- [x] The plugin's `CLAUDE.md` says `/new-branch` writes each goal file with its subgoals
  > **Note:** `CLAUDE.md:36`, `/new-branch`'s entry, gains one sentence: goal files are written with their subgoals, drafted from `scope:`, never a stub in the TODO model, and W12 warns on one that is. The `protect-agent-docs` hook lets the edit through, since this repository has no `docs/agents/`: the plugin's `CLAUDE.md` holds its own content, not an `@import` dispatcher.
- [x] `per-goal-layout-spec.md`'s goal-file template under "What is written" shows the subgoals, marked as an amendment, as goal 01 decided
  > **Note:** The spec's goal-file template gains a subgoal line, and a rule, **Its subgoals**, marked as added 2026-10-13 by this branch, says when there must be one: always in the TODO model, and in the DO model only when the scope splits the goal.
