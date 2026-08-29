# feat/smart-merge-mcp

**Created**: 2026-08-29
**Base**: main at 902b195
**Status**: active

## Purpose

Rework `/smart-merge` so GitHub operations prefer the GitHub MCP server when it is
available, falling back to `gh` on 404 or 403 with the fallback announced. Covers
master-plan subgoals 1 and 2 of revision 2 — the MCP path and the branch-cleanup
parity it requires. These were folded into one branch because subgoal 1 alone would
land a merge path that leaves orphaned local and remote branches.

## Scope

- `/smart-merge` steps 1, 6, 8, 9: PR read, PR create, merge, post-merge cleanup.
- Announce-on-fallback rule, worded so recurrence reads as a signal to widen the PAT.
- Both paths (MCP and `gh`) must converge on the same repository end state.

Out of scope: pre-merge CI checks (revision-2 subgoal 3), `allowed-tools` resolution
(subgoal 4), docs (subgoal 5).

## Context

- Settled decisions and probe findings: `docs/plan/DO.md`, "GitHub access — settled
  decisions (revision 2)".
- Probed live on 2026-08-29: fine-grained PAT returns 404 (not 403) for repos outside
  its selection; `merge_pull_request` has no `delete_branch` parameter;
  `create_pull_request` takes `body` as a string; tool prefix here is
  `mcp__plugin_github_github__`, which is installation-dependent.
- `gh` is separately authenticated with full `repo` scope and acts as break-glass.

## Notes

- 2026-08-29: branch created. First branch to exercise the two-tier plan convention
  end to end; the convention itself has never been run.
