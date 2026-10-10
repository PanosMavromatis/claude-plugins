---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/propose-branch-plan.sh:*), Bash(git status:*), Bash(git log:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git checkout -b:*), Bash(git add:*), Bash(git commit:*), Read, Write, Edit, Glob, Grep
description: Create a new feature branch with documented purpose
---

You are helping the user create a new Git branch with proper documentation. The user prefers to learn by doing — explain briefly before acting, and confirm with the user before any write operation (branch creation, file creation, commits).

Optional arguments: $ARGUMENTS — if provided, may contain a suggested branch name and/or short purpose.

## Workflow

### 1. Gather context

Ask the user, unless already provided via `$ARGUMENTS`:

- **Purpose**: what is this branch for? (feature, fix, experiment, docs, refactor)
- **Scope**: small patch, multi-phase feature, open-ended exploration?
- **Related context**: linked issues, related PRs, prior discussions, dependencies?

Keep this lightweight — 2-3 short answers are enough. Don't interrogate.

### 2. Suggest a branch name

Propose a branch name following the convention `<type>/<short-slug>`:

- Types: `feat`, `fix`, `exp`, `docs`, `refactor`, `chore`
- Slug: lowercase, hyphenated, 2-4 words, no redundant prefixes
- Examples: `feat/user-auth`, `fix/pdf-export`, `exp/cython-backend`, `docs/api-reference`

Present the suggested name and ask for confirmation or a correction.

### 3. Verify preconditions

Run read-only diagnostics:

```bash
git status
git branch --show-current
git log --oneline -5
```

Before proceeding, confirm:

- Working tree is clean (no uncommitted changes to tracked files). If not, stop and ask how to proceed (stash, commit, or abort).
- Current branch is `main` (or whichever base the user wants to branch from). If not, ask whether to switch first.

### 4. Propose the plan — read-only, before the branch exists

The bundled `scripts/propose-branch-plan.sh` decides where the plan goes, what its files are called, and where its master-plan backlink goes. Placement is a set of rules — the layout comes from the root plan, the directory from the open revision, goal-file names from the slug rule `/step` and `/hitl-step` read them by — so the script decides and this command writes exactly what it lists. Do not work any of it out yourself. It runs before the branch is created, so a refused name costs nothing to change.

**Choose the model** first. Check which master plan exists at the root of `docs/plan/`:

- `docs/plan/DO.md` exists → default to `DO.md` (plain checkbox model, driven by `/step`).
- `docs/plan/TODO.md` exists → default to `TODO.md` (marker model `[ ] [~] [x] [!] [-]`, driven by `/hitl-step`).
- Both exist → ask which this branch should use.
- Neither exists → default to `DO.md`.

State the inherited default and offer the override in one line — e.g. "Master plan uses `DO.md`, so this branch gets `DO.md`. Use `TODO.md` (HITL loop) instead?" Don't belabour it; the default is right most of the time.

**Run it** with the model, the agreed branch name, and the Scope items from step 1 as titles, one argument each, in order. Keep the list rough — 2-5 items is plenty. Run it alone, in exactly this form, with nothing appended, chained or piped: `allowed-tools` matches that command and nothing else.

    ${CLAUDE_PLUGIN_ROOT}/scripts/propose-branch-plan.sh <DO.md|TODO.md> <branch-name> -- "<scope item>" "<scope item>"

Act on `result:`. A key with several items continues on lines indented two spaces.

