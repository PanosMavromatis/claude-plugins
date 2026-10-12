# 01 — Write the session-handoff command

**Goal**: [x]
> **Done:** `commands/session-handoff.md` writes a Keep / Drop / Where-things-are handoff from git and the session's latest `locate-plan.sh` report, after flushing unlogged decisions to the plan; it needs nothing from the command runtime, so a 0.10.0 session can follow it as text.
> **Q:** How does `session-handoff.md` get the revision, branch and goal file, with no `${CLAUDE_PLUGIN_ROOT}` to reach `locate-plan.sh`: from the session's context (A), by globbing the installed script under `~/.claude/plugins/cache/` (B), or by resolving the plan in the command's own text (C)?
> **A:** A. The branch from `git branch --show-current`, and the revision, plan and goal-file paths from the latest `locate-plan.sh` report in the session; with none in context, the branch and the plan's flattened name, and a line saying the next `/hitl-step` or `/step` resolves the plan.

- [x] Read the models: the R1→R1a handoff (`tmp/session-handoff-r1-r1a.md`), §4.4's Keep / Drop / Say where, and an existing command's form under `plugins/workflow-coding/commands/`
  > **Note:** The R1→R1a handoff (149 lines) runs: where things stand, what to do next in order, R1a's settled decisions, carry-overs for R2, measurements, the user's working rules, then a one-paragraph Drop and a Where-things-are list. Keep is most of it. Two of its sections now live elsewhere: the working rules in the memory file `user-working-rules`, and the settled decisions in R1a's `_TODO.md`, so a handoff points at them rather than copying them. A command's frontmatter is plain text to a session reading the file, so `description:` is harmless there, and `allowed-tools:` must be absent.
- [x] Decide how the command finds the revision, branch and goal file with no `${CLAUDE_PLUGIN_ROOT}` to reach `locate-plan.sh`, and log the decision here
- [x] `plugins/workflow-coding/commands/session-handoff.md` writes `tmp/session-handoff.md` in three parts: Keep (§4.4's list), Drop (whatever a path retrieves) and Say where (pointers, not contents)
  > **Note:** The command gathers from git and the session's latest locate-plan.sh report, flushes unlogged decisions to the plan first (§4.4's Flush, confirmed edit by edit), and drafts Keep / Drop / Where things are; goal 03 tests that a session following it as text writes all three.
- [x] The file needs no `$ARGUMENTS`, no `${CLAUDE_PLUGIN_ROOT}` and no `allowed-tools`: no step depends on the command runtime
  > **Note:** grep finds no ARGUMENTS, CLAUDE_PLUGIN_ROOT or allowed-tools in it; its frontmatter is description: alone, and every command it runs is a plain git read.
