# feat/smart-merge-mcp

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Revision-2 subgoals 1 and 2 — MCP-preferred GitHub access in `/smart-merge`, and branch-cleanup parity between the two paths.

## Tasks

- [ ] Add a "GitHub access" preamble to `/smart-merge` defining the rule once: prefer a GitHub MCP tool when one is present in the tool list, fall back to `gh` on **404 or 403**, and announce every fallback naming the repo and the operation.
- [ ] Convert the PR-read operations (`gh pr view` / `gh pr list`) to `pull_request_read` and `list_pull_requests`, with the `gh` equivalents as the stated fallback.
- [ ] Convert PR creation to `create_pull_request`, dropping the `/tmp/pr-body-<branch>.md` temp file on the MCP path since `body` is a string parameter. Keep the temp-file form in the `gh` fallback.
- [ ] Convert the merge to `merge_pull_request`, mapping the existing strategy choice onto `merge_method` (`merge` / `squash` / `rebase`).
- [ ] Add explicit post-merge branch cleanup for the MCP path — remote (`git push origin --delete`) and local — so it ends in the same state as `gh pr merge --delete-branch`. State which path was taken in the final report.
