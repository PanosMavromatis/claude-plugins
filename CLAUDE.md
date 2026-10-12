# Session handoff

`tmp/session-handoff.md` is left by one session for the next. If it exists when a session
starts, that is, before your first reply, with no summary of an earlier conversation in
context, read it whole before anything else, and say in a few lines what you took from it.
Once the user confirms, archive it: run `mkdir -p tmp/handoffs`, then `mv` it to
`tmp/handoffs/<YYYY-MM-DD>-<branch>.md`, with the date from its `**Written**:` line and
the branch from its title, each `/` replaced by `-`. If that name is taken, add `-2`, `-3`
before `.md`. At any other time, after a compaction or in the session that wrote it, leave
it alone: it is the next session's.

# Compact instructions

Keep pointers, not copies.

- **Say where things are**, not what they say: the branch, the plan and the goal file by
  path, as the latest `locate-plan.sh` report gave them, and any other file by its path
  and a few words on what it holds.
- **Drop** what a later step can get back: the contents of any file under `docs/plan/`
  or `docs/agents/`, and of `AGENTS.md`, which their paths retrieve; subagent reports in
  full, since a subagent can be run again; anything under `.claude/agent-memory/`, which
  the agent reloads; and the bodies of commands and skills already run.
