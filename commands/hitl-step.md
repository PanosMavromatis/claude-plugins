---
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git add:*), Bash(ls:*), Read, Write, Edit, Glob, Grep
description: Execute the next top-level goal from TODO.md with human-in-the-loop Q&A, logged inline.
argument-hint: "[count]"
---

# HITL Step

Execute pending top-level goals from the project's `TODO.md` with a human-in-the-loop protocol: every decision is surfaced to the user, and every Q&A is logged **inline under the goal**, so the reasoning survives compaction, `/clear`, or a fresh session.

**`$ARGUMENTS`** is the number of top-level goals to complete. If empty or missing, default to **1**. Call this value **N**. The default is 1 because each iteration typically involves Q&A — batching defeats the interactive purpose.

Loop through Steps 2–4 exactly **N** times, then hard-stop. Do **not** continue beyond N goals even if unchecked items remain.

## Status markers

Top-level goals and subgoals use these markers. `TODO.md` may include a legend at the top for readability, but this skill defines the canonical meanings:

| Marker | Meaning                                                        |
|--------|----------------------------------------------------------------|
| `[ ]`  | Not started                                                    |
| `[~]`  | In progress — work has begun but the goal is not yet complete  |
| `[x]`  | Complete                                                       |
| `[!]`  | Blocked — cannot proceed without an external change            |
| `[-]`  | Deferred / descoped — intentionally not doing (now, or at all) |

All five markers apply to both top-level goals and subgoals. Parent-state rules are defined in Step 4.

## Step 1: Read TODO.md

Read `TODO.md` from the project root. If it does not exist, inform the user and stop.

The file has a three-tier structure:

```
## Section header        ← not a checkbox; just groups goals
- [ ] Top-level goal     ← the unit of work per iteration
  - [ ] Subgoal          ← acceptance criterion for the parent goal
  - [ ] Subgoal
```

## Step 2: Find the Next Top-level Goal

Scan top-to-bottom and select the **first top-level goal whose marker is `[ ]` or `[~]`** — a line beginning with `- [ ] ` or `- [~] ` at indent 0 (no leading spaces). `[~]` takes priority: a goal already in progress is where we left off, and should be resumed before starting a new one. Ignore indented subgoals at this stage; they're acceptance criteria, not separate units.

- Note the goal's line number and text, plus the line numbers of its subgoals (indented lines with any `- [ ]` / `- [~]` / `- [!]` marker that follow it, before the next top-level goal or section header).
- If the user named a specific goal out of order in their invocation, pick that one instead.
- If every top-level goal is `[x]` or `[-]`, inform the user that all reachable work is complete and stop. If any top-level goal is `[!]` (blocked), list those separately so the user knows what's waiting on them.

## Step 3: Execute the Goal

**At the start of execution**, flip the selected goal's marker from `[ ]` → `[~]` (leave it alone if already `[~]`) and save `TODO.md`. This makes mid-work state visible across sessions — if the work is interrupted, the next `/hitl-step` resumes here. Flip subgoals to `[~]` as you actively work on each one (optional for fast-finishing goals, but recommended for any subgoal spanning more than one conversational turn).

Work through the goal and its subgoals. **Every write operation and every external command requires user confirmation first.**

### 3a. Research

Do any read-only investigation needed (Read, Grep, Glob, Bash for git queries, WebFetch/context7 for library docs). Keep this phase brief — the point is to understand the goal well enough to proceed, not to pre-solve it.

### 3b. Decisions → Q&A with inline logging

If the goal requires the user to make a decision (pick X vs Y, confirm a constraint, supply a value):

1. Ask the question(s) clearly. One question at a time when possible.
2. **Wait for the user's response.**
3. **Immediately append** the Q&A under the parent goal using this exact format — `>`-prefixed lines indented with **2 spaces** to nest under the goal:

```
- [ ] The original top-level goal
  > **Q:** Your question here?
  > **A:** The user's answer here.
```

   Multiple rounds concatenate in order:

```
- [ ] The original top-level goal
  > **Q:** First question?
  > **A:** First answer.
  > **Q:** Second question?
  > **A:** Second answer.
```

4. Continue executing with the information gathered.

### 3c. Writes → propose, confirm, execute

If the goal requires creating or modifying files (Dockerfile, script, config):

1. Show the proposed content or diff.
2. Ask for explicit confirmation before writing.
3. On approval, write the file.

### 3d. External commands → the user runs them

For commands that affect systems outside the local repo (`docker build`, `gcloud`, registry pushes, Vertex AI job submission), **do not run them**. Show the exact command and let the user run it themselves (they can use the `!` prefix in the prompt to surface output into the conversation). Record the outcome inline under the goal as a `> **Ran:**` or `> **Result:**` note if it's worth preserving.

### 3e. Commit checkpoint (after each subgoal)

After a subgoal is flipped to `[x]` — a real completion, not `[~]`, `[!]`, or `[-]` — **pause before starting the next subgoal** and ask the user whether they want to commit the work so far:

