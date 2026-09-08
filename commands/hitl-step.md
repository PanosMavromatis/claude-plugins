---
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git add:*), Bash(ls:*), Read, Write, Edit, Glob, Grep
description: Execute the next top-level goal from a docs/plan TODO.md with human-in-the-loop Q&A, logged inline.
argument-hint: "[count] [plan-path]"
---

# HITL Step

Execute pending top-level goals from the project's `TODO.md` plan file with a human-in-the-loop protocol: every decision is surfaced to the user, and every Q&A is logged **inline under the goal**, so the reasoning survives compaction, `/clear`, or a fresh session.

**`$ARGUMENTS`** may contain up to two whitespace-separated tokens, in any order:

- a **bare integer** — the number of top-level goals to complete. Call this value **N**. If absent, default to **1**. The default is 1 because each iteration typically involves Q&A — batching defeats the interactive purpose.
- **anything else** — a path selecting the plan file (see Step 1). If absent, discover it.

Loop through Steps 2–4 exactly **N** times, then hard-stop. Do **not** continue beyond N goals even if unchecked items remain.

## Status markers

Top-level goals and subgoals use these markers. The plan file may include a legend at the top for readability, but this skill defines the canonical meanings:

| Marker | Meaning                                                        |
|--------|----------------------------------------------------------------|
| `[ ]`  | Not started                                                    |
| `[~]`  | In progress — work has begun but the goal is not yet complete  |
| `[x]`  | Complete                                                       |
| `[!]`  | Blocked — cannot proceed without an external change            |
| `[-]`  | Deferred / descoped — intentionally not doing (now, or at all) |

All five markers apply to both top-level goals and subgoals. Parent-state rules are defined in Step 4.

## Step 1: Locate and read the plan file

Plan files live under `docs/plan/`. There are two kinds:

- the **master plan**, `docs/plan/TODO.md`, whose items are subgoals that each spawn a branch;
- a **branch plan**, `TODO.md` inside a directory named for the branch with `/` flattened to `-`: branch `feat/user-auth` → a directory `feat-user-auth/`. That name is the plan's **identity**; its location is not. `/new-branch` creates the directory directly under `docs/plan/`, but it may be moved anywhere beneath `docs/plan/` afterwards — grouped into a milestone or component directory, say — and resolution still finds it. Reorganise with `git mv`; no command needs updating.

Resolve in the order below and **stop at the first rung that yields a file**. Call the result **the plan file**, and state which one you resolved to before doing any work.

1. **Path argument.** If `$ARGUMENTS` contained a path, interpret it as a repo-relative path, a path relative to `docs/plan/`, or a directory under `docs/plan/` — whichever resolves. If it names a directory, look for `TODO.md` inside it. If it resolves to nothing, say so and **stop**; do not fall through to the later rungs, since a typo would silently run a different plan.
2. **Branch plan.** Run `git branch --show-current` and flatten `/` to `-`; call the result the **plan name**. Find the plan by that name *wherever* it sits under `docs/plan/`, rather than at a fixed path. Check `docs/plan/<plan-name>/TODO.md` first — the flat location `/new-branch` creates, and the answer in nearly every case — and only if that misses, glob `docs/plan/**/<plan-name>/TODO.md`. Trying the exact path first is about cost, not correctness: in a large repo it avoids a recursive walk to find something that is almost always sitting in the obvious place. Branch names are unique per repo, so the name alone is a sufficient key and at most one match is expected.
   - **Exactly one match** — use it. On a branch created by `/new-branch`, this is normally the answer.
   - **Several matches** — a plan directory was copied rather than moved, so one of them is stale. List the full paths and ask which to use. Never guess, and never read from more than one.
   - **No match** — fall through to rung 3.

   If the resolved plan carries a `merged` status stamp (see below), use it anyway but say so, since that usually means the branch was reopened after merging.
3. **Master plan.** If `docs/plan/TODO.md` exists, use it — on `main`, this is normally the answer. **Read it differently from a branch plan.** A branch plan covers one branch and stays small, so read it whole. The master plan accumulates every subgoal of every revision, each with its `> **Done:**` annotation, and grows without bound — at 250 subgoals it is around 197 KB, and past roughly 500 it exceeds the default 2000-line read limit and a plain read silently truncates. When the master plan is the resolved file, locate what you need with `Grep` and read a bounded window around it (see Step 2) rather than loading the file. Note that you did so, and say how large the file is.
4. **Glob and ask.** Glob `docs/plan/**/TODO.md` and partition the matches by status stamp:
   - Exactly one **active** match → use it.
   - Several active matches → list them and ask which to use. Wait for the answer; do not guess. If any merged plans were excluded, add a line `(N merged plans not shown — name one explicitly to use it)`.
   - No active matches but some merged ones → list the merged plans and ask whether to use one. Never auto-select a merged plan.
   - No matches at all → go to rung 5.
