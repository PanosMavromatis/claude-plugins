---
allowed-tools: Bash(git:*), Bash(find:*), Bash(cat:*), Bash(ls:*), Read, Write, Glob, Grep
description: Execute the next N unchecked items in DO.md (default 1) and log all Q&A under each item.
argument-hint: "[count]"
---

# Step

You are executing pending tasks from the project's `DO.md` file.

**`$ARGUMENTS`** is the number of items to complete. If empty or missing, default to **1**. Call this value **N**.

Loop through Steps 2–4 exactly **N** times, then hard-stop. Do **not** continue beyond N items even if unchecked items remain.

## Step 1: Read DO.md

Read `DO.md` from the project root. If it does not exist, inform the user and stop.

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
3. Once the user answers, **immediately append a log entry** under the current task item in `DO.md` using this format:

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

1. Replace `- [ ]` with `- [x]` on the task's line in `DO.md`.
2. If no Q&A was logged but you want to note what was done, you may optionally add a brief completion note:

```
- [x] The original task description
  > Done: brief summary of what was accomplished.
```

3. Save `DO.md`.

## Step 5: Loop or Stop

- Increment your completed-task counter.
- If the counter equals **N**, proceed to Step 6. **Do not ask the user if they want to continue.**
- Otherwise, go back to Step 2 (re-read `DO.md` to pick up your latest edits) and execute the next unchecked item.
- If you run out of unchecked items before reaching N, proceed to Step 6.

## Step 6: Report

Tell the user:
- How many tasks were completed out of the N requested.
- A brief summary of each task completed.
- What the next pending task is (if any), so they know what `/step` will do next.
