# feat/smart-merge-mcp

**Status**: merged — PR #1 — 2026-08-29
**Created**: 2026-08-29
**Subgoal**: Revision-2 subgoals 1 and 2 — MCP-preferred GitHub access in `/smart-merge`, and branch-cleanup parity between the two paths.

## Tasks

- [x] Add a "GitHub access" preamble to `/smart-merge` defining the rule once: prefer a GitHub MCP tool when one is present in the tool list, fall back to `gh` on **404 or 403**, and announce every fallback naming the repo and the operation.
  > **Done:** New section before `## Workflow` stating the rule once: prefer MCP when a tool is present, fall back on 404 **or** 403, announce naming repo and operation, never fall back mid-operation, and local git always uses the shell. Includes the three-call diagnostic for an ambiguous 404.
- [x] Convert the PR-read operations (`gh pr view` / `gh pr list`) to `pull_request_read` and `list_pull_requests`, with the `gh` equivalents as the stated fallback.
  > **Done:** Step 1 now points PR-existence checks at `list_pull_requests` / `pull_request_read` with `gh pr list` / `gh pr view` as fallback; Guidelines updated to run the read-only MCP tools freely.
- [x] Convert PR creation to `create_pull_request`, dropping the `/tmp/pr-body-<branch>.md` temp file on the MCP path since `body` is a string parameter. Keep the temp-file form in the `gh` fallback.
  > **Done:** Step 6 split into MCP path (`create_pull_request`, body as a string — temp file gone) and `gh` fallback (temp file retained, since `--body-file` still needs it). Reports which path created the PR.
- [x] Convert the merge to `merge_pull_request`, mapping the existing strategy choice onto `merge_method` (`merge` / `squash` / `rebase`).
  > **Done:** Step 9 split into both paths, with the strategy from step 8 mapped onto `merge_method`. The `gh` path explicitly skips 9a because `--delete-branch` already cleans up.
- [x] Add explicit post-merge branch cleanup for the MCP path — remote (`git push origin --delete`) and local — so it ends in the same state as `gh pr merge --delete-branch`. State which path was taken in the final report.
  > **Done:** New step 9a, MCP-path only: deletes the remote branch then the local one with `git branch -d` (not `-D`, so an unmerged branch refuses rather than vanishes). Step 11 now reports which path was used and any fallback that occurred.
