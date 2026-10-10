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
    > **Note:** A second correction: `/agents-docs-init`'s heredoc was documented as a
    > deliberate gate too, in the command itself. The scanner checked allow-lists against
    > the bodies but never read the rationale beside them, so class B overcounts. Only
    > `/hitl-step`'s `awk` and `/smart-merge`'s `git pull --prune` and `/tmp` heredoc were
    > real gaps.
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
- [x] `check-plan-index.sh` reports a legacy plan's open items, and Step 6 runs it for both layouts
  > **Q:** For a legacy plan, how should Step 6 know whether the just-completed section is
  > fully resolved?
  > **A:** Put the heading in `open:`. In a one-file plan, each line ends
  > `— under <## heading>`, and the 8 report keys stay as they are.
  > **Done:** A legacy plan now gets `result: clean`, with its open items at every indent,
  > each with the `## ` heading it sits under (`OPEN_AWK` in the library). A revisions
  > index stays an `error`, with a fix that points to the revision's plan. `/hitl-step`'s
  > Step 6 runs the script for both layouts, and the `awk` is gone. `/step`'s Step 6 check
  > now runs for both layouts too. The suite has 39 cases (7 new) and 24 mutants (6 new,
  > `c07` retargeted), all killed. The `locate-plan` and `propose-branch-plan` suites and
  > their mutants still pass. The e2e grader now checks that e4's Step 6 ran the script and
  > no `awk`.
- [x] Rewrite the remaining steps onto tools their command allows
  > **Done:** No command step names `Grep`, `Glob` or `SlashCommand` as the only way to
  > do it. Plan lookups go through `locate-plan.sh` and `check-plan-index.sh`. Open-ended
  > search names both the tools and their shell stand-ins. Gates that are left out on purpose
  > are now documented in `/smart-merge` itself. The step-7 `Grep` waits for the next R1
  > subgoal.
  > **Q:** Asked again on the corrected premise: the plugin's `CLAUDE.md` gates `git rm`,
  > `git branch -d`, `gh pr merge` and the delete on purpose, and `git push` cannot be
  > allowed without also allowing `--delete`. What should `/smart-merge` change?
  > **A:** Allow only `git pull --prune`, which is additive. Write the `gh` fallback's body
  > file with `Write` instead of a `cat` heredoc. Add a Guidelines bullet naming every
  > unlisted write as a deliberate gate, as `/clean-gone` does.
  - [x] `/close-revision`'s pointer check
    > **Note:** Step 5 also relied on `Glob` without naming it ("the archive does not
    > appear among `docs/plan/**/DO.md` matches"), so the inventory's scanner missed it.
    > All three checks now use tools the command has. The "exactly one place" check re-runs
    > `close-revision.sh`, which must now refuse with "no such section". The pointer check is
    > a `Read` of the lines step 3 edited. The resolution check runs `locate-plan.sh`, newly
    > allowed. The `/master-plan` subgoal reworks this command anyway, and this keeps it
    > working until then.
  - [x] `/step` and `/hitl-step`: the out-of-order lookup, Step 4's subgoal check, Step 5's re-Grep, the investigation paragraph
    > **Note:** Three of the four now go through scripts both commands already allow. The
    > out-of-order lookup finds the item's line in `check-plan-index.sh`'s `open:` list, so
    > the per-goal special case goes. Step 4 takes the goal's `open:` lines. Step 5 re-runs
    > `locate-plan.sh` for both layouts, so the legacy re-`Grep` goes. Only the investigation,
    > which is open-ended, keeps search tools: `Grep`/`Glob` if the session has them, and
    > otherwise shell `grep`/`find`, read-only. Step 1 is still byte-identical across both
    > commands.
  - [x] `/hitl-step` Step 3a's research list
    > **Note:** Worded like the investigation paragraph: `Grep`/`Glob` if the session has
    > them, and otherwise shell `grep`/`find`, read-only. `/step` has no such list.
  - [x] `/smart-merge` allows its routine writes, with patterns that don't also cover
        `git push origin --delete`, which stays a documented second gate
    > **Note:** Narrowed by the Q&A above. No `git push` pattern can exclude `--delete`,
    > since even `git push -u origin` prefixes `git push -u origin --delete <b>`. So only
    > `git pull --prune` was allowed, and the gates are now documented in the command
    > itself. Whether a `Write` to `/tmp` prompts is unmeasured; the heredoc it replaces
    > was not allowed either.
  - [x] `SlashCommand` becomes `Skill(workflow-claude:<name>)` in `/smart-commit`,
        `/agents-docs-update` and `/agents-docs-codex-init`
    > **Note:** The rule takes the skill's name with no slash, the same value the 72
    > transcript calls passed as `skill`. `/agents-docs-codex-init` also gained the grant it
    > never had. The plugin's `CLAUDE.md` said `/smart-commit` used the SlashCommand tool;
    > that one word was fixed here too. Whether a `Skill(...)` entry pre-approves the nested
    > call is unmeasured, so the Verify goal checks it.
  - [-] `/agents-docs-init`'s heredoc is documented as a deliberate gate
    > **Descoped:** It already was. Line 85 of the command says `Bash(cat:*)` is deliberately
    > absent, because the heredoc replaces the user's `CLAUDE.md` and should keep prompting.
  - [-] `/smart-merge` step 7
    > **Deferred:** rewritten once, through `scripts/locate-plan.sh`, by the next R1 subgoal.
- [x] Verify the branch end to end
  - [x] The three script suites and their mutants pass
    > **Result:** On `95b8e17`: `locate-plan` 83 cases, `check-plan-index` 39 and
    > `propose-branch-plan` 32, all passing; mutants 27, 24 and 18, all killed, none stale.
  - [x] per-goal-e2e `e1`, `e3` and `e4` pass: e4's Step 6 runs `check-plan-index.sh` with
        no denial, and all three pass the master-plan `[~]` check (the user runs them)
    > **Result:** Run `r3`, 2026-10-10, on the working tree: 65 checks and 0 failing. That
    > includes "e4-step: Step 6 ran check-plan-index.sh, and no awk" and the `[~]` flip on
    > `r1` and `r4`, with `r3`'s `DO.md` master plan left alone. All six sessions had no
    > permission denials and made no `Grep`, `Glob` or shell-search calls, for $2.43 in all.
    > Run `r2`'s e4 had failed only on the Step 6 `awk`.
  - [x] A headless `/smart-commit` makes its nested `Skill(workflow-claude:agents-docs-update)`
        call with no permission denial, against a `SlashCommand` control (the user runs it)
    > **Result:** Two runs in scratchpad fixtures, each with one staged file and no remote.
    > On the working tree, the `Skill` call ran ("Launching skill"). In the 0.9.0 control,
    > whose `SlashCommand(…)` grant matches nothing, the same call was **denied**, and the
    > model synced the docs inline and committed anyway. So the grant is what lets the
    > call through. A headless 0.9.0 `/smart-commit` silently skips `/agents-docs-update`,
    > and the 72 interactive successes must have been approved prompts.
    > **Note:** The working-tree run had one denial of another kind: the model appended
    > `2>&1; echo "exit=$?"` to `git push --follow-tags`, and a chained command matches no
    > prefix rule. Its bare retry ran. The command text says "run alone" only for its
    > scripts, not for git.
