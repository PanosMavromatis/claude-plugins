---
allowed-tools: Bash(git fetch:*), Bash(git branch -vv:*), Bash(git branch --show-current:*), Bash(git worktree list:*), Bash(git rev-parse:*), Bash(git status:*), Bash(git log:*)
description: Delete local branches whose upstream is gone, and their worktrees, with confirmation.
---

# Clean Gone Branches

You are cleaning up local branches whose upstream tracking branch has been deleted on the remote (Git marks these `[gone]`), along with any worktrees attached to them. The user wants to learn by doing — **explain each step before running it, and wait for explicit approval before any deletion** (worktree removal, branch deletion). Read-only diagnostics run freely.

The destructive operations here (`git worktree remove`, `git branch -D`) are intentionally **not** in `allowed-tools`, so they additionally surface a harness permission prompt. The in-prompt confirmation below is the primary guard; treat the harness prompt as a backstop, not a substitute.

## Workflow

### 1. Refresh and gather state — read-only

First, optionally refresh which branches are `[gone]`:

```bash
git fetch --prune
```

Explain before running: `--prune` updates remote-tracking refs (e.g. deletes `origin/foo` when `foo` is gone on the remote) so `[gone]` status is accurate. **It deletes no local branches.** If it fails (offline, no remote), say so and proceed with the local view — `[gone]` markers may just be stale.

Then gather state:

```bash
git branch -vv
git worktree list
git branch --show-current
```

> **Note:** `[gone]` only appears under `git branch -vv` (double `v`). `git branch -v` does **not** show it. Always use `-vv` here.

### 2. Resolve the deletion targets

From `git branch -vv`, collect every branch whose tracking info reads `[<upstream>: gone]`. For each such branch:

- A `+` prefix in the branch list means it is checked out in a linked **worktree**. Map it to its worktree path from `git worktree list` (the line whose trailing `[<branch>]` matches). That worktree must be removed **before** the branch can be deleted.
- A `*` prefix means it is the current branch.

**Guards — exclude these from the target list, and warn:**

- The **current branch** (`git branch --show-current`). It cannot be deleted while checked out; if it is `[gone]`, tell the user to switch away first.
- `main` (or the repository's default branch). It should never be `[gone]`; if it appears, treat it as a red flag and stop to ask rather than deleting.

### 3. Present the targets and CONFIRM — wait for approval

Print the resolved set with an explicit **count**:

- The branch names that will be deleted (real names, never placeholders).
- The worktree paths that will be removed first, paired with their branch.

Then:

- **If the list is empty**, report "No `[gone]` branches to clean" and stop. Nothing else runs.
- **If exactly one branch is in scope**, ask for a single confirmation to remove it (and its worktree, if any).
- **If more than one branch is in scope**, flag it prominently before asking:

  > ⚠️ **N branches are `[gone]`, not 1** — review the full list below before confirming. Deletion is `-D` (force) and is not easily undone.

  Then ask the user to approve all, exclude specific entries, or abort.

Do not proceed to deletion until the user explicitly approves the set.

### 4. Execute the deletions — only after approval

For each approved target, using the **real substituted names** (never `<branch>` literals):

```bash
# If the branch has a worktree, remove it first:
git worktree remove --force <worktree-path>

# Then delete the branch:
git branch -D <branch-name>
```

Run these per target so a failure on one branch doesn't abort the rest. If a deletion fails (e.g. unmerged-work warning, locked worktree), stop on that target, explain, and ask how to proceed before continuing with the others.

### 5. Report

Summarize:

- Worktrees removed (paths).
- Branches deleted (names).
- Anything skipped by the guards (current branch / `main`) or by user exclusion, with the reason.

## Guidelines

- **Confirm before every deletion**: worktree removal and branch deletion. State exactly what will run, then wait for approval. Batch approval for the whole set is fine; a prominent count and the `>1` warning are what protect against an "I assumed one branch" mental model.
- **Read-only commands run freely**: `git fetch --prune`, `git branch -vv`, `git worktree list`, `git branch --show-current`, `git status`, `git log`.
- **`git branch -D` and `git worktree remove` are deliberately absent from `allowed-tools`.** This is not drift — do not "fix" it by adding them. They are the two irreversible operations in this command, and the harness permission prompt is a second gate behind the confirmation in step 3. Adding `Bash(git branch:*)` would be worse still: it is a prefix pattern, so it would authorize `git branch -D` on any branch, which is precisely the failure this omission prevents.
- **Never use placeholders in actual commands** — always substitute the real branch name and worktree path before running.
- **Never delete the current branch or `main`.** Skip and warn instead.
- **If anything unexpected happens** (a `[gone]` `main`, a locked worktree, an unmerged-branch refusal), stop and explain before proceeding.
- **Be concise**: one or two sentences before each action is enough.
