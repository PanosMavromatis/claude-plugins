# fix/agents-docs-frontmatter

**Created**: 2026-08-29
**Base**: main at 30687ed
**Status**: active

## Purpose

Close the frontmatter gaps in the `/agents-docs-*` commands — the last subgoal of
revision 2. The survey that recorded this subgoal was partly wrong, and the
correction is part of the work.

## Scope

- `agents-docs-codex-init`: has **no frontmatter block at all** — no `description`,
  so it appears unlabelled in the slash-command picker. Add the block.
- `agents-docs-init`: has a `description` but no `allowed-tools`.
- Correct the master plan: `agents-docs-build` was **already correct**. Its
  script-only `allowed-tools` is right because its body *prohibits* `git add`,
  `Write`/`Edit` on generated files, and source edits. The original survey counted
  those prohibitions as actions.

## Context

- The hook and `allowed-tools` are **orthogonal layers**. `protect-agent-docs.py`
  is a `PreToolUse` hook on `Write|Edit|MultiEdit` and fires regardless of what a
  command allow-lists, so allow-listing `Write` in these commands does not weaken
  protection of `CLAUDE.md`/`AGENTS.md`/`AGENTS.override.md` at all — the hook
  still blocks those paths once the sentinel exists.
- That is why `/agents-docs-init` writes dispatchers through a `cat <<'EOF' >`
  heredoc: Bash redirects are not matched by the hook. Documented at
  `commands/agents-docs-init.md:82`.
- `Bash(cat:*)` is therefore deliberately **not** added: that heredoc is what
  replaces a user's existing `CLAUDE.md`, which is the one genuinely destructive
  operation in the command and should keep prompting under the additive/destructive
  principle settled in PR #4.

## Notes

- 2026-08-29: branch created. Seventh cycle; closes revision 2.
