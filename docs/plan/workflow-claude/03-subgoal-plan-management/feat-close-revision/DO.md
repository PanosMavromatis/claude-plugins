# feat/close-revision

**Status**: merged — PR #15 — 2026-08-30
**Created**: 2026-08-30
**Subgoal**: Extract closed revisions from the master plan so it stays an index

## Tasks

- [x] Write `scripts/close-revision.sh <N>`: locate the `## Subgoals — revision N` section in the master plan, print it, the destination `docs/plan/rev-N/_DO.md`, and the pointer line that would replace it. Read-only. Refuse with a clear message when the section is missing, when it still has unchecked items, or when the destination already exists.
  > **Done:** `scripts/close-revision.sh <N>` locates the section, prints it with the destination and replacement pointer, and refuses on a missing section, unchecked items, or an existing destination. Read-only. `[x]` and `[-]` count as finished; `[ ]`, `[~]` and `[!]` block.
- [x] Test against synthetic fixtures: a clean close, a revision with open items, a nonexistent revision, an already-closed revision, a `TODO.md` master, and a revision whose heading format varies.
  > **Done:** Clean close, open items, nonexistent revision, already-closed, both usage errors, a `TODO.md` master (archive correctly `_TODO.md`), marker handling, and a colonless heading. Two defects caught: the pointer concatenated its subtitle with no separator, and the destination directory is not required to exist — so the command must `mkdir -p`. One test was mislabeled and proved nothing: the "colonless heading" fixture had a colon, so the fallback never ran. Re-run properly. Third time this session a test passed while exercising the wrong path.
- [x] Write `commands/close-revision.md` following the `/file-plans` precedent — script in `allowed-tools`, writes performed by the command behind confirmation. State that the human decides when a revision is closed and the command never infers it.
  > **Done:** `commands/close-revision.md` follows the `/file-plans` precedent — script in `allowed-tools`, writes behind confirmation, `mkdir` added for the destination. States that the human decides a revision is finished and the command never infers it, that the archive is verbatim, and that the extraction is a cut rather than a copy.
- [x] Update README (the manual runbook becomes the command) and `CLAUDE.md` (the archive filename rule and why `_DO.md` rather than `DO.md`).
  > **Done:** README's manual runbook became the command, plus a command-table row; `CLAUDE.md` gained the archive-filename rule with the reasoning for `_DO.md` over `DO.md`, the cut-not-copy and verbatim rules, the `/file-plans`-first ordering, and the human-trigger rule. Both lifecycle diagrams gained the step.
- [x] Dogfood: close revision 3 with the command once its own subgoal is complete, and verify afterwards that plan resolution is unaffected — rung 3 still finds the master plan, rung 4 does not offer the archive, and `/file-plans` reports nothing to do.
  > **Done:** Closed revision 3 with it. Master plan went from ~143 lines to 101; the 42-line section now lives at `docs/plan/rev-3/_DO.md`. Verified afterwards: the section exists in exactly one file, rung 3 still resolves the master plan, rung 4's 15 matches do **not** include the archive, filed branch plans still resolve by name, rung 1 reaches the archive explicitly, `/file-plans` reports nothing to do, and re-closing is refused. Two defects the dogfood exposed: collapsing blank lines left the pointer flush against the next heading, breaking Markdown, and a lone pointer bullet where a section used to be reads as an orphan — so pointers now accumulate under a `## Closed revisions` heading. Both fixed in the command.