5. **Legacy root file.** If `TODO.md` exists at the project root, use it, but tell the user that plans now live under `docs/plan/` and suggest moving it (`git mv TODO.md docs/plan/TODO.md`).

If no rung yields a file, inform the user and stop.

### Status stamp

A plan file may carry a status line near the top:

```
**Status**: active
**Status**: merged — PR #123 — 2026-08-29
```

`/new-branch` writes `active` at creation; `/smart-merge` rewrites it to `merged` when the branch lands. For rung 4, a plan counts as **merged** only if it has a `**Status**:` line whose value begins with `merged`. Everything else — `active`, any other value, or no status line at all — counts as **active**. Failing toward "active" is deliberate: plans merged outside `/smart-merge` never get stamped, and showing a stale option costs a second while hiding a live one costs much more.

The file has a three-tier structure:

```
## Section header        ← not a checkbox; just groups goals
- [ ] Top-level goal     ← the unit of work per iteration
  > **Note:** ...        ← a finding; never a checkbox (see 3b-bis)
  - [ ] Subgoal          ← acceptance criterion for the parent goal
  - [ ] Subgoal
```

## Step 2: Find the Next Top-level Goal

For a branch plan, which is small, read it whole and scan top-to-bottom. For the **master plan**, locate instead of scanning: `Grep` for `^- \[[ ~]\]` with line numbers on, then `Read` a window around the first hit rather than loading the file. This costs a fixed ~200 tokens where a whole-file read costs ~55k at 250 subgoals, and past ~500 subgoals a plain read truncates — which would hide later goals and make "all work complete" a false report rather than a finding. When in doubt about completion on a large file, confirm by `Grep`, which sees all of it.

Select the **first top-level goal whose marker is `[ ]` or `[~]`** — a line beginning with `- [ ] ` or `- [~] ` at indent 0 (no leading spaces). `[~]` takes priority: a goal already in progress is where we left off, and should be resumed before starting a new one. Ignore indented subgoals at this stage; they're acceptance criteria, not separate units.

- Note the goal's line number and text, plus the line numbers of its subgoals (indented lines with any `- [ ]` / `- [~]` / `- [!]` marker that follow it, before the next top-level goal or section header).
- If the user named a specific goal out of order in their invocation, pick that one instead.
- If every top-level goal is `[x]` or `[-]`, inform the user that all reachable work is complete and stop. If any top-level goal is `[!]` (blocked), list those separately so the user knows what's waiting on them.

## Step 3: Execute the Goal

**At the start of execution**, flip the selected goal's marker from `[ ]` → `[~]` (leave it alone if already `[~]`) and save the plan file. This makes mid-work state visible across sessions — if the work is interrupted, the next `/hitl-step` resumes here. Flip subgoals to `[~]` as you actively work on each one (optional for fast-finishing goals, but recommended for any subgoal spanning more than one conversational turn).

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

### 3b-bis. Findings → `> **Note:**`, never a checkbox

Work turns up things that are worth keeping and are **not tasks**: a measurement, a
surprise, a claim in the codebase that turned out to be false, a reason something was left
alone. These get a `> **Note:**` blockquote under the relevant goal or subgoal, in the same
2-space-indented form as the Q&A above:

```
- [x] The goal
  > **Note:** what was observed, and why it will matter to whoever reads this next.
```

**Do not write a finding as a `- [ ]` line.** A checkbox is a promise that something will
be done, so a note wearing one is read as outstanding work by anyone scanning the file —
and, because a plan is usually surveyed with a top-level `grep -c '^- \[ \]'`, an indented
one is *simultaneously* invisible to the count and alarming to a reader. If a note really
does imply future work, it is not a note: give it `[-]` and name the goal that picks it up,
per 3f.

The distinction to apply: **`> **Note:**` records something observed; `[-]` records
something postponed.** "The validator warns about this file and that is expected" is a
note. "This file's rewrite is deferred to goal C1" is `[-]`.

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
- **Split a goal**: if a top-level goal turns out to contain two independent decisions, rewrite it in place into two separate `- [ ]` lines in the plan file before continuing.
- **Descope a whole goal**: if a top-level goal becomes irrelevant, flip it to `[-]` with a `> **Descoped:** reason` note under it. This is distinct from `[x]` — it records that the work wasn't done, but by design.

## Step 4: Mark Complete

Determine the parent goal's final state based on the states of its subgoals and the work actually done. This is the only place a goal can leave the `[~]` state.

