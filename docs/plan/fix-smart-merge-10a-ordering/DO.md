# fix/smart-merge-10a-ordering

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Fix step 10a's ordering so `git branch -d` runs against a synced `main`.

## Tasks

- [ ] Split the MCP-path cleanup in two: step 10a deletes the remote branch only (before the sync), and a new step after the sync deletes the local branch. Both remain MCP-path only and skipped on the `gh` path.
- [ ] Rewrite the `-d`-over-`-D` rationale to say what the refusal actually distinguishes: with a synced `main`, a refusal means the merge did not land; before the sync it only means the local view is stale. Note that this is why the local delete must follow the pull.
- [ ] Verify step numbering and every cross-reference after the split, and make sure the final report still names which cleanup path ran.
