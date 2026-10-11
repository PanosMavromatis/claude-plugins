# docs/plan-convention

**Created**: 2026-10-11
**Base**: main at 6f520cf
**Status**: active

## Purpose

Bring the plugin's own documentation up to date with what R1 built. `plugins/workflow-claude/CLAUDE.md`
and its README still describe the pre-R1 plugin: Markdown commands only, `Grep` lookups,
`/open-revision` writing a legacy section, and `/file-plans` filing merged plans. This branch
rewrites their plan-convention and revision-lifecycle sections to match the scripts, agent and
reference that exist now, so R2 starts from docs that are true.

## Scope

- Re-locate and verify the drift list recorded under R1's subgoal in `docs/plan/TODO.md`
- Rewrite the plugin `CLAUDE.md`'s plan-convention, lifecycle and artifact sections, including
  the §4.2 distinction in "do not reintroduce the split"
- Rewrite the README's "What's in here", loop diagram and lifecycle prose
- `/new-branch`: the branch-doc path, "always flat", and an `argument-hint`

## Context

- Master-plan subgoal: revision 06-subagent-refactor-R1, `docs/plan/TODO.md` (the drift list)
- Agreed plan §4.2, `tmp/subagent-refactor-plan.md` (untracked): why per-revision files do not
  reopen the rejected master-plan split
- Prior branches that found the drift: `feat-locate-plan-diagnostics`, `feat-per-goal-layout`,
  `feat-master-plan` (goals 4 and 5)

## Notes