**Parent-state rules:**

- **`[x]` — Complete**: every subgoal is `[x]` or `[-]`. At least one subgoal must be `[x]` (a goal with all subgoals `[-]` is itself `[-]`, not `[x]`).
- **`[!]` — Blocked**: at least one subgoal is `[!]` and the remaining work can't finish without it. Add a `> **Blocked:** reason` note under the parent if the blocking source isn't obvious from the subgoals.
- **`[~]` — Still in progress**: real progress was made (some subgoals flipped to `[x]`) but the goal isn't done yet. Leave the parent as `[~]` so the next `/hitl-step` resumes here. This is a legitimate Step 4 outcome — not every iteration has to finish a top-level goal.
- **`[-]` — Descoped**: the entire goal is being abandoned. Add a `> **Descoped:** reason` note under the parent.

**Check the subgoals before flipping the parent — do not do it from memory.** A goal that
took several turns has scrolled its own acceptance criteria out of view, and the `[x]` rule
above is precisely a claim about lines you are no longer looking at. Re-read them, or
`Grep` the goal's line range for `- \[[ ~!]\]`, and resolve every hit before step 2 below.
A hit that turns out not to be a task at all is a finding written as a checkbox: convert it
to `> **Note:**` per 3b-bis rather than ticking it, since ticking implies work that was
never done.

**Applying the result:**

1. Update each subgoal's marker to reflect its current state (`[x]`, `[!]`, `[-]`, or `[~]` — never `[ ]` once work has touched it).
2. Flip the parent goal's marker per the rules above.
3. If the completed work isn't obvious from the subgoals alone, optionally add a brief `> **Done:**` note under the parent:

    ```
    - [x] The original top-level goal
      > **Done:** brief summary of what was accomplished.
    ```

4. Save the plan file. Use `Edit` — the marker change and the appended `> **Q:** / > **A:**` lines are localized, and rewriting the whole file with `Write` costs as much as reading it whole, which is the cost Step 2 exists to avoid on a large master plan.
5. **Commit checkpoint (after the parent goal).** Once the parent goal's marker has been flipped — whether to `[x]`, `[!]`, `[-]`, or left at `[~]` with real progress made — pause and ask the user whether they want to commit before `/hitl-step` moves on:

   > Goal "<goal text>" is now `[<state>]`. Would you like to commit (`git commit` or `/smart-commit`) before I continue to the next goal?

   Wait for the user's response. **Do not run the commit yourself.** Only after they answer do you proceed to Step 5. This pause fires every iteration, including the last one before Step 6.

## Step 5: Loop or Stop

- Increment the counter only if the parent goal's final state in Step 4 was `[x]`, `[!]`, or `[-]`. If it was left as `[~]`, the iteration still counts (we did work), but the user will almost certainly want to stop here and debrief — in that case, still increment and proceed to Step 6.
- If the counter equals **N**, proceed to Step 6. **Do not ask the user if they want to continue.**
- Otherwise, go back to Step 2 and execute the next top-level goal. Pick up your latest edits the same way Step 2 found the first goal — re-`Grep` for the next `[ ]` / `[~]` marker rather than re-reading the file. On a large master plan a whole-file re-read every iteration multiplies the cost by N, which is exactly the loop this command is built around.
- If no top-level goals remain in `[ ]` or `[~]` state, proceed to Step 6.

## Step 6: Report

Tell the user:

- How many goals were processed out of N requested, and each goal's final state (`[x]`, `[!]`, `[-]`, or `[~]`) with a one-line summary.
- **Blocked items**: if any subgoal or goal landed in `[!]` this iteration, surface the blocking reason explicitly — the user needs to resolve it before the next run can close that goal.
- **Section completion check**: if the just-completed section has all top-level goals in `[x]` or `[-]` state (under the nearest `##` above), say so and suggest running `/smart-commit` with a proposed message (e.g., `feat(docker): <section topic>`). Sections with a `[!]` goal are **not** complete.

  **Verify this at every indent, not just at the top level.** Step 4 should already have
  made it impossible for a `[x]` parent to hide an open subgoal, but this is the line the
  user acts on, so it is worth re-deriving rather than inheriting:

  ```bash
  awk '/^## /{s=$0} /^[[:space:]]*- \[[ ~!]\]/{print s" | "$0}' <plan file>
  ```

  Report "section complete" only if that prints nothing for the section. A completion claim
  is the one report a reader will not re-check.
- What the next pending top-level goal is (if any) — prefer a `[~]` in-progress goal over a `[ ]` not-started one when naming it, so the user knows the next `/hitl-step` will resume rather than start fresh.
