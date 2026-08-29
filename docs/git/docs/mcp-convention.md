# docs/mcp-convention

**Created**: 2026-08-29
**Base**: main at bb4bf0c
**Status**: active

## Purpose

Document the MCP-preferred GitHub access convention in `README.md` and `CLAUDE.md`.
Four cycles have shipped behaviour that neither document mentions: `/smart-merge`
prefers the GitHub MCP server, announces its fallbacks, gates on CI, and splits its
branch cleanup around the sync. Both docs still describe it as merging "via
`gh pr merge`" with no CI step.

Last subgoal of revision 2.

## Scope

- `README.md`: refresh the `/smart-merge` command-table row; add a conventions
  bullet for MCP-preferred access and the announce-on-fallback rule.
- `CLAUDE.md`: new section on GitHub access, and refresh the `/smart-merge` bullet
  under "How the commands compose".

Out of scope: the `/agents-docs-*` `allowed-tools` gaps — a separate subgoal.
The `allowed-tools` principle already landed in `CLAUDE.md` in PR #4.

## Context

- The convention and its findings live in `docs/plan/DO.md` under "GitHub access —
  settled decisions (revision 2)"; this pass moves the durable parts into the docs
  proper, where a reader looks first.
- Everything documented here was established by execution across PRs #1-#4, not by
  design discussion: the 404-vs-403 distinction, `merge_pull_request` not deleting
  branches, and the cleanup ordering.

## Notes

- 2026-08-29: branch created. Fifth cycle; closes revision 2.
