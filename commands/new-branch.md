---
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

### 6. Commit the doc — CONFIRM FIRST

Explain: this doc will be committed to the branch so the `/smart-merge` command can later use it to inform the PR title and body. It will be deleted automatically at merge time (kept out of `main`'s history).

Run:

```bash
git add docs/git/<branch-name>.md
git commit -m "Add branch doc for <branch-name>"
```

### 7. Report

Summarize the final state:

- Current branch: `<branch-name>`
- Doc created at: `docs/git/<branch-name>.md`
- Next steps: start the work; run `/smart-merge` when ready to merge.

## Guidelines

- **Confirm before every write**: branch creation, file creation, commit.
- **Read-only commands** (`git status`, `git log`, `git branch`) can run freely.
- **Never leave placeholders** in actual commands — always substitute real branch names.
- **Respect trivial branches**: if the user wants to skip the doc for a quick fix, don't insist. Just create the branch and note that `/smart-merge` will have less context to work with.
- **Don't push the branch doc commit specifically** unless the user says so — but make clear that regular `git push` after each working commit is the expected workflow and needs no special handling here.
