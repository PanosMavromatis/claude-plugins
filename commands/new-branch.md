---
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git checkout -b:*), Bash(git add:*), Bash(git commit:*), Read, Write, Glob, Grep
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

### 4. Create the branch — CONFIRM FIRST

Explain what will happen:

> I'll run `git checkout -b <name>` to create branch `<name>` from `<base>` at `<short-sha>`. Proceed?

Wait for approval, then run it.

### 5. Create the branch doc

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

### 6. Create the branch plan

The branch gets its own plan file in a directory named for the branch with `/` flattened to `-`, so branch `feat/user-auth` → `feat-user-auth/`. Always create it **directly under `docs/plan/`** — `docs/plan/feat-user-auth/`.

That name, not that path, is what `/step`, `/hitl-step` and `/smart-merge` resolve by: they search for a directory of that name anywhere beneath `docs/plan/`. So the plan can later be moved into a milestone or component directory with `git mv` and still resolve. Creating it flat keeps this command free of any grouping policy — deciding where a plan belongs is a judgement best made once the shape of the work is clear, which is never at branch-creation time.

Unlike the branch doc, **the plan is not deleted at merge** — it lands on `main` as the durable record of how this piece of work was actually executed. `/smart-merge` only stamps it as merged.

**Choose the model.** Check which master plan exists at the root of `docs/plan/`:

- `docs/plan/DO.md` exists → default to `DO.md` (plain checkbox model, driven by `/step`).
- `docs/plan/TODO.md` exists → default to `TODO.md` (marker model `[ ] [~] [x] [!] [-]`, driven by `/hitl-step`).
- Both exist → ask which this branch should use.
- Neither exists → default to `DO.md`.

State the inherited default and offer the override in one line — e.g. "Master plan uses `DO.md`, so this branch gets `DO.md`. Use `TODO.md` (HITL loop) instead?" Don't belabour it; the default is right most of the time.

**Write the file**, seeded from the Scope answer gathered in step 1. For `DO.md`:

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

The `**Status**: active` line is load-bearing: `/step` and `/hitl-step` use it to filter merged plans out of their disambiguation prompt, and `/smart-merge` rewrites it to `merged` at merge time. Always write it.

Keep the task list rough — 2-5 items is plenty. It's a working file, and `/step` will edit it as work proceeds.

**Backlink the master plan.** If a master plan exists and this branch executes one of its items, add a backlink blockquote under that item:

```markdown
- [ ] The master-plan subgoal this branch executes
  > **Branch:** feat/user-auth
```

If no master plan exists, or the branch doesn't correspond to any of its items, skip this and set `**Subgoal**: standalone` in the header.

### 7. Commit the doc and plan — CONFIRM FIRST

Explain: the branch doc informs the PR title and body and is deleted at merge; the plan directory is the durable record and stays on `main`.

Run (substituting the real branch name and the plan filename actually created):

```bash
git add docs/git/<branch-name>.md docs/plan/<flattened-branch>/DO.md
git commit -m "<subject>"
```

> **Subject.** The wording below is the message's *content*; its **form** is the
> repository's, not this plugin's. Before committing, read `git log --oneline -20` and
> match the dominant subject form — `/smart-commit` Step 3 states the rule in full,
> including why subjects matching this plugin's own templates must be discounted.
>
> Content: a branch doc and plan are being added for `<branch-name>`.

If the master plan was backlinked in step 6, include it in the same `git add`.

### 8. Report

Summarize the final state:

- Current branch: `<branch-name>`
- Doc created at: `docs/git/<branch-name>.md`
- Plan created at: `docs/plan/<flattened-branch>/<DO|TODO>.md`
- Next steps: run `/step` (or `/hitl-step`) to work the plan; `/smart-merge` when ready to merge.

## Guidelines

- **Confirm before every write**: branch creation, file creation, commit.
- **Read-only commands** (`git status`, `git log`, `git branch`) can run freely.
- **Never leave placeholders** in actual commands — always substitute real branch names.
- **Respect trivial branches**: if the user wants to skip the doc or the plan for a quick fix, don't insist. Just create the branch and note that `/smart-merge` will have less context to work with, and that `/step` will fall back to the master plan.
- **Don't push the branch doc commit specifically** unless the user says so — but make clear that regular `git push` after each working commit is the expected workflow and needs no special handling here.
