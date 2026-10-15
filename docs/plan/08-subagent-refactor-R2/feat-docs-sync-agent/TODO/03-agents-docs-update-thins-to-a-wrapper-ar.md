# 03 — /agents-docs-update thins to a wrapper around docs-sync

**Goal**: [ ]

- [ ] Before the wrapper is written, whether a command's `allowed-tools` grant reaches the subagent it spawns is measured headless in default permission mode, for a write the agent needs (an `Edit`, `git add`) and for one it must never make (`git commit` under a command that grants it); the wrapper relies on the first or says which allow rules a user needs, and the second is shown to be refused, or is stopped by a hook, before `/smart-commit` spawns the agent
- [ ] `commands/agents-docs-update.md` spawns `docs-sync` and reports what it staged, carries no routing of its own, and describes the §4.3 layout, not the dispatcher's
- [ ] If goal 01 found that hooks do not fire inside a subagent, the command re-runs `check-agents-md.sh` after the agent returns (§8)
