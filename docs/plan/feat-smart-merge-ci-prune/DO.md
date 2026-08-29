# feat/smart-merge-ci-prune

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Revision-2 subgoal "pre-merge CI check", with the `git fetch --prune` fix folded in.

## Tasks

- [x] Fix `/smart-merge` step 10 to prune: replace the bare `git pull` with a form that removes stale remote-tracking refs, and say in the step why it matters — `/clean-gone` finds branches by their upstream showing `[gone]`, which only appears after a prune.
  > **Done:** Step 10 (now 11) uses `git pull --prune`, with a paragraph explaining that `/clean-gone` depends on the `[gone]` marking a prune produces — without it the lifecycle's last command silently finds nothing.
- [x] Add a pre-merge CI gate as a new step before the merge: MCP `pull_request_read` with `get_check_runs` (and `get_status` for legacy commit statuses), falling back to `gh pr checks` per the GitHub-access rule.
  > **Done:** New step 8, placed after step 7's push because checks run against the branch head and step 7 moves it. MCP `get_check_runs` plus `get_status` for legacy statuses; `gh pr checks` as the announced fallback.
- [x] Define the gate's behaviour precisely: report each failing or pending check by name, require explicit confirmation before merging over a failure, and pass through silently when no checks are configured — many repos have none, and a gate that nags on every merge gets ignored.
  > **Done:** Four outcomes spelled out: none configured → one line and continue; all passing → one line and continue; failing → name each and require explicit confirmation, neither auto-merging nor refusing; pending → name and ask, never poll. A both-paths-failed result is explicitly "undetermined", not "passing".
- [x] Renumber the steps that follow the new gate, and add the CI result to the final report.
  > **Done:** Steps 8-11 became 9-12 (9a → 10a); the three internal cross-references were updated and verified with a grep for stale ones. Final report gains a CI-at-merge-time line.
