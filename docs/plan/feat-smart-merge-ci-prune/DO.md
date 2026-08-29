# feat/smart-merge-ci-prune

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Revision-2 subgoal "pre-merge CI check", with the `git fetch --prune` fix folded in.

## Tasks

- [ ] Fix `/smart-merge` step 10 to prune: replace the bare `git pull` with a form that removes stale remote-tracking refs, and say in the step why it matters — `/clean-gone` finds branches by their upstream showing `[gone]`, which only appears after a prune.
- [ ] Add a pre-merge CI gate as a new step before the merge: MCP `pull_request_read` with `get_check_runs` (and `get_status` for legacy commit statuses), falling back to `gh pr checks` per the GitHub-access rule.
- [ ] Define the gate's behaviour precisely: report each failing or pending check by name, require explicit confirmation before merging over a failure, and pass through silently when no checks are configured — many repos have none, and a gate that nags on every merge gets ignored.
- [ ] Renumber the steps that follow the new gate, and add the CI result to the final report.
