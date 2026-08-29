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

By convention the plan file lives at `docs/plan/DO.md` or in a sub-directory of `docs/plan/` (e.g. `docs/plan/auth-rewrite/DO.md`) — **not** at the project root. Resolve it as follows, and call the result **the plan file**:

1. **Path argument given.** Interpret it as a repo-relative path, a path relative to `docs/plan/`, or the name of a directory under `docs/plan/` — whichever resolves. If it names a directory, look for `DO.md` inside it. If it resolves to nothing, say so and stop; do not silently fall back to discovery.
2. **No path argument.** Glob `docs/plan/**/DO.md`.
   - Exactly one match → use it.
   - Several matches → list them and ask the user which to use. Wait for the answer; do not guess.
   - No matches → go to 3.
3. **Legacy fallback.** If `DO.md` exists at the project root, use it, but tell the user the convention is now `docs/plan/` and suggest moving it (`git mv DO.md docs/plan/DO.md`).
4. If nothing is found anywhere, inform the user and stop.

State which plan file you resolved to before doing any work. Every later reference to `DO.md` in this command means the resolved plan file, and all its paths (log entries, checkbox edits) apply to that file.

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
