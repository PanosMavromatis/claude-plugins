# fix/allowed-tools-sync

**Created**: 2026-08-29
**Base**: main at 534c2df
**Status**: active

## Purpose

Bring `allowed-tools` back in sync with what each command actually does, for
`/new-branch`, `/smart-merge` and `/clean-gone`. All three allow-list only
read-only diagnostics while performing writes — a standing violation of the repo's
own "keep `allowed-tools` and the prompt body in sync" rule.

## Scope

- Three commands' frontmatter, plus the `Scoped allowed-tools` convention bullet in
  `CLAUDE.md` recording the principle that decides what goes in.
- Record the `/agents-docs-*` gaps as a separate subgoal.

Out of scope: the `/agents-docs-*` trio. `agents-docs-init` and `-codex-init` carry
no `allowed-tools` at all and write via heredoc redirects that interact with the
`protect-agent-docs.py` hook — that needs its own thought, not a ride-along.

## Context

- **Principle settled**: additive writes are allow-listed, destructive ones are not.
  `git push` of a feature branch only adds; `gh pr merge`, `git push origin --delete`,
  `git branch -d`/`-D` and `git worktree remove` remove or are irreversible, and keep
  prompting as a second gate behind each command's own CONFIRM FIRST prose.
- This keeps `/smart-commit` — which already allow-lists `git push`, `git commit` and
  `git tag` — consistent with the rule rather than an exception to it.
- **MCP tool names stay off the allow-list.** They are `mcp__plugin_github_github__*`
  here, but that prefix encodes how the consumer installed the server; an entry that
  matches nothing fails silently, whereas a missing entry merely prompts.
- `/clean-gone` was the sharpest find: the most destructive command in the plugin,
  currently gated only by accident.

## Notes

- 2026-08-29: branch created. Fourth cycle.
