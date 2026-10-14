# 03 — protect-agent-docs.py protects AGENTS.override.md only

**Goal**: [ ]

- [ ] With the sentinel `docs/agents/codex-review/AGENTS.md` present, a `Write` or `Edit` of an `AGENTS.override.md`, at the root or in a component, is blocked; without it, it passes
- [ ] `AGENTS.md` and `CLAUDE.md` pass at every path, and the hook's presence check for `CLAUDE.md` is gone
