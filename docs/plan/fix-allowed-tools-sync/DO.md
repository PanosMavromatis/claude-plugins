# fix/allowed-tools-sync

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Resolve the `allowed-tools` drift, extended to `/clean-gone`.

## Tasks

- [ ] `/new-branch`: add the additive writes it performs — `Write`, `Bash(git checkout -b:*)`, `Bash(git add:*)`, `Bash(git commit:*)`.
- [ ] `/smart-merge`: add `Write`, `Edit`, `Bash(git add:*)`, `Bash(git commit:*)`, `Bash(git rm:*)`, `Bash(git push:*)`, `Bash(gh pr create:*)`, `Bash(gh pr checks:*)`. Leave `gh pr merge`, `git push origin --delete` and `git branch -d` off so they prompt. Do not add MCP tool names.
- [ ] `/clean-gone`: leave `git branch -D` and `git worktree remove` off deliberately, and add a comment in the body making that explicit so a future editor does not "fix" it by adding them.
- [ ] Record the principle in `CLAUDE.md`'s `Scoped allowed-tools` bullet: additive writes allow-listed, destructive ones deliberately omitted, MCP names never hardcoded.
- [ ] Add a master-plan subgoal for the `/agents-docs-*` gaps found during the survey.
