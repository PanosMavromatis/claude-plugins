# fix/agents-docs-frontmatter

**Status**: merged — PR #7 — 2026-08-29
**Created**: 2026-08-29
**Subgoal**: Close the `/agents-docs-*` frontmatter gaps.

## Tasks

- [x] `agents-docs-codex-init`: add the missing frontmatter block entirely — a `description` (it currently has none, so the picker shows it unlabelled) plus scoped `allowed-tools`.
  > **Done:** Added the whole block — it had none, so the picker showed it unlabelled. `description` plus scoped `allowed-tools` (reads, `Write`, `Edit`, `Glob`, `Grep`, `git status`, `ls`, `find`).
- [x] `agents-docs-init`: add `allowed-tools` covering what it performs — reads, `Write`/`Edit` for the `docs/agents/` sources. Deliberately omit `Bash(cat:*)` so the heredoc that replaces a user's `CLAUDE.md` keeps prompting.
  > **Done:** Added the same set alongside the existing `description`. `Bash(cat:*)` deliberately omitted, and a note recorded next to the heredoc explanation saying so, in the same style as `/clean-gone`.
- [x] Correct the master plan's claim that `agents-docs-build` has a gap: it does not. Its body prohibits the operations the survey counted, so script-only is correct.
  > **Done:** Struck through in the subgoal text with the correction inline: the body prohibits `git add`, `Write`/`Edit` on generated files, and source edits, so script-only is right. Also stated in `CLAUDE.md` so the wrong conclusion is not reached again.
- [x] Record in `CLAUDE.md` that the hook and `allowed-tools` are orthogonal layers — allow-listing `Write` does not weaken `protect-agent-docs.py`, because a `PreToolUse` hook fires regardless of the allow-list.
  > **Done:** New paragraph in the agent-docs section: a `PreToolUse` hook fires regardless of the allow-list, so allow-listing `Write` cannot weaken protection and the allow-list cannot re-enable a blocked write. The two layers are reasoned about separately.
