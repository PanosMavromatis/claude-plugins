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
    > **Note:** Correction, 2026-10-10: the plugin's `CLAUDE.md` ("Scoped `allowed-tools`:
    > additive yes, destructive no") documents `git rm`, `git branch -d`, `gh pr merge` and
    > `git push origin --delete` as deliberate gates. It also explains that `/smart-merge`
    > cannot allow `git push`, because that prefix also covers `--delete`. Only
    > `git pull --prune` is undocumented. The first Q&A above was answered on the opposite
    > premise, so it is asked again when that subgoal is worked.
- [x] `/new-branch` marks the master-plan subgoal it executes `[~]`
  > **Note:** Raised by the user, 2026-10-10: no R1 master-plan item went `[~]` when its
  > branch started. It is unrelated to `Grep`. Neither the installed 0.9.0 nor the working
  > tree told `/new-branch` to flip the item, and none of the four R1 setup commits did.
  > The one `[~]` in the master plan's history came from `/hitl-step` working it directly
  > in R0. `/hitl-step` does flip its goal to `[~]` at the start (this branch's goal 1 did),
  > but the goal reaches `[x]` before the checkpoint commit, so `[~]` never lands in a
  > commit. That is the design, not a defect. `/step`'s `DO.md` model has no `[~]`.
  - [x] `/new-branch` flips the `subgoal:` line from `[ ]` to `[~]` when the model is
        `TODO.md`. `propose-branch-plan.sh` already reports that line, so no script changes.
  - [x] The e2e grader expects the flip on a `TODO.md` master plan and forbids it on a
        `DO.md` one
    > **Note:** The first draft took the backlink's line (the block end, 10) for the item's
    > (9). A scratchpad test on fresh fixtures caught it. The check now compares the branch's
    > master plan whole against `main`'s with the expected edits applied, and 6 of 6 cases
    > grade right: correct edits pass, while a backlink-only `TODO.md` edit and a flipped
    > `DO.md` fail.
  - [x] This repository's master plan marks the `fix/disallowed-tool-steps` subgoal `[~]`
  - [-] Re-run e2e `e1`, `e3` and `e4`
    > **Deferred:** to the Verify goal, where the user runs them.
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
- [ ] Verify: the three script suites pass, per-goal-e2e `e4` passes Step 6, and `e1`, `e3` and `e4` pass the master-plan `[~]` check (the user runs them)
