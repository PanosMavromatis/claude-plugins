---
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch -v:*), Bash(git rev-parse:*), Bash(gh pr view:*), Bash(gh pr list:*)
description: Interactive guided workflow to merge current branch into main via GitHub PR
---

You are guiding the user through merging their current Git branch into `main` via a GitHub Pull Request. The user wants to learn by doing — **explain each step before running it, and wait for explicit approval before any write action** (push, file deletion, commit, PR create, merge). Read-only diagnostic commands can run freely.

## GitHub access: MCP preferred, `gh` as fallback

GitHub operations in this command have two implementations. **Prefer the GitHub MCP server** when one of its tools is present in your tool list; otherwise use `gh`. There is no shell command that reports MCP availability — you can see your own tools, so judge from that.

**Fall back on 404 *or* 403.** A fine-grained PAT that does not cover the repository returns **404, not 403** — GitHub masks the existence of private repositories deliberately. A fallback keyed only on 403 would never fire in the exact case it exists for. Treat either status from an MCP GitHub call as "not permitted here" and fall back.

**Announce every fallback, naming the repository and the operation:**

> MCP `merge_pull_request` returned 404 for `owner/repo` — falling back to `gh pr merge`, which is separately authenticated with broader scope.

This is not decoration. A silent fallback turns a permission boundary into a speed bump nobody notices; an announced one makes repeated fallbacks a legible signal that the PAT's repository selection or permissions should be widened. **Never fall back silently.**

**Do not diagnose a 404 by guessing.** If it is unclear whether the repository is outside the PAT's scope, misnamed, or the server is failing, run the three-call diagnostic: `get_me` (identity), the failing call (target access), then `search_repositories` with `user:<owner>` (what the PAT actually covers).

**Complete one operation on one mechanism.** Do not begin an operation via MCP and finish it with `gh`; fall back at operation boundaries, not mid-sequence.

Local git operations — commits, pushes, branch deletion, file removal — have no MCP equivalent and always use the shell.

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

These are local and always run as shown. If you need to check whether a PR already exists for this branch, prefer MCP `list_pull_requests` (filter by `head`) or `pull_request_read` with method `get`; fall back to `gh pr list` / `gh pr view` per the rule above.

Confirm with the user:

- Current branch is the one to be merged (not `main` itself).
- Working tree is clean. If dirty, stop and ask (stash, commit, or abort).
- The branch has commits ahead of `main`. If `git log main..HEAD` is empty, stop — there's nothing to merge.

Report a brief summary: branch name, N commits ahead of main, clean/dirty state.

### 2. Read the branch doc and the branch plan

**Branch doc.** Check for `docs/git/<current-branch>.md`. If it exists, read it — it contains the purpose, scope, and context captured when the branch was created. Use this as primary input for drafting the PR.

**Branch plan.** Check for `docs/plan/<flattened-branch>/DO.md` or `TODO.md`, where the directory is the branch name with `/` flattened to `-` (branch `feat/user-auth` → `docs/plan/feat-user-auth/`). If it exists, read it — the completed items and their `> **Q:** / > **A:**` logs record how the work actually went, which is useful input for the PR body's Summary.

Unlike the branch doc, **the plan is not deleted at merge.** It lands on `main` as the durable record; step 7 only stamps it.

**Warn on unfinished items.** If the plan still has items in `[ ]`, `[~]`, or `[!]`, list them and say so plainly:

> The plan for this branch has N unfinished items: <list>. Merging is fine — the plan survives on `main` and you can keep working it — but flagging in case something was meant to land in this PR.

This is a **warning, not a gate**. Do not block the merge; the user may be deliberately landing partial work, and nothing is lost either way.

If neither file exists, note this and proceed using only the commit log and diff as input.

### 3. Draft PR title and body

Based on the branch doc (if present), the commits in `main..HEAD`, and the diff stat:

- **Title**: one line, imperative mood, sentence case, ~50-72 chars, no trailing period. Describes the umbrella scope of the whole branch, not any single commit.
- **Body**: Markdown-formatted. Group commits thematically (not chronologically) under section headers. Include Summary, and sections for the major themes present (e.g., Implementation, Infrastructure, Documentation, Testing). Keep it scannable.
- **Plan pointer**: if a branch plan exists, end the body with a line pointing at it — `Plan: \`docs/plan/feat-user-auth/DO.md\`` (substituting the real path). The plan lands on `main` with this merge, so the pointer resolves permanently. Do **not** paste the plan's contents into the body: PR bodies cap at 65,536 characters, and the file itself is the record.

Present both to the user. Let them edit, replace, or approve. Do not proceed until approved.

### 4. Delete the branch doc — CONFIRM FIRST

Explain: the branch doc was a working artifact for this branch; deleting it now means it stays in the branch's history (recoverable via SHA) but won't pollute `main`.

**Only the branch doc is deleted.** Leave `docs/plan/<flattened-branch>/` alone — it is meant to land on `main`.

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

**MCP path (preferred).** Call `create_pull_request` with `owner`, `repo`, `head` (the branch), `base` (`main`), `title`, and `body`. The body is a plain string parameter, so the approved body goes straight in — no temp file, and no heredoc quoting hazard when the body contains backticks or `$`.

**`gh` fallback.** `gh pr create` reads the body from a file to avoid editor friction:

```bash
cat > /tmp/pr-body-<branch>.md <<'EOF'
<approved body>
EOF

gh pr create \
  --base main \
  --head <branch> \
  --title "<approved title>" \
  --body-file /tmp/pr-body-<branch>.md

rm /tmp/pr-body-<branch>.md
```

