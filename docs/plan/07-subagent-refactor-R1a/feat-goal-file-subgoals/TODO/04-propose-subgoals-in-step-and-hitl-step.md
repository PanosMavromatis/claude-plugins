# 04 — Propose subgoals in /step and /hitl-step

**Goal**: [x]
> **Done:** `/hitl-step`'s Step 2 proposes subgoals for a branch plan's goal with none before work starts, never for a master plan's item; `/step` keeps a DO goal with no tasks as its own task, Step 1 stays in lockstep, and `per-goal-layout-spec.md` records the rule as an amendment.
> **Q:** `/step`'s Step 2 already makes a DO goal file with no tasks the task itself, as goals 02 and 03 decided, so should subgoal 2 be reworded to keep that and check the lockstep (A), or kept, `/step` proposing tasks too (B)?
> **A:** A.
> **Q:** Which goals does `/hitl-step` propose subgoals for: any branch plan's goal with `subgoals: —`, per-goal or legacy, but never a master plan's item (A), or per-goal plans only, where W12 fires (B)?
> **A:** A.

- [x] Step 2 of `commands/hitl-step.md`: a goal with no subgoals gets them proposed, confirmed and written to its goal file before work starts
  > **Note:** Step 2 gains a bullet: a branch plan's goal with `subgoals: —` gets its subgoals proposed before Step 3, drafted from the goal, its `>` lines and the plan's `**Subgoal**:` line, shown, and written on confirmation, at indent 0 in a goal file or indented in a one-file plan; a master plan's item never does, as answered above. It reads only `kind:` and `subgoals:`, which `locate-plan.sh` already reports, so no script changes.
- [x] Step 2 of `commands/step.md` keeps a DO goal with no tasks as its own task, as goals 02 and 03 decided, so it proposes none; and Step 1 stays byte-identical between the two: the plugin `CLAUDE.md`'s lockstep diff comes out empty
  > **Note:** Reworded from "does the same" by the first answer above: proposing tasks for a DO goal would undo the DO rule goals 02 and 03 kept.
  > **Note:** `step.md` is unchanged: its Step 2 already makes the goal the task when its goal file has none. The lockstep check of `CLAUDE.md:200`, Step 1 of both with `TODO.md`→`DO.md` and `/hitl-step`→`/step` substituted, comes out empty on the edited `hitl-step.md`, 65 lines each.
- [x] `per-goal-layout-spec.md`'s Step 2 under "`/step` and `/hitl-step` on a per-goal plan" says a TODO goal with no subgoals gets them proposed first, marked as an amendment
  > **Note:** The spec's Step 2 bullet for the step commands gains the rule, marked as added 2026-10-13 by this branch: in the TODO model a branch plan's goal with `subgoals: —` gets its subgoals proposed before Step 3, never a master plan's item, and the DO model proposes nothing.
