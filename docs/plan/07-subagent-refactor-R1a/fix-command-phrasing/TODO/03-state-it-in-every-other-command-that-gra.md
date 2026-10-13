# 03 — State it in every other command that grants git

**Goal**: [ ]

- [ ] `smart-merge`, `smart-commit`, `master-plan`, `close-revision`, `clean-gone`, `agents-docs-update`, `agents-docs-init` and `agents-docs-codex-init` each state that `git` runs as `git <subcommand>`, never `git -C <path>`, and that every command runs alone; those already stating the run-alone rule gain the `-C` half
- [ ] The plugin's `CLAUDE.md`, beside "Scoped `allowed-tools`", says a command granting `git` states the rule, and why `Bash(git -C:*)` is never granted: it would match a `git -C <path> push`
