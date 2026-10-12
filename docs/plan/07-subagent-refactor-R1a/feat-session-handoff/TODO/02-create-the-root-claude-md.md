# 02 — Create the root CLAUDE.md

**Goal**: [ ]
> **Note:** The plugin's `protect-agent-docs.py` hook blocks `CLAUDE.md` writes only when `docs/agents/core.md` exists, and this repository has no `docs/agents/`, so the write goes through.
> **Note:** Found during goal 01: §4.3 of the design targets `AGENTS.md` at the root and no `CLAUDE.md`, since Claude Code reads `AGENTS.md` only when no `CLAUDE.md` exists. Wherever that target is adopted, this `CLAUDE.md`'s handoff line and compact instructions must move into `AGENTS.md`; §4.4 lists as open whether Claude Code honours `# Compact instructions` there.

- [ ] Settle what happens to a handoff once it is read: deleted once the user confirms (the settled decision at `_TODO.md:30`–`31`), or archived, as `tmp/session-handoff-r1-r1a.md` was
- [ ] Confirm from Claude Code's documentation which section of the project's instruction file compaction reads, and whether auto-compaction reads it too
- [ ] `CLAUDE.md` at the repository root holds the one conditional line: if `tmp/session-handoff.md` exists, read it before anything else, and delete or archive it, as settled above, once the user confirms
- [ ] It holds a `# Compact instructions` section with §4.4's Drop list and Say-where convention
