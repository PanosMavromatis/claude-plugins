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
- [x] Repoint every reference to the old location: the plugin's README and CLAUDE.md,
      and anything under `commands/` or `scripts/` that reads the plugin's own `docs/`
  > **Note:** nothing the plugin runs reads its own `docs/` — no `${CLAUDE_PLUGIN_ROOT}/docs`
  > or relative `../docs/` in `commands/`, `scripts/` or `hooks/` — so dropping the
  > history from installs is safe, not merely tidy.
  > **Note:** the revision labels in `commands/{open,close}-revision.md`, both
  > `scripts/*-revision.sh` and the README's sample tree are example names, not paths,
  > and stay. The history's own internal paths stay as written (goal 2's header note
  > covers them). The one stale claim was `CLAUDE.md`'s "layout in this repo" paragraph.
  > **Note:** the installed `protect-agent-docs.py` did not block the `CLAUDE.md` edit,
  > contrary to the warning given beforehand: it arms only when a sentinel
  > `docs/agents/<component>/core.md` exists, and this repository has no `docs/agents/`.
  > That changes once R2/R3 give the plugin a `docs/agents/` source — from then on its
  > `CLAUDE.md` is edited through the source, as the hook intends.
  > **Done:** `plugins/workflow-claude/CLAUDE.md` now describes the marketplace layout —
  > root master plan, history under `docs/plan/workflow-claude/` moved by one `git mv`.
- [ ] Index revisions 02–04 under `## Closed revisions` in the root master plan,
      at their new paths
