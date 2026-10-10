# fix/disallowed-tool-steps

**Status**: active
**Created**: 2026-10-10
**Subgoal**: revision 06-subagent-refactor-R1 — steps that rely on a tool their command does not allow

## Tasks

- [x] Measure which steps rely on a tool their command does not allow
  > **Q:** `/smart-merge`'s routine writes aren't in its `allowed-tools`, so each one prompts
  > behind its own CONFIRM FIRST. How should this branch treat them?
  > **A:** Allow the routine ones. Keep `git push origin --delete` as a documented second
  > gate, the way `/clean-gone` keeps `git branch -D`.
  > **Q:** `SlashCommand` is a dead tool name. Fix it here?
  > **A:** Yes: `Skill(workflow-claude:<name>)` in the allow-lists and the body text, plus the
  > grant `/agents-docs-codex-init` lacks.
  > **Q:** `/agents-docs-init` writes `CLAUDE.md` with a `cat` heredoc, which prompts. How
  > should it be treated?
  > **A:** Document the prompt as a deliberate gate, as `/file-plans` does for `git mv`.
  - [x] When `Grep` and `Glob` are missing from a session whose `allowed-tools` grants them
    > **Note:** Measured 2026-10-10 from every transcript under `~/.claude/projects` and the
    > e2e `init` tool lists. It is not intermittent. Since 2.1.117, native macOS and Linux
    > builds replace both tools with embedded `ugrep` and `bfs` behind shell `grep` and
    > `find`. Windows and npm installs keep them. A main session on a native build never has
    > them, interactive or `-p`: all 9 e2e `init` lists lack both, and the one 2.1.296 main
    > session that called `Grep` got "No such tool available". `allowed-tools` cannot bring
    > them back. Only an explicit tool list can: `--tools` (since 2.1.162), the Agent SDK
    > (9 of 20 `sdk-py` sessions on 2.1.295–296 called one), or a subagent's `tools` (101
    > of 131 trial subagents on 2.1.295 called `Grep`).
    > **Note:** The fallback costs a failed call or an improvised substitute, not a prompt:
    > shell `grep` ran unprompted in default-mode headless sessions (e4-step, both runs).
    > `awk` is what prompts, and it was refused in both runs. A rewrite can't simply say
    > "shell `grep`", because builds that keep `Grep` may have no shell `grep` (Windows).
  - [x] Every such step across the 11 command files, including any tool gap besides `Grep`, `Glob` and the legacy Step 6 `awk`
    > **Note:** Inventory of the working tree, 2026-10-10. A scratchpad scanner found the
    > candidates and every hit was vetted by hand: 11 real gaps, and the rest were prose.
    > **A, `Grep`/`Glob` named on a build without them:** `/close-revision`:73; `/step`:36
    > and `/hitl-step`:50; `/step`:64 and `/hitl-step`:78; `/hitl-step`:142 (Step 3a, not
    > in the plan); `/hitl-step`:237; `/step`:179 and `/hitl-step`:265; `/smart-merge`:164
    > (deferred). **B, a shell command not in `allowed-tools`:** `/hitl-step`:281's `awk`;
    > `/smart-merge`'s `git rm`, `git push`, `git push origin --delete`, `git pull --prune`
    > and `git branch -d`, and its `gh` fallback's `/tmp` writes and `gh pr merge`; and
    > `/agents-docs-init`:83's heredoc. **C, a dead tool name:** `SlashCommand`, in
    > `/smart-commit`, `/agents-docs-update` and `/agents-docs-codex-init`. No transcript
    > ever called it: all 72 nested calls went through `Skill`, and all succeeded. Excluded
    > because they are deliberate and documented: `/clean-gone`'s `git branch -D` and
    > `git worktree remove`, and `/file-plans`' `git mv`. The 4 `dp-compile` commands
    > declare no `allowed-tools`.
- [ ] `check-plan-index.sh` reports a legacy plan's open items, and Step 6 runs it for both layouts
- [ ] Rewrite the remaining steps onto tools their command allows
  - [ ] `/close-revision`'s pointer check
  - [ ] `/step` and `/hitl-step`: the out-of-order lookup, Step 4's subgoal check, Step 5's re-Grep, the investigation paragraph
  - [ ] `/hitl-step` Step 3a's research list
  - [ ] `/smart-merge` allows its routine writes, with patterns that don't also cover
        `git push origin --delete`, which stays a documented second gate
  - [ ] `SlashCommand` becomes `Skill(workflow-claude:<name>)` in `/smart-commit`,
        `/agents-docs-update` and `/agents-docs-codex-init`
  - [ ] `/agents-docs-init`'s heredoc is documented as a deliberate gate
  - [-] `/smart-merge` step 7
    > **Deferred:** rewritten once, through `scripts/locate-plan.sh`, by the next R1 subgoal.
- [ ] Verify: the three script suites pass, and per-goal-e2e `e4` passes Step 6 (the user runs it)
