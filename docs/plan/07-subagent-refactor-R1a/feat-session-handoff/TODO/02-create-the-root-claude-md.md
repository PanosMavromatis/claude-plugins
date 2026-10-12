# 02 — Create the root CLAUDE.md

**Goal**: [x]
> **Done:** The root `CLAUDE.md` has the next session read `tmp/session-handoff.md` first and archive it to `tmp/handoffs/` once the user confirms, and holds `# Compact instructions` (§4.4's Drop list and Say where), which Claude Code's docs say compaction reads, auto-compaction included.
> **Note:** The plugin's `protect-agent-docs.py` hook blocks `CLAUDE.md` writes only when `docs/agents/core.md` exists, and this repository has no `docs/agents/`, so the write goes through.
> **Note:** Found during goal 01: §4.3 of the design targets `AGENTS.md` at the root and no `CLAUDE.md`, since Claude Code reads `AGENTS.md` only when no `CLAUDE.md` exists. Wherever that target is adopted, this `CLAUDE.md`'s handoff line and compact instructions must move into `AGENTS.md`; §4.4 lists as open whether Claude Code honours `# Compact instructions` there.
> **Q:** What does the next session do with `tmp/session-handoff.md` once it has read it and the user confirms: archive it, dated (A), delete it, as settled at `_TODO.md:30`–`31` (B), or ask each time (C)?
> **A:** A. Move it to `tmp/handoffs/<YYYY-MM-DD>-<flattened-branch>.md`: gitignored, so it costs nothing, and R2 keeps examples to measure reorientation against after the transcripts expire.

- [x] Settle what happens to a handoff once it is read: deleted once the user confirms (the settled decision at `_TODO.md:30`–`31`), or archived, as `tmp/session-handoff-r1-r1a.md` was
  > **Note:** Recorded as a dated settled decision in R1a's `_TODO.md`, amending `:30`–`31`; subgoal 2's text there now says archive.
- [x] Confirm from Claude Code's documentation which section of the project's instruction file compaction reads, and whether auto-compaction reads it too
  > **Note:** Claude Code's docs (2026-10-12): the costs page gives the heading as `# Compact instructions` in the project-root `CLAUDE.md`; how-claude-code-works names a "Compact Instructions" section under "When context fills up", its account of automatic compaction, and context-window says the automatic pass "works the same way as the `/compact` step", so auto-compaction reads it, though no page says so in one sentence. context-window's "What survives compaction" table re-injects the project-root `CLAUDE.md` from disk, so the handoff line survives compaction too; the table names no `AGENTS.md`.
- [x] `CLAUDE.md` at the repository root holds the one conditional line: if `tmp/session-handoff.md` exists, read it before anything else, and delete or archive it, as settled above, once the user confirms
  > **Note:** One paragraph under `# Session handoff`: read it whole first, say what was taken from it, and on the user's confirmation `mkdir -p tmp/handoffs` and `mv` it to `tmp/handoffs/<YYYY-MM-DD>-<branch>.md`, the date from its `**Written**:` line and the branch from its title, as goal 01's template writes them.
- [x] It holds a `# Compact instructions` section with §4.4's Drop list and Say-where convention
  > **Note:** §4.4's Drop list, with skills beside commands, and a Say-where line that keeps the plan and goal-file paths `/session-handoff` reads from context (goal 01's Q&A). No static Keep: in-flight Keep is what remains for `/smart-compact`, and R2 measures it against this plain baseline. The file is 1014 bytes, loaded into every session.
