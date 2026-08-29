# fix/allowed-tools-sync

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Resolve the `allowed-tools` drift, extended to `/clean-gone`.

## Tasks

- [x] `/new-branch`: add the additive writes it performs — `Write`, `Bash(git checkout -b:*)`, `Bash(git add:*)`, `Bash(git commit:*)`.
  > **Done:** Added `Bash(git checkout -b:*)`, `Bash(git add:*)`, `Bash(git commit:*)`, `Read`, `Write`, `Glob`, `Grep`.
- [x] `/smart-merge`: add `Write`, `Edit`, `Bash(git add:*)`, `Bash(git commit:*)`, `Bash(git rm:*)`, `Bash(git push:*)`, `Bash(gh pr create:*)`, `Bash(gh pr checks:*)`. Leave `gh pr merge`, `git push origin --delete` and `git branch -d` off so they prompt. Do not add MCP tool names.
  > **Done:** Added `git fetch`, `gh pr checks`, `gh pr create`, `git add`, `git commit`, `git checkout main`, plus `Read`/`Write`/`Edit`/`Glob`/`Grep`. **`Bash(git push:*)` was added and then removed** — it is a prefix pattern that also matches `git push origin --delete`, the destructive op the principle says must prompt. No pattern admits the additive push while excluding the deleting one, so push stays off here. `git rm` likewise off. No MCP names.
- [x] `/clean-gone`: leave `git branch -D` and `git worktree remove` off deliberately, and add a comment in the body making that explicit so a future editor does not "fix" it by adding them.
  > **Done:** Added a Guidelines bullet stating the omission is deliberate, with the reason: these are the two irreversible ops, the prompt is a second gate, and `Bash(git branch:*)` would authorize `-D` on any branch.
- [x] Record the principle in `CLAUDE.md`'s `Scoped allowed-tools` bullet: additive writes allow-listed, destructive ones deliberately omitted, MCP names never hardcoded.
  > **Done:** Rewrote the `Scoped allowed-tools` bullet as "additive yes, destructive no", listing what is omitted on purpose and both traps — prefix breadth (with the `/smart-commit` vs `/smart-merge` asymmetry as the worked example) and never hardcoding MCP tool names.
- [x] Add a master-plan subgoal for the `/agents-docs-*` gaps found during the survey.
  > **Done:** Added, noting `agents-docs-init` and `-codex-init` have no `allowed-tools` at all and write via heredoc redirects — the path `protect-agent-docs.py` passes through deliberately, so it needs its own thought.
