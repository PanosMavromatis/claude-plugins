# chore/move-plan-history

**Status**: active
**Created**: 2026-10-08
**Subgoal**: revision 05-subagent-refactor-R0 — move `plugins/workflow-claude/docs/plan/` to `docs/plan/workflow-claude/`

## Tasks

- [x] Move `plugins/workflow-claude/docs/plan/` to `docs/plan/workflow-claude/` with `git mv`
  > **Done:** 21 tracked files moved as pure renames (0 insertions, 0 deletions), so
  > `git log --follow` keeps their history; nothing untracked or ignored was left
  > behind, and `plugins/workflow-claude/docs/` no longer exists.
- [ ] Mark the moved `DO.md` closed, and check that every moved branch plan is marked
      `merged`, so the old `/step`'s plan search offers none of them as active
- [ ] Repoint every reference to the old location: the plugin's README and CLAUDE.md,
      and anything under `commands/` or `scripts/` that reads the plugin's own `docs/`
- [ ] Index revisions 02–04 under `## Closed revisions` in the root master plan,
      at their new paths
