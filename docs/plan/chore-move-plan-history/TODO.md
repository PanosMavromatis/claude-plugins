# chore/move-plan-history

**Status**: active
**Created**: 2026-10-08
**Subgoal**: revision 05-subagent-refactor-R0 — move `plugins/workflow-claude/docs/plan/` to `docs/plan/workflow-claude/`

## Tasks

- [x] Move `plugins/workflow-claude/docs/plan/` to `docs/plan/workflow-claude/` with `git mv`
  > **Done:** 21 tracked files moved as pure renames (0 insertions, 0 deletions), so
  > `git log --follow` keeps their history; nothing untracked or ignored was left
  > behind, and `plugins/workflow-claude/docs/` no longer exists.
- [x] Mark the moved `DO.md` closed, and check that every moved branch plan is marked
      `merged`, so the old `/step`'s plan search offers none of them as active
  > **Note:** of the 22 moved files, all 17 branch plans already carried
  > `merged — PR #n — <date>`; the three revision `_DO.md` files carry no status line
  > and need none, since the glob is `**/DO.md` and matches the exact name only. The
  > old master plan was the one `active` file, with no open items.
  > **Note:** the stamp must begin with `merged` — the status contract recognises no
  > other closed value, so `closed` would still read as active.
  > **Note:** the moved PR numbers belong to the archived `PanosMavromatis/workflow-claude`
  > and now collide with this repository's own (PR #1 here is not PR #1 there).
  > **Q:** how should the old master plan be stamped?
  > **A:** `merged — superseded by docs/plan/TODO.md — 2026-10-08`, plus a header line
  > naming the archived repository the PR numbers refer to.
  > **Done:** stamped, and the provenance line added.
- [ ] Repoint every reference to the old location: the plugin's README and CLAUDE.md,
      and anything under `commands/` or `scripts/` that reads the plugin's own `docs/`
- [ ] Index revisions 02–04 under `## Closed revisions` in the root master plan,
      at their new paths
