---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh:*), Bash(${CLAUDE_PLUGIN_ROOT}/scripts/check-plan-index.sh:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git rev-parse:*), Bash(git add:*), Bash(ls:*), Read, Write, Edit, Glob, Grep
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

## Step 1: Locate the plan file

Plan files live under `docs/plan/`: the **master plan**, whose items each spawn a branch,
and **branch plans**, a `TODO.md` in a directory named for the branch with `/` flattened
to `-` (`feat/user-auth` → `feat-user-auth/`). That name is a plan's identity, not its
location: it may sit anywhere beneath `docs/plan/`, and `git mv` reorganises plans
without any command changing.

The bundled `scripts/locate-plan.sh` resolves the plan, by the five rungs the plugin's
`CLAUDE.md` describes, for both step commands. It is read-only and deterministic. Do not
resolve the plan yourself.

1. Run it, with the path token from `$ARGUMENTS` after `--`, or nothing after it if there
   is none. Run it alone, in exactly that form, with nothing appended, chained or
   piped: `allowed-tools` matches that command and nothing else.

       ${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh TODO.md -- <path>

   If the user named an item out of order, run it once to find the plan, then run
   `${CLAUDE_PLUGIN_ROOT}/scripts/check-plan-index.sh TODO.md -- <plan>`, alone, to list
   its open items by line: in a per-goal plan, the item is an index line among them. Run
   `locate-plan.sh` again with `--goal <line>` before the `--`.
2. Act on `result:`; the report says everything the exit status does. A key with
   several items continues on lines indented two spaces.
   - `found`: the plan file is `plan:`. State it, with `rung:` and `kind:`,
     before any work, and show every `warnings:` line; then carry on. If `layout:` is
     `per-goal`, the plan is an index and `goal-file:` holds the selected goal; Steps 2–6
     say where each read and edit goes. A warning that the `next:` line's marker differs
     from its goal file's `**Goal**:` means an edit stopped between the two files. The
     goal file is the source of truth: offer to rewrite that index line with its marker,
     and once the user agrees and it is written, run the script again before any work.
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
- Stay inside the repository, with `Read` and `git status`, `git log`, `git diff` and
  `ls`, each run alone. To search, use `Grep` and `Glob` if your session has them; native
  macOS and Linux builds have had neither since Claude Code 2.1.117, and there use shell
  `grep` and `find`, read-only, with no `-exec`, `-delete` or redirection. Never read or
  search outside it, even where a path hints at another repository, and never edit, move,
  create or delete anything; any other command needs the user's approval.
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

The file has a three-tier structure:

```
## Section header        ← not a checkbox; just groups goals
- [ ] Top-level goal     ← the unit of work per iteration
  > **Note:** ...        ← a finding; never a checkbox (see 3b-bis)
  - [ ] Subgoal          ← acceptance criterion for the parent goal
  - [ ] Subgoal
```

## Step 2: Find the Next Top-level Goal

The report's `next:` is the goal: the first indent-0 `[~]`, else the first `[ ]`. `[~]`
comes first because a goal in progress is where the last run stopped. `subgoals:` lists its
acceptance criteria. A goal the user named out of order was passed as `--goal`, and
`next:` is that one.

- Read the goal and its subgoals: the whole file for a branch plan, which is small; for a
  master plan, a window from `next:` to the last `subgoals:` line and the blockquotes
  under it.
- If `next: —`, every top-level goal is `[x]` or `[-]`: say that all reachable work is
  complete, and stop. List `blocked:` separately, so the user knows what is waiting on them.
- **A per-goal plan** (`layout: per-goal`): read the index and `goal-file:` whole; both are
  small. `subgoals:` are the goal file's lines. Everything that sits under a goal in a
  single-file plan sits in its goal file, **outdented one level**: the goal's own `>`
  lines at indent 0, directly under `**Goal**:` and before the first subgoal; its
  subgoals at indent 0; and each subgoal's `>` lines at indent 2 beneath it.

## Step 3: Execute the Goal

**At the start of execution**, flip the selected goal's marker from `[ ]` → `[~]` (leave it alone if already `[~]`) and save the plan file. This makes mid-work state visible across sessions — if the work is interrupted, the next `/hitl-step` resumes here. Flip subgoals to `[~]` as you actively work on each one (optional for fast-finishing goals, but recommended for any subgoal spanning more than one conversational turn).

**In a per-goal plan, every change to a goal's marker goes goal file first, then index**: `**Goal**:` in the goal file, then the goal's index line. The goal file is the source of truth and the index mirrors it, so a run interrupted between the two leaves a mismatch Step 1 can repair; the other order would lose the edit. The Q&A (3b), notes (3b-bis), subgoal markers and escape-hatch notes all go in the goal file, outdented as Step 2 describes.

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
- **In a per-goal plan**, a split goal NN gains a sibling NNa. Add the index line `- [ ] NNa — <title>` directly after NN's line, and create `TODO/NNa-<slug>.md` with the heading `# NNa — <title>` and the line `**Goal**: [ ]`. The slug is the title lowercased, with each run of other characters as one `-`, at most 40 characters. Step 6's check confirms the name. Descoping a goal flips its goal file first, then its index line.

## Step 4: Mark Complete

Determine the parent goal's final state based on the states of its subgoals and the work actually done. This is the only place a goal can leave the `[~]` state.

**Parent-state rules:**

- **`[x]` — Complete**: every subgoal is `[x]` or `[-]`. At least one subgoal must be `[x]` (a goal with all subgoals `[-]` is itself `[-]`, not `[x]`).
- **`[!]` — Blocked**: at least one subgoal is `[!]` and the remaining work can't finish without it. Add a `> **Blocked:** reason` note under the parent if the blocking source isn't obvious from the subgoals.
- **`[~]` — Still in progress**: real progress was made (some subgoals flipped to `[x]`) but the goal isn't done yet. Leave the parent as `[~]` so the next `/hitl-step` resumes here. This is a legitimate Step 4 outcome — not every iteration has to finish a top-level goal.
- **`[-]` — Descoped**: the entire goal is being abandoned. Add a `> **Descoped:** reason` note under the parent.

**Check the subgoals before flipping the parent — do not do it from memory.** A goal that
took several turns has scrolled its own acceptance criteria out of view, and the `[x]` rule
above is precisely a claim about lines you are no longer looking at. Re-read them, or run
`check-plan-index.sh` as Step 6 does and take the `open:` lines between this goal's line
and the next goal's, and resolve every one before step 2 below.
A hit that turns out not to be a task at all is a finding written as a checkbox: convert it
to `> **Note:**` per 3b-bis rather than ticking it, since ticking implies work that was
never done. In a per-goal plan the subgoals are the goal file's items: `Read` the goal
file again, since it is small.

**Applying the result:**

1. Update each subgoal's marker to reflect its current state (`[x]`, `[!]`, `[-]`, or `[~]` — never `[ ]` once work has touched it).
2. Flip the parent goal's marker per the rules above. In a per-goal plan, flip `**Goal**:` in the goal file first, then the index line.
3. If the completed work isn't obvious from the subgoals alone, optionally add a brief `> **Done:**` note under the parent (in a per-goal plan, at indent 0 in the goal file, under `**Goal**:`):

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
- Otherwise, go back to Step 2 and execute the next top-level goal. Pick up your latest edits by running the script again, exactly as in Step 1, rather than re-reading the file: it reports the next goal, and in a per-goal plan its goal file. On a large master plan a whole-file re-read every iteration multiplies the cost by N, which is exactly the loop this command is built around.
- If no top-level goals remain in `[ ]` or `[~]` state, proceed to Step 6.

## Step 6: Report

Tell the user:

- How many goals were processed out of N requested, and each goal's final state (`[x]`, `[!]`, `[-]`, or `[~]`) with a one-line summary.
- **Blocked items**: if any subgoal or goal landed in `[!]` this iteration, surface the blocking reason explicitly — the user needs to resolve it before the next run can close that goal.
- **Section completion check**: if the just-completed section has all top-level goals in `[x]` or `[-]` state (under the nearest `##` above), say so and suggest running `/smart-commit` with a proposed message naming the section topic. **Do not put a subject form on it** — no conventional prefix, no imperative template. `/smart-commit` Step 3 reads the convention from the repository, and a form pasted in here would be a guess arriving ahead of the command that actually knows. Sections with a `[!]` goal are **not** complete.

  **Verify this at every indent, not just at the top level.** Step 4 should already have
  made it impossible for a `[x]` parent to hide an open subgoal, but this is the line the
  user acts on, so it is worth re-deriving rather than inheriting. Run, alone, with
  `plan:` from Step 1:

      ${CLAUDE_PLUGIN_ROOT}/scripts/check-plan-index.sh TODO.md -- <plan>

  It reads both layouts. Its report has `result:`, `open:`, `problem:` and `fix:`, read as
  Step 1 reads `locate-plan.sh`'s. Each `open:` line is an open item, at any indent; in a
  one-file plan it ends `— under <heading>`, naming the `## ` section it sits in.
  - `clean`: report the section complete only if no `open:` line names its heading, and
    the plan complete only if `open:` is `—`. A per-goal plan's goals have no sections,
    so for one only the second applies. A completion claim is the one report a reader
    will not re-check.
  - `drift`: relay each `problem:` line with its `fix:` line. A per-goal plan's index
    and goal files disagree, and the fix is the user's to make.
  - `error`, or no report: show the output, and report nothing complete.
- What the next pending top-level goal is (if any) — prefer a `[~]` in-progress goal over a `[ ]` not-started one when naming it, so the user knows the next `/hitl-step` will resume rather than start fresh.
