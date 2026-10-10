---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git rev-parse:*), Bash(git add:*), Bash(ls:*), Read, Write, Edit, Glob, Grep
description: Execute the next N unchecked items in a docs/plan DO.md (default 1) and log all Q&A under each item.
argument-hint: "[count] [plan-path]"
---

# Step

You are executing pending tasks from the project's `DO.md` plan file.

**`$ARGUMENTS`** may contain up to two whitespace-separated tokens, in any order:

- a **bare integer** — the number of items to complete. Call this value **N**. If absent, default to **1**.
- **anything else** — a path selecting the plan file (see Step 1). If absent, discover it.

Loop through Steps 2–4 exactly **N** times, then hard-stop. Do **not** continue beyond N items even if unchecked items remain.

## Step 1: Locate the plan file

Plan files live under `docs/plan/`: the **master plan**, whose items each spawn a branch,
and **branch plans**, a `DO.md` in a directory named for the branch with `/` flattened
to `-` (`feat/user-auth` → `feat-user-auth/`). That name is a plan's identity, not its
location: it may sit anywhere beneath `docs/plan/`, and `git mv` reorganises plans
without any command changing.

The bundled `scripts/locate-plan.sh` resolves the plan, by the five rungs the plugin's
`CLAUDE.md` describes, for both step commands. It is read-only and deterministic. Do not
resolve the plan yourself.

1. Run it, with the path token from `$ARGUMENTS` after `--`, or nothing after it if there
   is none. Run it alone, in exactly that form, with nothing appended, chained or
   piped: `allowed-tools` matches that command and nothing else.

       ${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh DO.md -- <path>

   If the user named an item out of order, run it once to find the plan, `Grep` that
   file for the item, and run it again with `--goal <line>` before the `--`.
2. Act on `result:`; the report says everything the exit status does. A key with
   several items continues on lines indented two spaces.
   - `found`: the plan file is `plan:`. State it, with `rung:` and `kind:`,
     before any work, and show every `warnings:` line; then carry on. If `layout:` is
     `per-goal`, say this version cannot yet edit goal files, and stop.
   - `ask`: show `candidates:` and `message:`, wait for the user's choice, and
     run the script again with it as the path. Never pick a candidate yourself.
   - `none`: say there is no plan, and stop.
   - `error`: the repository breaks a convention resolution relies on. Relay
     each `problem:` line with its `fix:` line, offer to investigate (below), and stop.
     The fix is the user's to make; do not work around it.
   - no `result:` line (a usage error, or the script itself failed), or no `message:`
     line (the report's last key, so the report was cut short): show the output, offer
     to investigate (below), and stop. Never act on part of a report. There is no second
     resolution path in this command.
3. **Check before trusting.** Confirm the `next:` line matches the file verbatim, within
   the read Step 2 makes or with a one-line `Read`. A mismatch means the file changed
   after the script read it: run the script once more, and stop if it still disagrees.

**Investigating, only when asked.** The offer is one line, ending the reply: that you can
look into it, read-only. Investigate only if the user then asks. When they do:
- Stay inside the repository, with `Read`, `Grep`, `Glob`, and `git status`, `git log`,
  `git diff` and `ls`, each run alone. Never read or search outside it, even where a path
  hints at another repository, and never edit, move, create or delete anything; any other
  command needs the user's approval.
- Look for evidence that makes each `fix:` exact, or shows it wrong: the lines the report
  names, the history (`git log --stat --follow -- <path>`), near-miss names. For a failed
  run, start from its stderr and any `hint:` line.
- Report each finding with its evidence (file:line, commit, output), then a fix, marked as
  yours rather than the script's. If you find nothing beyond the script's own `fix:`, say
  so. Applying a fix is the user's call; once they have, start again from step 1.

A master plan (`kind: legacy-master` or `revision-master`) grows without bound, and past
~500 subgoals a whole-file read silently truncates. Never read one whole: read bounded
windows around the lines the report names.

### Status stamp

A plan file may carry a status line near the top:

```
**Status**: active
**Status**: merged — PR #123 — 2026-08-29
```

`/new-branch` writes `active` at creation; `/smart-merge` rewrites it to `merged` when the branch lands. For the script's glob rung, a plan counts as **merged** only if it has a `**Status**:` line whose value begins with `merged`. Everything else — `active`, any other value, or no status line at all — counts as **active**. Failing toward "active" is deliberate: plans merged outside `/smart-merge` never get stamped, and showing a stale option costs a second while hiding a live one costs much more.

The file uses standard Markdown checkbox syntax:

```
- [x] Completed task
- [ ] Pending task
```

## Step 2: Find the Next Unchecked Item

The report's `next:` is the **current task**: the first `- [ ]` line, at any indent.

- Read the item and any blockquotes beneath it: the whole file for a branch plan, which is
  small; for a master plan, a window starting at `next:`.
- If `next: —`, every item is checked: say that all tasks are complete, and stop.

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

### Findings → `> **Note:**`, never a checkbox

Work turns up things worth keeping that are **not tasks**: a measurement, a surprise, a
claim in the codebase that turned out to be false, a reason something was left alone. Log
those as a `> **Note:**` blockquote under the task, in the same 2-space-indented form:

```
- [x] The original task description
  > **Note:** what was observed, and why it will matter to whoever reads this next.
```

**Never write a finding as a `- [ ]` line.** A checkbox is a promise that something will be
done, so a note wearing one reads as outstanding work — and since a plan is usually
surveyed by grepping for unchecked items, a note that is really a note will keep being
re-reported as unfinished by everyone who looks. If it genuinely implies future work, it is
a task: write it as one, where it belongs in the list.

## Step 4: Mark Complete

Once the task is fully done:

1. Replace `- [ ]` with `- [x]` on the task's line in the plan file. Use `Edit` for this — it is a one-line change, and rewriting the whole file with `Write` costs as much as reading it whole, which is the cost Step 2 exists to avoid on a large master plan.
2. If no Q&A was logged but you want to note what was done, you may optionally add a brief completion note:

```
- [x] The original task description
  > Done: brief summary of what was accomplished.
```

3. Save the plan file — again as a targeted edit, not a full rewrite.
4. **Commit checkpoint.** After saving, pause and ask the user whether they want to commit the completed task before `/step` continues:

   > Task "<task text>" is complete. Would you like to commit now (`git commit` or `/smart-commit`) before I move on, or keep going?

   Wait for the user's response. **Do not run the commit yourself** — the user runs their preferred commit command (they can use the `!` prefix in the prompt to surface output, or invoke `/smart-commit` themselves). Only after they answer do you proceed to Step 5. This pause fires every iteration, including the last one before Step 6.

## Step 5: Loop or Stop

- Increment your completed-task counter.
- If the counter equals **N**, proceed to Step 6. **Do not ask the user if they want to continue.**
- Otherwise, go back to Step 2 and execute the next unchecked item. Pick up your latest edits the same way Step 2 found the first item — re-`Grep` for the next `- [ ]` rather than re-reading the file. On a large master plan a whole-file re-read every iteration multiplies the cost by N, which is exactly the loop this command is built around.
- If you run out of unchecked items before reaching N, proceed to Step 6.

## Step 6: Report

Tell the user:
- How many tasks were completed out of the N requested.
- A brief summary of each task completed.
- What the next pending task is (if any), so they know what `/step` will do next.
