---
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git add:*), Bash(find:*), Bash(cat:*), Bash(ls:*), Read, Write, Glob, Grep
description: Execute the next N unchecked items in a docs/plan DO.md (default 1) and log all Q&A under each item.
argument-hint: "[count] [plan-path]"
---

# Step

You are executing pending tasks from the project's `DO.md` plan file.

**`$ARGUMENTS`** may contain up to two whitespace-separated tokens, in any order:

- a **bare integer** — the number of items to complete. Call this value **N**. If absent, default to **1**.
- **anything else** — a path selecting the plan file (see Step 1). If absent, discover it.

Loop through Steps 2–4 exactly **N** times, then hard-stop. Do **not** continue beyond N items even if unchecked items remain.

## Step 1: Locate and read the plan file

Plan files live under `docs/plan/`. There are two kinds:

- the **master plan**, `docs/plan/DO.md`, whose items are subgoals that each spawn a branch;
- a **branch plan**, `docs/plan/<flattened-branch>/DO.md`, covering the work of one branch. The directory name is the branch name with `/` flattened to `-`: branch `feat/user-auth` → `docs/plan/feat-user-auth/`.

Resolve in the order below and **stop at the first rung that yields a file**. Call the result **the plan file**, and state which one you resolved to before doing any work.

1. **Path argument.** If `$ARGUMENTS` contained a path, interpret it as a repo-relative path, a path relative to `docs/plan/`, or a directory under `docs/plan/` — whichever resolves. If it names a directory, look for `DO.md` inside it. If it resolves to nothing, say so and **stop**; do not fall through to the later rungs, since a typo would silently run a different plan.
2. **Branch plan.** Run `git branch --show-current`, flatten `/` to `-`, and check `docs/plan/<flattened>/DO.md`. If it exists, use it — on a branch created by `/new-branch`, this is normally the answer. If it carries a `merged` status stamp (see below), use it anyway but say so, since that usually means the branch was reopened after merging.
3. **Master plan.** If `docs/plan/DO.md` exists, use it — on `main`, this is normally the answer.
4. **Glob and ask.** Glob `docs/plan/**/DO.md` and partition the matches by status stamp:
   - Exactly one **active** match → use it.
   - Several active matches → list them and ask which to use. Wait for the answer; do not guess. If any merged plans were excluded, add a line `(N merged plans not shown — name one explicitly to use it)`.
   - No active matches but some merged ones → list the merged plans and ask whether to use one. Never auto-select a merged plan.
   - No matches at all → go to rung 5.
5. **Legacy root file.** If `DO.md` exists at the project root, use it, but tell the user that plans now live under `docs/plan/` and suggest moving it (`git mv DO.md docs/plan/DO.md`).

If no rung yields a file, inform the user and stop.

### Status stamp

A plan file may carry a status line near the top:

```
**Status**: active
**Status**: merged — PR #123 — 2026-08-29
```

`/new-branch` writes `active` at creation; `/smart-merge` rewrites it to `merged` when the branch lands. For rung 4, a plan counts as **merged** only if it has a `**Status**:` line whose value begins with `merged`. Everything else — `active`, any other value, or no status line at all — counts as **active**. Failing toward "active" is deliberate: plans merged outside `/smart-merge` never get stamped, and showing a stale option costs a second while hiding a live one costs much more.

The file uses standard Markdown checkbox syntax:

```
- [x] Completed task
- [ ] Pending task
```

## Step 2: Find the Next Unchecked Item

Scan top-to-bottom and select the **first** line matching `- [ ]`. This is the **current task**.

- Note its exact line number and full text.
- If every item is checked, inform the user that all tasks are complete and stop.

## Step 3: Execute the Task

Carry out the task described in the current item. Use all available tools as needed.

### Asking Follow-up Questions

If you need clarification or input from the user before you can proceed:

1. Ask your question(s) clearly.
2. **Wait for the user's response.**
3. Once the user answers, **immediately append a log entry** under the current task item in the plan file using this format:

```
- [ ] The original task description
  > **Q:** Your question here?
  > **A:** The user's answer here.
```

Use `>` blockquote lines, indented with 2 spaces to nest under the task item. If there are multiple rounds of questions, append each Q&A pair in order:

```
- [ ] The original task description
  > **Q:** First question?
  > **A:** First answer.
  > **Q:** Second question?
  > **A:** Second answer.
```

4. Then continue executing the task using the information gathered.

## Step 4: Mark Complete

Once the task is fully done:

1. Replace `- [ ]` with `- [x]` on the task's line in the plan file.
2. If no Q&A was logged but you want to note what was done, you may optionally add a brief completion note:

```
- [x] The original task description
  > Done: brief summary of what was accomplished.
```

3. Save the plan file.
4. **Commit checkpoint.** After saving, pause and ask the user whether they want to commit the completed task before `/step` continues:

   > Task "<task text>" is complete. Would you like to commit now (`git commit` or `/smart-commit`) before I move on, or keep going?

   Wait for the user's response. **Do not run the commit yourself** — the user runs their preferred commit command (they can use the `!` prefix in the prompt to surface output, or invoke `/smart-commit` themselves). Only after they answer do you proceed to Step 5. This pause fires every iteration, including the last one before Step 6.

## Step 5: Loop or Stop

- Increment your completed-task counter.
- If the counter equals **N**, proceed to Step 6. **Do not ask the user if they want to continue.**
- Otherwise, go back to Step 2 (re-read the plan file to pick up your latest edits) and execute the next unchecked item.
- If you run out of unchecked items before reaching N, proceed to Step 6.

## Step 6: Report

Tell the user:
- How many tasks were completed out of the N requested.
- A brief summary of each task completed.
- What the next pending task is (if any), so they know what `/step` will do next.