> Subgoal "<subgoal text>" is complete. Would you like to commit now (`git commit` or `/smart-commit`) before I continue, or keep going?

Wait for the user's response. **Do not run the commit yourself** — the user runs their preferred commit command (they can use the `!` prefix to surface output, or invoke `/smart-commit` themselves). If they say continue, move to the next subgoal. Optionally record the decision under the parent goal as `> **Commit:** committed here` or `> **Commit:** deferred` if it's worth preserving across sessions.

This pause is non-negotiable: every `[x]` subgoal gets one. The point is to give the user a clean checkpoint to capture before more diff piles up.

### 3f. Escape hatches (any time during Step 3)

- **Block a subgoal**: if progress requires an external change you can't make (missing credentials, quota approval, upstream bugfix, unavailable hardware), mark the subgoal `[!]` and append `> **Blocked:** reason` under it. Do not flip the parent to `[x]` while any subgoal is `[!]` — see Step 4 for the parent-state rules.
- **Defer or descope a subgoal**: if the subgoal is intentionally being skipped (optional work, out of scope, replaced by a different approach), mark it `[-]` and append `> **Deferred:** reason` or `> **Descoped:** reason` under it. The parent can still complete as `[x]` — `[-]` subgoals count as "resolved" for parent-state purposes.
- **Split a goal**: if a top-level goal turns out to contain two independent decisions, rewrite it in place into two separate `- [ ]` lines in `TODO.md` before continuing.
- **Descope a whole goal**: if a top-level goal becomes irrelevant, flip it to `[-]` with a `> **Descoped:** reason` note under it. This is distinct from `[x]` — it records that the work wasn't done, but by design.

## Step 4: Mark Complete

Determine the parent goal's final state based on the states of its subgoals and the work actually done. This is the only place a goal can leave the `[~]` state.

**Parent-state rules:**

- **`[x]` — Complete**: every subgoal is `[x]` or `[-]`. At least one subgoal must be `[x]` (a goal with all subgoals `[-]` is itself `[-]`, not `[x]`).
- **`[!]` — Blocked**: at least one subgoal is `[!]` and the remaining work can't finish without it. Add a `> **Blocked:** reason` note under the parent if the blocking source isn't obvious from the subgoals.
- **`[~]` — Still in progress**: real progress was made (some subgoals flipped to `[x]`) but the goal isn't done yet. Leave the parent as `[~]` so the next `/hitl-step` resumes here. This is a legitimate Step 4 outcome — not every iteration has to finish a top-level goal.
- **`[-]` — Descoped**: the entire goal is being abandoned. Add a `> **Descoped:** reason` note under the parent.

**Applying the result:**

1. Update each subgoal's marker to reflect its current state (`[x]`, `[!]`, `[-]`, or `[~]` — never `[ ]` once work has touched it).
2. Flip the parent goal's marker per the rules above.
3. If the completed work isn't obvious from the subgoals alone, optionally add a brief `> **Done:**` note under the parent:

    ```
    - [x] The original top-level goal
      > **Done:** brief summary of what was accomplished.
    ```

4. Save `TODO.md`.
5. **Commit checkpoint (after the parent goal).** Once the parent goal's marker has been flipped — whether to `[x]`, `[!]`, `[-]`, or left at `[~]` with real progress made — pause and ask the user whether they want to commit before `/hitl-step` moves on:

   > Goal "<goal text>" is now `[<state>]`. Would you like to commit (`git commit` or `/smart-commit`) before I continue to the next goal?

   Wait for the user's response. **Do not run the commit yourself.** Only after they answer do you proceed to Step 5. This pause fires every iteration, including the last one before Step 6.

## Step 5: Loop or Stop

- Increment the counter only if the parent goal's final state in Step 4 was `[x]`, `[!]`, or `[-]`. If it was left as `[~]`, the iteration still counts (we did work), but the user will almost certainly want to stop here and debrief — in that case, still increment and proceed to Step 6.
- If the counter equals **N**, proceed to Step 6. **Do not ask the user if they want to continue.**
- Otherwise, go back to Step 2 (re-read `TODO.md` to pick up your latest edits) and execute the next top-level goal.
- If no top-level goals remain in `[ ]` or `[~]` state, proceed to Step 6.

## Step 6: Report

Tell the user:

- How many goals were processed out of N requested, and each goal's final state (`[x]`, `[!]`, `[-]`, or `[~]`) with a one-line summary.
- **Blocked items**: if any subgoal or goal landed in `[!]` this iteration, surface the blocking reason explicitly — the user needs to resolve it before the next run can close that goal.
- **Section completion check**: if the just-completed section has all top-level goals in `[x]` or `[-]` state (under the nearest `##` above), say so and suggest running `/smart-commit` with a proposed message (e.g., `feat(docker): <section topic>`). Sections with a `[!]` goal are **not** complete.
- What the next pending top-level goal is (if any) — prefer a `[~]` in-progress goal over a `[ ]` not-started one when naming it, so the user knows the next `/hitl-step` will resume rather than start fresh.
