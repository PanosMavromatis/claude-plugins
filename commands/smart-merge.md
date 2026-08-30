---
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch -v:*), Bash(git rev-parse:*), Bash(git fetch:*), Bash(gh pr view:*), Bash(gh pr list:*), Bash(gh pr checks:*), Bash(gh pr create:*), Bash(git add:*), Bash(git commit:*), Bash(git checkout main:*), Read, Write, Edit, Glob, Grep
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

**Branch plan.** Flatten the branch name's `/` to `-` to get the **plan name** (branch `feat/user-auth` → `feat-user-auth`), then find the directory of that name *wherever* it sits under `docs/plan/`: check `docs/plan/<plan-name>/` first — the flat location `/new-branch` creates, and the answer in nearly every case — and only if that misses, glob `docs/plan/**/<plan-name>/`. Read whichever of `DO.md` or `TODO.md` it contains — the completed items and their `> **Q:** / > **A:**` logs record how the work actually went, which is useful input for the PR body's Summary.

Resolve by name rather than by a fixed path because the layout beneath `docs/plan/` is deliberately unconstrained: plans may be regrouped into milestone or component directories with `git mv`. A path-based check would report a moved plan as absent, and this command would then skip the stamp in step 7 — leaving a merged plan marked `active` forever. **Note the resolved path**; steps 3, 4 and 7 all refer back to it.

Unlike the branch doc, **the plan is not deleted at merge.** It lands on `main` as the durable record; step 7 only stamps it.

**Warn on unfinished items.** If the plan still has items in `[ ]`, `[~]`, or `[!]`, list them and say so plainly:

> The plan for this branch has N unfinished items: <list>. Merging is fine — the plan survives on `main` and you can keep working it — but flagging in case something was meant to land in this PR.

This is a **warning, not a gate**. Do not block the merge; the user may be deliberately landing partial work, and nothing is lost either way.

If neither file exists, note this and proceed using only the commit log and diff as input.

### 3. Draft PR title and body

Based on the branch doc (if present), the commits in `main..HEAD`, and the diff stat:

- **Title**: one line, imperative mood, sentence case, ~50-72 chars, no trailing period. Describes the umbrella scope of the whole branch, not any single commit.
- **Body**: Markdown-formatted. Group commits thematically (not chronologically) under section headers. Include Summary, and sections for the major themes present (e.g., Implementation, Infrastructure, Documentation, Testing). Keep it scannable.
- **Plan pointer**: if a branch plan exists, end the body with a line naming it — `Plan: \`feat-user-auth\` under \`docs/plan/\`` (substituting the real directory name). The plan lands on `main` with this merge, so the record it points at is permanent.

  **Write the name, not the path.** A PR body cannot be meaningfully edited once the PR is merged, while plan *locations* are deliberately free — the filing sweep moves merged plans into revision directories. A path pointer is therefore correct only until the next sweep: the first one silently invalidated seven of them, including the pointer in the PR that performed the move. A name stays correct through every regrouping, and resolves the same way every command resolves a plan — search `docs/plan/` for a directory of that name. This is the identity-vs-location rule applied to records instead of lookups; do not "improve" it back into a path.

  Do **not** paste the plan's contents into the body: PR bodies cap at 65,536 characters, and the file itself is the record.

Present both to the user. Let them edit, replace, or approve. Do not proceed until approved.

### 4. Delete the branch doc — CONFIRM FIRST

Explain: the branch doc was a working artifact for this branch; deleting it now means it stays in the branch's history (recoverable via SHA) but won't pollute `main`.

**Only the branch doc is deleted.** Leave the branch plan directory resolved in step 2 alone, wherever it sits — it is meant to land on `main`.

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

**Stamp the branch plan.** Using the path resolved in step 2 — not a reconstructed one — rewrite its status line to record the merge:

```
**Status**: merged — PR #123 — 2026-08-29
```

`/step` and `/hitl-step` read this line to filter merged plans out of their disambiguation prompt. The value must begin with `merged` for that filter to see it.

**Update the master plan — locate first, do not read the whole file.** The master plan is the one file in this system that grows without bound: it accumulates every subgoal of every revision, each with its `> **Done:**` annotation. All this step needs from it is the one item backlinked to this branch. Find that item, then read only around it.

1. **Locate.** Use `Grep` for the pattern `> \*\*Branch:\*\* <branch-name>` in `docs/plan/DO.md` (or `TODO.md`), with line numbers on. Use the `Grep` tool rather than a shell `grep` — it is allow-listed here and a bash `grep` would prompt.
2. **Read a window.** `Read` the file with `offset` and `limit` set to a window around the hit — roughly 10 lines before and 15 after is ample, since a subgoal item plus its blockquotes runs a few lines. That window is what you edit.
3. **Edit in place.** Mark the item complete and append the `> **Done:**` line beneath the existing backlink.

