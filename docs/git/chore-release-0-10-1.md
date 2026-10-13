# chore/release-0-10-1

**Created**: 2026-10-13
**Base**: main at d1a7295
**Status**: active

## Purpose

Release `workflow-coding` 0.10.1, R1a subgoal 4 and the revision's last: bump `plugin.json` to 0.10.1 and document what the release carries, the new `/session-handoff` and `/session-export-full` above all; then check, after the merge, that the marketplace install loads 0.10.1 with both, that `/session-export-full` exports the session it runs in, and that the R1a handoff is written and read first.

## Scope

- `plugins/workflow-coding/.claude-plugin/plugin.json` to 0.10.1. `README.md`, `plugins/workflow-coding/README.md` and `plugins/workflow-coding/CLAUDE.md` document the two commands and what else 0.10.1 changes: the plan scripts' SIGPIPE fix, goal files written with their subgoals, and the phrasing rule with its `dev/command-phrasing` check.
- After the merge: the marketplace install, `/session-export-full` on its own session, and the R1a handoff. Goal 02 can only be checked once 0.10.1 is on `main`, so the plan merges with it open and subgoal 4 at `[~]`; the branch that closes R1a ticks both.
- Not here: an e2e run of the release text, and §4.2 of the untracked `tmp/subagent-refactor-plan.md`.

## Context

- R1a subgoal 4 is at `docs/plan/07-subagent-refactor-R1a/_TODO.md:68`. It builds on 1, 2, 3, 5 and 6, all merged (PRs #15–#19).
- `.claude-plugin/marketplace.json` carries no version, and `dp-compile` depends on `workflow-coding` unpinned. The repository has no tags, `CHANGELOG.md` or `VERSION`: `plugin.json` is the release.
- `fix/command-phrasing` (PR #19) left its tightened "`Read` `smart-commit.md` whole" pointers unverified by an e2e run, and this branch runs none, so that waits for the next run.

## Notes

- 2026-10-13: the goal files are written with their subgoals, by hand, since the installed `/new-branch` is still 0.10.0.
