# 03a — A hook stops docs-sync committing or pushing

**Goal**: [ ]
> **Note:** Split from goal 03's first subgoal: run `a1` showed a command's grant reaches the subagents it spawns, `git commit` included, so under `/smart-commit`, which grants `git commit` and `git push`, only `docs-sync`'s instructions would stop it. Goal 04 must not let `/smart-commit` spawn the agent before this goal is done.

- [ ] Whether a `PreToolUse` hook's input names the subagent that made a call is checked in the docs and confirmed by one headless case
- [ ] A hook refuses `git commit`, `git push`, `git rm`, `git branch -d` and `gh pr merge` when they come from `docs-sync`, and lets the main session's through, tested by a suite and by a headless case under a command that grants them
