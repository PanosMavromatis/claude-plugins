# fix/agents-docs-frontmatter

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Close the `/agents-docs-*` frontmatter gaps.

## Tasks

- [ ] `agents-docs-codex-init`: add the missing frontmatter block entirely — a `description` (it currently has none, so the picker shows it unlabelled) plus scoped `allowed-tools`.
- [ ] `agents-docs-init`: add `allowed-tools` covering what it performs — reads, `Write`/`Edit` for the `docs/agents/` sources. Deliberately omit `Bash(cat:*)` so the heredoc that replaces a user's `CLAUDE.md` keeps prompting.
- [ ] Correct the master plan's claim that `agents-docs-build` has a gap: it does not. Its body prohibits the operations the survey counted, so script-only is correct.
- [ ] Record in `CLAUDE.md` that the hook and `allowed-tools` are orthogonal layers — allow-listing `Write` does not weaken `protect-agent-docs.py`, because a `PreToolUse` hook fires regardless of the allow-list.
