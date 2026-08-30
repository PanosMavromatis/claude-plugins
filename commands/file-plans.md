---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/file-plans.sh:*), Bash(mkdir:*), Bash(git status:*), Bash(git log:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git checkout -b:*), Bash(git add:*), Bash(git commit:*), Read, Glob, Grep
description: File merged branch plans into their revision directories under docs/plan/.
---

# /file-plans

Branch plans are never deleted — they land on `main` as the durable record of how each subgoal was executed — so `docs/plan/` gains one flat directory per merged branch. This command sweeps them into revision directories, leaving the master plan and any in-flight plans at the top level.

**Nothing is being classified.** `/new-branch` writes each plan's `> **Branch:**` backlink beneath a specific `## Subgoals — revision <label>` heading, so a plan's revision was recorded when the branch was created. The bundled `scripts/file-plans.sh` reads it back. This is a lookup, not a judgement — which is why it can be automated at all.

## Workflow

### 1. Propose

Run the script. It is read-only: it prints proposed `git mv` commands and a count, and moves nothing.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/file-plans.sh
```

Show the user its output verbatim. Do not paraphrase the proposals — the paths are the thing being approved.

### 2. Explain the skips

The script reports two kinds of plan it cannot place. Both leave the plan flat, which is the safe outcome: a plan filed into the *wrong* revision is worse than one never filed, because the mistake becomes invisible once it is filed.

- **`no backlink`** — the master plan has no `> **Branch:**` line for this plan. Usually a branch created without `/new-branch`, or one whose subgoal was never recorded. If the user wants it filed, the fix is to add the backlink to the master plan under the right subgoal and re-run; do not offer to guess a revision.
- **`no revision label`** — the backlink exists but its enclosing heading is a bare `## Subgoals`, with no revision label to derive. Typically a plan predating the convention. Leave it, or the user can retitle the heading.

Say which skips appeared and why. A skip reported and understood is the point; a skip passed over in silence is the failure this command exists to avoid.

### 3. Branch — CONFIRM FIRST

The moves are a commit, and plans live on `main` where branch protection commonly forbids direct commits. If the current branch is `main`, propose a branch:

> I'll run `git checkout -b chore/file-plans` and make the moves there. Proceed?

Wait for approval. If the user is already on a working branch and wants the moves folded into it, that is fine — say which branch the commit will land on either way.

### 4. Execute — CONFIRM FIRST

Present the exact `git mv` commands from step 1 and ask for approval. On approval, run them **verbatim as printed** — do not reconstruct paths, and do not "tidy" a destination.

**Create the destination directory first.** `git mv src dest/name` fails outright when `dest/` does not exist (`fatal: renaming failed: No such file or directory`), and a revision opened by `/open-revision` has no directory until its first plan is filed. So for each distinct destination in the proposal:

```bash
mkdir -p docs/plan/<label>/
```

This is the normal case, not an edge case: every revision's *first* filing hits it.

`git mv` is deliberately **not** in this command's `allowed-tools`. That is not drift: the harness prompt is a second gate behind this confirmation, matching how `/clean-gone` and `/smart-merge` treat operations that move or remove things. Do not "fix" it by adding `Bash(git mv:*)`.

If any `git mv` fails, stop and report. Do not continue with the remaining moves — a partial sweep is harder to reason about than a failed one.

### 5. Commit — CONFIRM FIRST

```bash
git add -A
git commit -m "chore(plan): file merged plans into revision directories"
```

Nothing else needs updating, and that is worth stating in the report: every command finds a plan by its directory **name**, not its path, so moving a plan breaks no lookup. The one thing a move *does* break is a path written into an immutable record — which is why `/smart-merge` names the plan in the PR body rather than pointing at a path.

### 6. Report

- Plans filed, and into which revision directories
- Plans skipped, with the reason for each
- The resulting top level of `docs/plan/`
- The branch the commit landed on, and that it still needs a PR

## Guidelines

- **The script never moves anything.** If you find yourself wanting it to, that is the command's job, behind a confirmation.
- **Run the printed commands verbatim.** The script resolved those paths; reconstructing them reintroduces exactly the class of bug the name-based resolution was built to remove.
- **Never guess a revision.** Two cases are underivable by design, and both are reported. Guessing would produce a confidently misfiled plan, which nobody will notice.
- **Filing is optional.** A project that never runs this is fine — the layout beneath `docs/plan/` is unconstrained, and grouping by revision is one option among several. A monorepo might group by component instead, reading the component list from the `docs/agents/` tree.
