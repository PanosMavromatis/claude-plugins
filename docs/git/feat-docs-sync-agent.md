# feat/docs-sync-agent

**Created**: 2026-10-14
**Base**: main at ad4e000
**Status**: active

## Purpose

R2 subgoal 8. `/agents-docs-update`'s work moves into a subagent, `agents/docs-sync.md`, so the doc sync runs outside the main session's context: `/agents-docs-update` thins to a wrapper around it, and `/smart-commit` spawns it with the `Agent` tool. Two things are tested before the agent is built: whether `protect-agent-docs.py` fires on a subagent's `Edit`, and whether `dp-compile`'s gate still sees the docs the agent stages.

## Scope

- the two tests, run and recorded before any agent text is written
- `plugins/workflow-coding/agents/docs-sync.md` (new): §4.1's row and conventions, §4.3's routing, a rebuild of `AGENTS.override.md` only on a `codex-review/` change, `memory: project`
- `commands/agents-docs-update.md` and `commands/smart-commit.md`
- `.claude/agent-memory/`, committed
- §7.7's cases, end to end

## Context

- R2 subgoal 8: `docs/plan/08-subagent-refactor-R2/_TODO.md:67`
- Design: §4.1, §4.3, §7.7 and §8 of `tmp/subagent-refactor-plan.md`; D-N7 for the agent's memory
- Builds on subgoal 7 (PR #29): the build writes only `AGENTS.override.md`, and the hook protects only that file. `/agents-docs-update` still describes the dispatcher layout and calls the build on a `core.md` or `codex.md` change, which the new build refuses; this branch replaces that
- The `dp-compile` test and §7.7's cases need real sessions, which cost money: the user runs them
- A hook changed here is not live in this repository until 0.11.0 is installed (subgoal 14)

## Notes

- 2026-10-14, goal 01: `dev/subagent-hooks/` runs four headless haiku sessions on fixtures with this repository's plugins loaded by `--plugin-dir`. In run `s2`, `protect-agent-docs.py` fires on a subagent's `Edit`, between a blocked main-session control and a subagent edit of `AGENTS.md` that lands, so `/agents-docs-update` needs no `check-agents-md.sh` re-run; and `dp-compile`'s gate blocks the main session's commit, naming the kernel, having seen the `AGENTS.md` a subagent staged. Run `s1`'s gate case was void: `dp-compile` loaded alone by `--plugin-dir` is dropped silently for its missing dependency, left for R4. The `Agent` tool ran each subagent in the background, so `/smart-commit` must commit after `docs-sync` hands back. A note under R2 subgoal 14 records that until 0.11.0 a fresh install gets `main` labelled 0.10.1
- 2026-10-14, goal 02: `agents/docs-sync.md` does `/agents-docs-update`'s work by §4.1 and §4.3: `sonnet`, bare `tools` (the docs give `tools:` no Bash-pattern form, so the user's permission rules and the body's Never list bound its Bash), `memory: project`. It stops in the dispatcher layout, routes edits by §4.3's rule, rebuilds only on a `codex-review/` change, stages its edits and its memory, and returns four lines. Both validators pass, plugin-dev's `validate-agent.sh` only as a patched copy, since its `set -e` counter exits at any first warning. Run `m1` puts a plugin agent's memory in `.claude/agent-memory/workflow-coding-docs-sync/`. Goal 03 now first measures whether a command's grant reaches the agent, for an edit and for a `git commit` it must never make; goal 05's runs use default permissions, and its gate case blocks, since the gate names a kernel only then
- 2026-10-14, goal 03, subgoal 1: `dev/grant-lifetime/` gains `spawn`, `direct` and `relay` fixture commands and nine headless cases. Run `a1`: a command's grant reaches the subagents it spawns, for `Edit`, `git add` and `git commit`, in the foreground and in the background, where the main session's turn ended and resumed on the hand-back; without a command the subagent's writes are denied. So `/agents-docs-update` can rely on its grant for `docs-sync`'s writes, but under `/smart-commit` only the agent's instructions would stop it committing or pushing: goal 03a, split off, builds a hook for that before goal 04. The model ran two background cases in the foreground, so a command cannot count on either mode. `docs-sync`'s guide now overrides only its routing steps, never Output or Never, and the agent does not edit it
- 2026-10-14, goal 03: `/agents-docs-update` is a wrapper. It describes the §4.3 layout, spawns `workflow-coding:docs-sync` once, acts only on its hand-back, and relays its four lines with paths from the repository root; its `allowed-tools` are exactly the agent's, since a command's grant reaches the agent, and `find`, `cat`, `ls`, `git branch --show-current` and `Skill(agents-docs-build)` went. The plugin's README and `CLAUDE.md` describe it. `/smart-commit` still invokes it through `Skill` and waits for a "Step 6" the wrapper no longer has, until goal 04
- 2026-10-14, goal 03a, subgoal 1: a subagent's tool call carries `agent_id` and `agent_type` in a `PreToolUse` hook's input, and a plugin agent's `agent_type` is its namespaced name: run `i1`'s fixture hook logged `workflow-coding:docs-sync` for the agent's calls, `general-purpose` for a stand-in's, and neither field for the main session's. So the guard can match `workflow-coding:*` and never touch the main session's commit. Because `/smart-commit` also grants `git tag`, the guard became an allowlist: this plugin's agents may run only `git status`, `diff`, `add`, `log`, `show`, `rev-parse` and `ls-files` and `gh pr list` and `pr view`
