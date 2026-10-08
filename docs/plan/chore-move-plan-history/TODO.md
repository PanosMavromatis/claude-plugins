# chore/move-plan-history

**Status**: active
**Created**: 2026-10-08
**Subgoal**: revision 05-subagent-refactor-R0 — move `plugins/workflow-claude/docs/plan/` to `docs/plan/workflow-claude/`

## Tasks

- [ ] Move `plugins/workflow-claude/docs/plan/` to `docs/plan/workflow-claude/` with `git mv`
- [ ] Mark the moved `DO.md` closed, and check that every moved branch plan is marked
      `merged`, so the old `/step`'s plan search offers none of them as active
- [ ] Repoint every reference to the old location: the plugin's README and CLAUDE.md,
      and anything under `commands/` or `scripts/` that reads the plugin's own `docs/`
- [ ] Index revisions 02–04 under `## Closed revisions` in the root master plan,
      at their new paths
