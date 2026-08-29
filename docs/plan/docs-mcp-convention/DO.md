# docs/mcp-convention

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Update `README.md` and `CLAUDE.md` for the MCP-preferred convention.

## Tasks

- [x] `README.md`: refresh the `/smart-merge` command-table row — it still says "merges via `gh pr merge`" with no mention of the MCP path or the CI gate.
  > **Done:** Row now says it gates on CI and prefers the GitHub MCP server, falling back to `gh`, instead of "merges via `gh pr merge`".
- [x] `README.md`: add a conventions bullet covering MCP-preferred access, the 404-or-403 fallback trigger, and why every fallback is announced.
  > **Done:** Two bullets added rather than one: the fallback rule (404-or-403, announced, and why a silent fallback defeats a narrow PAT), and the cleanup divergence between the two merge paths.
- [x] `CLAUDE.md`: add a "GitHub access" section — the fallback rule, the `merge_pull_request` cleanup divergence and why steps 10a/11a sit where they do, and the tool-name portability constraint.
  > **Done:** New section between the agent-docs system and the `commit-commands` coexistence notes. Covers the 404/403 split with the real cases that produced each, the announce rule, the 10a/11/11a ordering and why `-d` before the sync misfires, why `--prune` is required by `/clean-gone`, and the tool-name portability constraint.
- [x] `CLAUDE.md`: refresh the `/smart-merge` bullet under "How the commands compose" to mention the CI gate and the MCP preference.
  > **Done:** Bullet now mentions the CI gate and the MCP preference, and points at the new section.
- [x] Sweep both files for any remaining claim that GitHub work goes through `gh`.
  > **Done:** Found one: the plan-convention section pinned the merge-time write window to "between `gh pr create` and `gh pr merge`", which is mechanism-specific and stale now that either path may create the PR. Reworded neutrally with a parenthetical saying why.
