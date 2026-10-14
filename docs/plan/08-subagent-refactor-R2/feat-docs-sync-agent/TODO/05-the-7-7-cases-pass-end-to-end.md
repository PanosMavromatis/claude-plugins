# 05 — The §7.7 cases pass end to end

**Goal**: [ ]

- [ ] A staged change to a CLI flag edits `AGENTS.md` and commits nothing, and a staged diff of pure history edits `_history/` and leaves `AGENTS.md` alone
- [ ] A `codex-review/` change rebuilds `AGENTS.override.md`, and an `Edit` of `AGENTS.override.md` from inside the agent is blocked by the hook
- [ ] `/smart-commit` with a kernel staged runs `docs-sync` and then the `dp-compile` gate, whose output names the kernel