```markdown
- [x] The master-plan subgoal this branch executed
  > **Branch:** feat/user-auth
  > **Done:** One-or-two-sentence summary of what landed — PR #123
```

**Follow the sequence literally.** The instinct when told "update the master plan" is to read the file and edit it, and at today's sizes that works fine — which is exactly why it survives until it doesn't. Measured against synthetic master plans built from this repo's own subgoal blocks: at 250 subgoals the file is ~197 KB / ~55k tokens and **0.39%** of what a whole-file read loads is the block being edited; at ~500 subgoals it passes 2000 lines and a default read **truncates**. Locating first costs about 200 tokens and does not change with file size.

**Handle a missing or duplicated backlink explicitly — never silently.**

- **Exactly one hit** — the normal case. Proceed.
- **No hits** — say so, and say which of the two things it means: either this branch legitimately has no master-plan item (a standalone branch, or one created without `/new-branch`), in which case stamping the branch plan is the whole of this step; or the backlink was lost or misspelled, which is a defect worth knowing about. Do not silently skip: an unreported miss is indistinguishable from having had nothing to do, and it leaves a subgoal open forever with no trace of why. If the file is large enough that truncation is plausible, say that too rather than concluding the item is absent.
- **More than one hit** — a duplicated backlink. List the line numbers and ask which item to close. Do not update both.

For a `TODO.md` master plan, apply `/hitl-step`'s marker rules instead of a bare `[x]`: `[!]` if the work is blocked, `[-]` if the subgoal was descoped, `[~]` if real progress was made but the subgoal isn't finished. The summary should say what changed, not restate the subgoal.

**Commit and push**, substituting real names throughout. Stage the branch plan at **the path resolved in step 2**, not a reconstructed one — a plan that has been filed into a revision directory is not at `docs/plan/<name>/`:

```bash
git add docs/plan/rev-3/feat-user-auth/DO.md docs/plan/DO.md
git commit -m "Record merge of feat/user-auth in plans (PR #123)"
git push
```

The example shows a filed plan deliberately. A flat `docs/plan/feat-user-auth/DO.md` is the more common case, and writing that here invites reconstructing the path instead of reusing the resolved one — which fails silently, since `git add` on a non-existent path errors but a wrong-but-existing path would not.

Pushing to the open PR's branch updates the PR, so this change is included in the merge and reviewable alongside the work it describes.

### 8. Check CI status — before choosing a strategy

Checks run against the branch head, and step 7 just pushed to it, so this is the earliest point the result is meaningful. `/smart-merge` used to merge without ever looking at CI.

**MCP path (preferred).** `pull_request_read` with method `get_check_runs` for GitHub Actions and other check runs, and `get_status` for legacy commit statuses. A repo may use either or both.

`get_check_runs` **403s on any install backed by a fine-grained PAT** — GitHub does not offer a `Checks` permission for that token type at all, so this is a property of the credential, not a misconfiguration. Announce the fallback as normal, but do not tell the user to go and grant a permission that does not exist. `get_status` needs the **Commit statuses** permission, which *is* grantable.

**`gh` fallback.**

```bash
gh pr checks <pr-number>
```

**Count before you read state.** `get_status` returns `state: "pending"` with `total_count: 0` for a commit that has **no** statuses — "pending" there means "nothing has reported", not "something is running". Inspect `total_count` (and the length of `statuses` / `check_runs`) **first**: zero means *none configured*, whatever `state` says. Reading `state` first makes every CI-less repo look like it has work in flight, and the gate stops to wait for something that will never arrive. Keep this check; do not simplify it away.

**How to act on the result:**

- **No checks configured** — zero check runs *and* zero statuses → say so in one line and continue. Many repos have none, and a gate that nags on every merge is a gate that gets ignored.
- **All passing** → say so in one line and continue.
- **Any failing** → list each failing check by name, with its URL if available, and **require explicit confirmation before merging**. Do not merge over a red check on your own judgement; do not refuse either — the user may be merging a docs change past a flaky integration suite.
- **Any genuinely pending** — at least one check or status exists and has not concluded → name them and ask whether to wait or proceed. Do not poll in a loop.

If the MCP call fails with 404 or 403, announce and fall back per the "GitHub access" rule. If both paths fail for any other reason, say the CI state could not be determined and let the user decide — an undetermined result is not a passing one.

### 9. Suggest merge strategy

Based on the shape of the branch, recommend one of three strategies and explain the tradeoffs:

