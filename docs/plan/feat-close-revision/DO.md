# feat/close-revision

**Status**: active
**Created**: 2026-08-30
**Subgoal**: Extract closed revisions from the master plan so it stays an index

## Tasks

- [ ] Write `scripts/close-revision.sh <N>`: locate the `## Subgoals — revision N` section in the master plan, print it, the destination `docs/plan/rev-N/_DO.md`, and the pointer line that would replace it. Read-only. Refuse with a clear message when the section is missing, when it still has unchecked items, or when the destination already exists.
- [ ] Test against synthetic fixtures: a clean close, a revision with open items, a nonexistent revision, an already-closed revision, a `TODO.md` master, and a revision whose heading format varies.
- [ ] Write `commands/close-revision.md` following the `/file-plans` precedent — script in `allowed-tools`, writes performed by the command behind confirmation. State that the human decides when a revision is closed and the command never infers it.
- [ ] Update README (the manual runbook becomes the command) and `CLAUDE.md` (the archive filename rule and why `_DO.md` rather than `DO.md`).
- [ ] Dogfood: close revision 3 with the command once its own subgoal is complete, and verify afterwards that plan resolution is unaffected — rung 3 still finds the master plan, rung 4 does not offer the archive, and `/file-plans` reports nothing to do.
