# 02 — agents/docs-sync.md does /agents-docs-update's work

**Goal**: [ ]

- [ ] `agents/docs-sync.md` carries §4.1's row and conventions, §4.3's routing rule, a rebuild of `AGENTS.override.md` only when a `codex-review/AGENTS.md` changed, and `memory: project` (D-N7)
- [ ] It passes `validate-agent.sh` and the `plugin-dev:plugin-validator` agent, and its `tools:` holds no `git commit`, `git push`, `git rm`, `gh pr merge` or `git branch -d`
- [ ] The directory the harness uses for the agent's memory is recorded, and `.claude/agent-memory/` is committed