- `ask`: the master plan has open subgoals with no branch yet. Show `candidates:` and ask which one this branch executes, offering standalone as well. Never pick one yourself. Run the script again with `--subgoal <file>:<line>` (the candidate's prefix, exactly as shown) or `--standalone`, before the `--`.
- `propose`: show `layout:`, `revision:`, `subgoal:`, `dir:`, `index:`, every `goals:` line, `backlink:`, and every `warnings:` line. This is what step 7 writes, and nothing else.
- `error`: relay each `problem:` line with its `fix:` line, and stop before creating anything. A name that is taken means the branch was planned before: offer to resume that plan instead, or go back to step 2 for another name. The fix is the user's to choose; do not work around it.
- no `result:` line, or no `message:` line (the report's last key, so the report was cut short): show the output and stop. Never act on part of a report.

### 5. Create the branch — CONFIRM FIRST

Explain what will happen:

> I'll run `git checkout -b <name>` to create branch `<name>` from `<base>` at `<short-sha>`. Proceed?

Wait for approval, then run it.

### 6. Create the branch doc

Write `docs/git/<branch-name>.md` with this template, filled in from the gathered context:

```markdown
# <branch-name>

**Created**: <YYYY-MM-DD>
**Base**: <base-branch> at <short-sha>
**Status**: active

## Purpose

<One-paragraph summary of why this branch exists and what it will deliver.>

## Scope

<Bulleted list of planned work. Can be rough — this is a working doc.>

## Context

<Related issues, prior discussions, docs consulted, dependencies. Include links.>

## Notes

<Running log. Add entries as work progresses — decisions made, things tried, things deferred.>
```

### 7. Write the branch plan — CONFIRM FIRST

Write exactly the paths the proposal listed in step 4 — `index:`, each `goals:` path, and the backlink — and nothing else. Show what you will write, then write it.

The plan's directory is named for the branch with `/` flattened to `-` (`feat/user-auth` → `feat-user-auth/`). That name, not its path, is what `/step`, `/hitl-step` and `/smart-merge` resolve by: they search for a directory of that name anywhere beneath `docs/plan/`. So a plan can sit inside a revision's directory, where the proposal puts a subgoal's plan under a revisions index, or flat, and can later be moved with `git mv` and still resolve.

Unlike the branch doc, **the plan is not deleted at merge** — it lands on `main` as the durable record of how this piece of work was actually executed. `/smart-merge` only stamps it as merged.

**`layout: per-goal`** — an index, and one goal file per goal. The index, at `index:`:

```markdown
# <branch-name>

**Status**: active
**Created**: <YYYY-MM-DD>
**Revision**: <revision:>
**Subgoal**: <the subgoal: line's text after its `- [ ] ` marker, or standalone>
**Layout**: per-goal

## Goals

<each goals: line's index line — the text after its path — in order>
```

Leave out `**Revision**:` when `revision:` is `—`. Each goal file, at its `goals:` path, takes the index line's text after its marker as its heading:

```markdown
# <NN — title>

**Goal**: [ ]
```

**`layout: legacy`** — one file, at `index:`, as before. For `DO.md`:

```markdown
# <branch-name>

**Status**: active
**Created**: <YYYY-MM-DD>
**Subgoal**: <the master-plan item this branch executes, or "standalone">

## Tasks

- [ ] <first task from the scope discussion>
- [ ] <second task>
```

For `TODO.md`, use the same header and the three-tier structure `/hitl-step` expects (top-level goals at indent 0, subgoals indented beneath them).

Either way, the `**Status**: active` line is load-bearing: `/step` and `/hitl-step` use it to filter merged plans out of their disambiguation prompt, and `/smart-merge` rewrites it to `merged` at merge time. Always write it.

**The backlink.** If `backlink:` is not `—`, insert one new line directly after the line it names:

```markdown
  > **Branch:** <branch-name>
```

Use `Edit`, never `Write`: the master plan is the one file that grows without bound, and rewriting it whole costs what reading it whole does. `Read` that one line (`offset` it, `limit` 2), and anchor the `Edit` on it together with the line after it, so the match is unique. If `backlink:` is `—`, the plan is standalone and nothing is backlinked.

**Mark the subgoal in progress.** When the model is `TODO.md`, also flip the marker on the `subgoal:` line from `[ ]` to `[~]`: a branch is now working that subgoal, and `[~]` is how the marker model tells anyone scanning the master plan so. Leave a `[~]` as it is. A `DO.md` master plan has no `[~]`, so leave its marker alone, as with a standalone plan, which has no `subgoal:` line. `Read` that one line the same way and change only its marker; the line count does not change, so the backlink's line still holds. `/smart-merge` closes the item at merge time.

### 8. Commit the doc and plan — CONFIRM FIRST

Explain: the branch doc informs the PR title and body and is deleted at merge; the plan directory is the durable record and stays on `main`.

Run, substituting the real paths — the branch doc, `index:`, every `goals:` path, and the master file `backlink:` names if one was backlinked:

```bash
git add docs/git/<branch-name>.md <index> <goal file>... <backlinked master file>
git commit -m "<subject>"
```

> **Subject.** The wording below is the message's *content*; its **form** is the
> repository's, not this plugin's. Before committing, read `git log --oneline -20` and
> match the dominant subject form — `/smart-commit` Step 3 states the rule in full,
> including why subjects matching this plugin's own templates must be discounted.
>
> Content: a branch doc and plan are being added for `<branch-name>`.

### 9. Report

Summarize the final state:

- Current branch: `<branch-name>`
- Doc created at: `docs/git/<branch-name>.md`
- Plan created at: the `index:` path, with its goal files if per-goal, and the backlink if any
- Next steps: run `/step` (or `/hitl-step`) to work the plan; `/smart-merge` when ready to merge.

## Guidelines

- **Confirm before every write**: branch creation, file creation, commit.
- **Read-only commands** (`git status`, `git log`, `git branch`) can run freely.
- **Never leave placeholders** in actual commands — always substitute real branch names.
- **Respect trivial branches**: if the user wants to skip the doc or the plan for a quick fix, don't insist. Skip step 4 and step 7, create the branch, and note that `/smart-merge` will have less context to work with, and that `/step` will fall back to the master plan.
- **Don't push the branch doc commit specifically** unless the user says so — but make clear that regular `git push` after each working commit is the expected workflow and needs no special handling here.
