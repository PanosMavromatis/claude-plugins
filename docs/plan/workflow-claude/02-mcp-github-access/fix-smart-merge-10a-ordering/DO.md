# fix/smart-merge-10a-ordering

**Status**: merged — PR #3 — 2026-08-29
**Created**: 2026-08-29
**Subgoal**: Fix step 10a's ordering so `git branch -d` runs against a synced `main`.

## Tasks

- [x] Split the MCP-path cleanup in two: step 10a deletes the remote branch only (before the sync), and a new step after the sync deletes the local branch. Both remain MCP-path only and skipped on the `gh` path.
  > **Done:** Step 10a now deletes only the remote branch; new step 11a, after the sync, deletes the local one. Both stay MCP-path only, and step 10 now says the `gh` path skips both.
- [x] Rewrite the `-d`-over-`-D` rationale to say what the refusal actually distinguishes: with a synced `main`, a refusal means the merge did not land; before the sync it only means the local view is stale. Note that this is why the local delete must follow the pull.
  > **Done:** Step 11a spells out that the refusal means different things before and after the sync — a genuinely unlanded merge after, merely a stale `HEAD` before — and that running it after the pull is what makes the refusal informative rather than routine.
- [x] Verify step numbering and every cross-reference after the split, and make sure the final report still names which cleanup path ran.
  > **Done:** Numbering now 10, 10a, 11, 11a, 12; both cross-references in step 10 updated and a grep confirmed no stale ones. Final report now names which mechanism did the branch deletion.
