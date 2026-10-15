# 04 — Remove /agents-docs-init and /agents-docs-codex-init

**Goal**: [ ]

- [ ] `commands/agents-docs-init.md` and `commands/agents-docs-codex-init.md` are deleted.
- [ ] The plugin's `README.md`, its `CLAUDE.md`, and the command list in `_meta/plugin-conflict-report.md` name `/agents-docs-migrate` in their place, and none of them still says the init commands write a layout the build refuses.
- [ ] `grep -rE "agents-docs-(codex-)?init" plugins/` finds either command only where its removal is recorded.
