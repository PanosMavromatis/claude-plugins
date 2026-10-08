# chore/measure-context

**Created**: 2026-10-08
**Base**: main at fbd45fa
**Status**: active

## Purpose

Executes subgoal 3 of revision `05-subagent-refactor-R0`: a read-only
`dev/measure-context.sh` that reports what a session and each command load, so the
subagent refactor is judged against measured numbers rather than impressions. Its first
run sets the baseline every later revision is compared with.

## Scope

- `dev/measure-context.sh`, read-only, taking a repository path; it reports, in bytes and
  ≈ tokens (bytes / 4): session-start instruction files and their transitive imports;
  per command, its body plus the files it reads whole; the `docs/agents/**` total; the
  largest and median branch plan; the master plan.
- Run it on the read-only reference clone and reproduce the numbers the refactor plan was
  built on; resolve any gap rather than average it away.
- Record the baseline under goal 3 of the root master plan.

## Context

- Root master plan: `docs/plan/TODO.md`, revision `05-subagent-refactor-R0`, subgoal 3.
- Goals 1 and 2 landed as PR #1 and PR #2.
- Repository-level tooling, not shipped in a plugin; `plugins/dp-compile/dev/smoke-test.sh`
  is the nearest existing script of this kind.

## Notes
