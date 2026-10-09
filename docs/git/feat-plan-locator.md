# feat/plan-locator

**Created**: 2026-10-08
**Base**: main at 7dfc39f
**Status**: active

## Purpose

Add `agents/plan-locator.md` to `workflow-claude` and make it Steps 1–2 of `/step` and
`/hitl-step`. The five-rung plan resolution then lives once, in the agent body, and the
commands' shared Step 1 shrinks to a few lines. The first subgoal of revision
`06-subagent-refactor-R1`; the branch also carries the commit that opens that revision.

## Scope

- `agents/plan-locator.md`, written with plugin-dev's `agent-development`: haiku, tools
  `Read, Grep, Glob, Bash(git branch --show-current:*)`, body under 3,000 characters,
  a fixed report shape of paths and line numbers the caller can check with one `Read`
- `/hitl-step` and `/step` Steps 1–2 replaced by "spawn `plan-locator`, use what it
  returns", byte-identical apart from the filename
- The lockstep `sed` check in the plugin's `CLAUDE.md` updated to match
- Tested outside this session, on each rung; `plugin-validator` passes

## Context

- Working plan `tmp/subagent-refactor-plan.md` (private): §4.1 agent table, §4.2 the five
  rungs, §3.1 model tiers, §7.0 driver-vs-subject, §7.0b tooling, §7.7 regression set
- Driver is the installed 0.9.0; the edited agent is not live in this session and must
  not be loaded into it with `--plugin-dir`
- Master plan: `docs/plan/TODO.md`, revision `06-subagent-refactor-R1`, first subgoal

## Notes
