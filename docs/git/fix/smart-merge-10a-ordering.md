# fix/smart-merge-10a-ordering

**Created**: 2026-08-29
**Base**: main at 04d0dd2
**Status**: active

## Purpose

Fix the ordering bug in `/smart-merge` step 10a, found while executing PR #2:
`git branch -d` runs before local `main` is synced, so the merged branch is not
yet reachable from HEAD and `-d` refuses with "not fully merged" on **every** MCP
merge. The check itself is correct — the ordering makes it a false alarm, and the
step's own advice ("stop and investigate rather than forcing") would halt every cycle.

## Scope

- Split the cleanup: remote branch deletion stays at 10a (before the sync), local
  branch deletion moves after it, so `-d` evaluates against a current `main`.
- Rewrite the `-d`-over-`-D` rationale to describe what it actually catches.

Out of scope: `allowed-tools` resolution and the README/CLAUDE.md docs pass.

## Context

- Found by execution, not review — the second post-merge cleanup bug in two cycles
  (the first was the missing `--prune`, fixed in PR #2).
- `-d` refusing was the correct behaviour and is why the bug surfaced at all; `-D`
  would have deleted the branch silently and left the bug latent.
- The MCP path needs this because merge and cleanup are separate calls there;
  `gh pr merge --delete-branch` does both atomically and is unaffected.

## Notes

- 2026-08-29: branch created. Third cycle; second run of the MCP-preferring flow.
