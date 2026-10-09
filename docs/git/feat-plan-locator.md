# feat/plan-locator

**Created**: 2026-10-08
**Base**: main at 7dfc39f
**Status**: active

## Purpose

Add `agents/plan-locator.md` to `workflow-claude` and make it Steps 1–2 of `/step` and
`/hitl-step`. The five-rung plan resolution then lives once, in the agent body, and the
commands' shared Step 1 shrinks to a few lines. The first subgoal of revision
`06-subagent-refactor-R1`; the branch also carries the commit that opens that revision.

Testing the agent showed that resolution is rule-shaped work. The branch therefore also
specifies and builds `scripts/locate-plan.sh`, a deterministic resolver that returns a
diagnostic (`problem:` and `fix:`) rather than guessing. It measures where
troubleshooting should live, in the parent or in a subagent that wraps the script, and
ships whichever the measurements favour.

## Scope

- `agents/plan-locator.md`, written with plugin-dev's `agent-development`: haiku, tools
  `Read, Grep, Glob` (the caller passes the branch name), `omitClaudeMd`, body under
  3,000 characters, a fixed report of repo-relative paths and line numbers
- `/hitl-step` and `/step` Steps 1–2 replaced by "spawn `plan-locator`, use what it
  returns", byte-identical apart from the filename
- The lockstep `sed` check in the plugin's `CLAUDE.md` updated to match
- Tested outside this session, on each rung: a 20-case headless suite (Haiku, then
  Sonnet); `plugin-validator` passes
- `scripts/locate-plan.sh`: the same rungs and report, plus `error`/`problem:`/`fix:`
  diagnostics and `warnings:`; run on the same suite plus a case for every diagnostic
- Step 1 switched to the script; the agent kept or deleted on the evidence
- Measured against the alternative: a subagent that runs the script and troubleshoots
  its diagnostics itself

## Context

- Working plan `tmp/subagent-refactor-plan.md` (private): §4.1 agent table, §4.2 the five
  rungs, §3.1 model tiers, §7.0 driver-vs-subject, §7.0b tooling, §7.7 regression set
- Driver is the installed 0.9.0; the edited agent is not live in this session and must
  not be loaded into it with `--plugin-dir`
- Master plan: `docs/plan/TODO.md`, revision `06-subagent-refactor-R1`, first subgoal

## Notes