- **Merge commit** (`--merge`): Preserves all individual commits AND creates a merge commit that visibly records the PR as a unit. Best for branches with multiple meaningful commits (phased work, logical milestones). Default choice for most feature branches.
- **Rebase and merge** (`--rebase`): Replays commits linearly on top of main. Preserves granular commits without a merge commit. Linear history, but SHAs change. Good when you want commit-level traceability without merge-commit noise.
- **Squash and merge** (`--squash`): Collapses all branch commits into one. Best when the branch has messy WIP commits that aren't worth preserving individually, or the work is better represented as a single logical unit.

Heuristic:

- N commits, all meaningful → `--merge` (preferred) or `--rebase`
- N commits, mostly WIP/fixups → `--squash`
- 1 clean commit → any; `--squash` and `--rebase` produce identical history

Let the user choose. Default to `--merge` if they're unsure.

### 10. Merge the PR — CONFIRM FIRST

The two paths differ in what they clean up, and that difference is the reason steps 10a and 11a exist. State which path you are taking before running it.

**MCP path (preferred).** Call `merge_pull_request` with `owner`, `repo`, `pullNumber`, and `merge_method` mapped from the strategy chosen in step 9 — `merge`, `squash`, or `rebase`.

**`gh` fallback.**

```bash
gh pr merge <pr-number> --<strategy> --delete-branch
```

`--delete-branch` removes the branch both locally and on GitHub, which completes the cleanup in one call. **On the `gh` path, skip steps 10a and 11a.**

### 10a. Delete the remote branch — MCP path only, CONFIRM FIRST

`merge_pull_request` takes no `delete_branch` parameter and deletes nothing: after an MCP merge, the branch survives **both** locally and on the remote. Left alone, the two paths would end in different repository states.

Delete the remote branch now, substituting the real name:

```bash
git push origin --delete <branch-name>
```

The **local** branch is deleted in step 11a, after the sync — not here. Deleting it before local `main` has caught up would make `git branch -d` refuse for the wrong reason; see 11a.

### 11. Sync local main

```bash
git checkout main
git pull --prune
git log --oneline -5
```

Confirm the merge commit (or squashed/rebased commits) is present on local main.

**`--prune` is not optional.** A plain `git pull` leaves the deleted branch's remote-tracking ref (`origin/<branch>`) behind, so `git branch -r` keeps listing a branch that no longer exists. This matters beyond tidiness: `/clean-gone` finds branches by their upstream showing `[gone]`, and that marking only appears once the stale ref is pruned. Without this, the last command in the branch lifecycle silently has nothing to find.

### 11a. Delete the local branch — MCP path only, CONFIRM FIRST

Now that `main` carries the merge commit, the branch is reachable from `HEAD` and can be deleted safely:

```bash
git branch -d <branch-name>
```

Use `-d`, never `-D`. **What the refusal means depends on when you run it**, which is the whole reason this step sits after the sync rather than beside 10a:

- **After the sync (here)** — a refusal means the merge genuinely did not land what you think it did. Stop and investigate; do not force.
- **Before the sync** — a refusal means only that local `main` is stale. The branch *is* merged on the remote, but `HEAD` cannot see it yet, so `-d` refuses on every single MCP merge and the "stop and investigate" advice above would halt every cycle.

Running it here is what makes the refusal informative instead of routine.

Alternatively, if the user prefers, `/clean-gone` sweeps the local branch once the remote one is gone and the prune in step 11 has marked its upstream `[gone]`.

### 12. Final report

Summarize:

- PR #N merged via `<strategy>` strategy
- CI at merge time: all passing / N failing (merged anyway, confirmed) / none configured / undetermined
- New `main` tip: `<short-sha> <subject>`
- Branch `<name>` deleted locally and on remote — on the MCP path say that steps 10a and 11a did it; on the `gh` path, `--delete-branch`
- Merged via **MCP** or **`gh`** — say which, and note any fallback that occurred and why
- Plan preserved on `main` at the path resolved in step 2, stamped `merged`
- PR URL for future reference

## Guidelines

- **Confirm before every write action**: push, file deletion, commit, PR create, merge, branch delete. State what will run, then wait for approval.
- **Read-only commands run freely**: `git status`, `git log`, `git diff`, `git branch`, `gh pr view`, `gh pr list`, and the read-only GitHub MCP tools (`pull_request_read`, `list_pull_requests`, `get_me`, `search_repositories`).
- **Announce every MCP→`gh` fallback**, naming the repo and the operation. See "GitHub access" above — a silent fallback defeats the point of a narrowly-scoped PAT.
- **Never use placeholders in actual commands** — always substitute the real branch name, PR number, title, etc.
- **If anything unexpected happens** (merge conflicts, auth errors, divergent branches, failed push), stop immediately and explain before proceeding.
- **Preserve user agency**: the user is learning. When choices exist (merge strategy, title wording, scope of body), present options with tradeoffs and let them decide.
- **Be concise**: don't over-explain standard operations. One or two sentences before each action is enough.