Report the PR number and URL, and note which path created it — the PR number is needed by step 7.

### 7. Record the merge in the plans — CONFIRM FIRST

The PR number now exists, and the branch is still open — this is the only window where both are true, so both plan updates happen here, on the branch, in one commit. Doing it after the merge would mean committing directly to `main`, which branch protection commonly forbids.

Skip this step entirely if no branch plan and no master plan exist.

**Stamp the branch plan.** Rewrite its status line to record the merge:

```
**Status**: merged — PR #123 — 2026-08-29
```

`/step` and `/hitl-step` read this line to filter merged plans out of their disambiguation prompt. The value must begin with `merged` for that filter to see it.

**Update the master plan.** If `docs/plan/DO.md` or `docs/plan/TODO.md` has an item backlinked to this branch (a `> **Branch:** <branch-name>` blockquote beneath it, written by `/new-branch`), mark that item complete and log the outcome beneath it:

```markdown
- [x] The master-plan subgoal this branch executed
  > **Branch:** feat/user-auth
  > **Done:** One-or-two-sentence summary of what landed — PR #123
```

For a `TODO.md` master plan, apply `/hitl-step`'s marker rules instead of a bare `[x]`: `[!]` if the work is blocked, `[-]` if the subgoal was descoped, `[~]` if real progress was made but the subgoal isn't finished. The summary should say what changed, not restate the subgoal.

**Commit and push**, substituting real names throughout:

```bash
git add docs/plan/feat-user-auth/DO.md docs/plan/DO.md
git commit -m "Record merge of feat/user-auth in plans (PR #123)"
git push
```

Pushing to the open PR's branch updates the PR, so this change is included in the merge and reviewable alongside the work it describes.

### 8. Suggest merge strategy

Based on the shape of the branch, recommend one of three strategies and explain the tradeoffs:

- **Merge commit** (`--merge`): Preserves all individual commits AND creates a merge commit that visibly records the PR as a unit. Best for branches with multiple meaningful commits (phased work, logical milestones). Default choice for most feature branches.
- **Rebase and merge** (`--rebase`): Replays commits linearly on top of main. Preserves granular commits without a merge commit. Linear history, but SHAs change. Good when you want commit-level traceability without merge-commit noise.
- **Squash and merge** (`--squash`): Collapses all branch commits into one. Best when the branch has messy WIP commits that aren't worth preserving individually, or the work is better represented as a single logical unit.

Heuristic:

- N commits, all meaningful → `--merge` (preferred) or `--rebase`
- N commits, mostly WIP/fixups → `--squash`
- 1 clean commit → any; `--squash` and `--rebase` produce identical history

Let the user choose. Default to `--merge` if they're unsure.

### 9. Merge the PR — CONFIRM FIRST

The two paths differ in what they clean up, and that difference is the reason step 9a exists. State which path you are taking before running it.

**MCP path (preferred).** Call `merge_pull_request` with `owner`, `repo`, `pullNumber`, and `merge_method` mapped from the strategy chosen in step 8 — `merge`, `squash`, or `rebase`.

**`gh` fallback.**

```bash
gh pr merge <pr-number> --<strategy> --delete-branch
```

`--delete-branch` removes the branch both locally and on GitHub, which completes the cleanup in one call. **On the `gh` path, skip step 9a.**

### 9a. Branch cleanup — MCP path only, CONFIRM FIRST

`merge_pull_request` takes no `delete_branch` parameter and deletes nothing: after an MCP merge, the branch survives **both** locally and on the remote. Left alone, the two paths would end in different repository states and the branch would linger as `[gone]`-less clutter.

Delete both explicitly, substituting the real branch name:

```bash
git push origin --delete <branch-name>
git checkout main
git branch -d <branch-name>
```

Use `-d`, not `-D` — it refuses to delete a branch whose commits are not reachable, which is exactly the safety check wanted right after a merge. If `-d` refuses, stop and investigate rather than forcing: it means the merge did not land what you think it did.

Alternatively, if the user prefers, `/clean-gone` sweeps the local branch once the remote one is gone — but the remote deletion above still has to happen first.

### 10. Sync local main

```bash
git checkout main
git pull
git log --oneline -5
```

Confirm the merge commit (or squashed/rebased commits) is present on local main.

### 11. Final report

Summarize:

- PR #N merged via `<strategy>` strategy
- New `main` tip: `<short-sha> <subject>`
- Branch `<name>` deleted locally and on remote
- Merged via **MCP** or **`gh`** — say which, and note any fallback that occurred and why
- Plan preserved on `main` at `docs/plan/<flattened-branch>/<DO|TODO>.md`, stamped `merged`
- PR URL for future reference

## Guidelines

- **Confirm before every write action**: push, file deletion, commit, PR create, merge, branch delete. State what will run, then wait for approval.
- **Read-only commands run freely**: `git status`, `git log`, `git diff`, `git branch`, `gh pr view`, `gh pr list`, and the read-only GitHub MCP tools (`pull_request_read`, `list_pull_requests`, `get_me`, `search_repositories`).
- **Announce every MCP→`gh` fallback**, naming the repo and the operation. See "GitHub access" above — a silent fallback defeats the point of a narrowly-scoped PAT.
- **Never use placeholders in actual commands** — always substitute the real branch name, PR number, title, etc.
- **If anything unexpected happens** (merge conflicts, auth errors, divergent branches, failed push), stop immediately and explain before proceeding.
- **Preserve user agency**: the user is learning. When choices exist (merge strategy, title wording, scope of body), present options with tradeoffs and let them decide.
- **Be concise**: don't over-explain standard operations. One or two sentences before each action is enough.
