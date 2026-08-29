# docs/mcp-convention

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Update `README.md` and `CLAUDE.md` for the MCP-preferred convention.

## Tasks

- [ ] `README.md`: refresh the `/smart-merge` command-table row — it still says "merges via `gh pr merge`" with no mention of the MCP path or the CI gate.
- [ ] `README.md`: add a conventions bullet covering MCP-preferred access, the 404-or-403 fallback trigger, and why every fallback is announced.
- [ ] `CLAUDE.md`: add a "GitHub access" section — the fallback rule, the `merge_pull_request` cleanup divergence and why steps 10a/11a sit where they do, and the tool-name portability constraint.
- [ ] `CLAUDE.md`: refresh the `/smart-merge` bullet under "How the commands compose" to mention the CI gate and the MCP preference.
- [ ] Sweep both files for any remaining claim that GitHub work goes through `gh`.
