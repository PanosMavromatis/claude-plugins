---
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch -v:*), Bash(git rev-parse:*), Bash(gh pr view:*), Bash(gh pr list:*)
description: Interactive guided workflow to merge current branch into main via GitHub PR
---

You are guiding the user through merging their current Git branch into `main` via a GitHub Pull Request using `gh`. The user wants to learn by doing — **explain each step before running it, and wait for explicit approval before any write action** (push, file deletion, commit, PR create, merge). Read-only diagnostic commands can run freely.

## Workflow

### 1. Diagnostics

Gather state with read-only commands:

```bash
git branch -v
git status
git log --all --graph --oneline -20
git log main..HEAD --oneline
git diff main..HEAD --stat
```

Confirm with the user:

- Current branch is the one to be merged (not `main` itself).
- Working tree is clean. If dirty, stop and ask (stash, commit, or abort).
- The branch has commits ahead of `main`. If `git log main..HEAD` is empty, stop — there's nothing to merge.

Report a brief summary: branch name, N commits ahead of main, clean/dirty state.

### 2. Read the branch doc

Check for `docs/git/<current-branch>.md`. If it exists, read it — it contains the purpose, scope, and context captured when the branch was created. Use this as primary input for drafting the PR.

If no doc exists, note this and proceed using only the commit log and diff as input.

### 3. Draft PR title and body

Based on the branch doc (if present), the commits in `main..HEAD`, and the diff stat:

- **Title**: one line, imperative mood, sentence case, ~50-72 chars, no trailing period. Describes the umbrella scope of the whole branch, not any single commit.
- **Body**: Markdown-formatted. Group commits thematically (not chronologically) under section headers. Include Summary, and sections for the major themes present (e.g., Implementation, Infrastructure, Documentation, Testing). Keep it scannable.

Present both to the user. Let them edit, replace, or approve. Do not proceed until approved.

### 4. Delete the branch doc — CONFIRM FIRST

Explain: the branch doc was a working artifact for this branch; deleting it now means it stays in the branch's history (recoverable via SHA) but won't pollute `main`.

If the doc exists, run:

```bash
git rm docs/git/<branch-name>.md
git commit -m "Remove branch doc (merging to main)"
```

If the doc doesn't exist, skip this step.

### 5. Push the branch — CONFIRM FIRST

Check if `origin/<branch>` exists and is in sync:

```bash
git rev-parse origin/<branch> 2>/dev/null
git status -sb
```

If the branch isn't on the remote, or the local branch is ahead of its remote counterpart, run:

```bash
git push -u origin <branch>
```

(The `-u` sets upstream on first push; harmless on subsequent pushes.)

### 6. Create the PR — CONFIRM FIRST

To avoid the editor (nano) friction, write the approved body to a temp file and pass it directly:

```bash
# Save body to a temp file
cat > /tmp/pr-body-<branch>.md <<'EOF'
<approved body>
EOF

# Create the PR
gh pr create \
  --base main \
  --head <branch> \
  --title "<approved title>" \
  --body-file /tmp/pr-body-<branch>.md
```

Clean up the temp file afterward:

```bash
rm /tmp/pr-body-<branch>.md
```

Report the PR URL returned by `gh`.

### 7. Suggest merge strategy

Based on the shape of the branch, recommend one of three strategies and explain the tradeoffs:

- **Merge commit** (`--merge`): Preserves all individual commits AND creates a merge commit that visibly records the PR as a unit. Best for branches with multiple meaningful commits (phased work, logical milestones). Default choice for most feature branches.
- **Rebase and merge** (`--rebase`): Replays commits linearly on top of main. Preserves granular commits without a merge commit. Linear history, but SHAs change. Good when you want commit-level traceability without merge-commit noise.
- **Squash and merge** (`--squash`): Collapses all branch commits into one. Best when the branch has messy WIP commits that aren't worth preserving individually, or the work is better represented as a single logical unit.

Heuristic:

- N commits, all meaningful → `--merge` (preferred) or `--rebase`
- N commits, mostly WIP/fixups → `--squash`
- 1 clean commit → any; `--squash` and `--rebase` produce identical history

Let the user choose. Default to `--merge` if they're unsure.

### 8. Merge the PR — CONFIRM FIRST

Run:

```bash
gh pr merge <pr-number> --<strategy> --delete-branch
```

`--delete-branch` removes the branch both locally and on GitHub. This is the right default after a successful feature merge.

### 9. Sync local main

```bash
git checkout main
git pull
git log --oneline -5
```

Confirm the merge commit (or squashed/rebased commits) is present on local main.

### 10. Final report

Summarize:

- PR #N merged via `<strategy>` strategy
- New `main` tip: `<short-sha> <subject>`
- Branch `<name>` deleted locally and on remote
- PR URL for future reference

## Guidelines

- **Confirm before every write action**: push, file deletion, commit, PR create, merge, branch delete. State what will run, then wait for approval.
- **Read-only commands run freely**: `git status`, `git log`, `git diff`, `git branch`, `gh pr view`, `gh pr list`.
- **Never use placeholders in actual commands** — always substitute the real branch name, PR number, title, etc.
- **If anything unexpected happens** (merge conflicts, auth errors, divergent branches, failed push), stop immediately and explain before proceeding.
- **Preserve user agency**: the user is learning. When choices exist (merge strategy, title wording, scope of body), present options with tradeoffs and let them decide.
- **Be concise**: don't over-explain standard operations. One or two sentences before each action is enough.
