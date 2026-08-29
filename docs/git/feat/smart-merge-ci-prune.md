# feat/smart-merge-ci-prune

**Created**: 2026-08-29
**Base**: main at 0b25a54
**Status**: active

## Purpose

Two changes to `/smart-merge`, both concerning the merge itself: add a pre-merge CI
gate (revision-2 subgoal 3 of the plan list), and fix the prune gap that leaves a
stale `origin/<branch>` after a `--delete-branch` merge (subgoal folded in per the
granularity discussion — too small to justify its own branch).

This is also the first cycle to run the **new** MCP-preferring `/smart-merge`
end to end. PR #1 was merged entirely via `gh`, so the MCP write path
(`create_pull_request`, `merge_pull_request`, step 9a cleanup) has never executed.

## Scope

- New pre-merge step: `pull_request_read` with `get_check_runs` / `get_status`,
  `gh pr checks` as fallback, confirm before merging over failing checks.
- Step 10: `git fetch --prune` so `/clean-gone` can see `[gone]` upstreams.
- Carries an uncommitted master-plan edit from `main` (the prune subgoal itself).

Out of scope: `allowed-tools` resolution, and the README/CLAUDE.md docs pass — both
remain separate subgoals.

## Context

- Prune gap found by execution, not review, while merging PR #1: `git pull` does not
  prune, and `/clean-gone` detects branches by their upstream showing `[gone]`, which
  only appears after a prune.
- `/smart-merge` currently merges without looking at CI at all.
- This repo has no CI workflows yet, so the new gate will exercise its
  "no checks configured" path rather than a real failure.

## Notes

- 2026-08-29: branch created from `main` at the PR #1 merge commit.
