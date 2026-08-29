# fix/ci-gate-empty-status

**Created**: 2026-08-29
**Base**: main at fc2f433
**Status**: active

## Purpose

Fix the CI gate's empty-status misclassification in `/smart-merge` step 8, and
document the `Checks` permission constraint in the same place.

GitHub's combined-status endpoint returns `state: "pending"` with `total_count: 0`
for a commit with no statuses — "pending" means "nothing has reported", not
"something is running". The gate reads `state` first, so on every repo without CI
the MCP path would announce phantom pending checks and stop to ask whether to wait
for something that will never arrive.

## Scope

Both open CI-gate subgoals, folded because they edit the same paragraph of the same
step and splitting them would mean two PRs touching identical lines:

- the `total_count` check before `state`;
- a note that `get_check_runs` 403s on any PAT-backed install by design.

Out of scope: the `/agents-docs-*` `allowed-tools` gaps.

## Context

- Found by granting the `Commit statuses` permission and re-running the call. The
  403 had masked the bug for four cycles — the fallback to `gh pr checks` reported
  "no checks reported" correctly, so nothing looked wrong.
- `Checks` is not offered for fine-grained PATs at all: absent from GitHub's
  permission dropdown where it would sort alphabetically, and still 403 after
  `Commit statuses` was granted and began working.
- `gh pr checks` is unaffected — it reports "no checks reported" correctly.

## Notes

- 2026-08-29: branch created. Sixth cycle. A permission fix exposing a latent bug in
  the path it unblocked.
