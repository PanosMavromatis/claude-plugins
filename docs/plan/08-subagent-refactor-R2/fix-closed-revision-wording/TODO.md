# fix/closed-revision-wording

**Status**: active
**Created**: 2026-10-13
**Revision**: 08-subagent-refactor-R2
**Subgoal**: 2. Under a revisions index, `close-revision.sh`'s stamp writes the revision's index line in the form of the revisions closed earlier, keeping its note: ``- [x] <label> — <note> — closed. See `docs/plan/<label>/_TODO.md`.``, as `docs/plan/TODO.md:21` reads. Today it flips `[~]` to `[x]` and keeps the note alone. `--check` verifies the new form, and R1a's line is rewritten to it. `propose-revision.sh`'s `convert` stops carrying over prose that says a close extracts or moves a revision, and this repository's two such lines, left for R2 by PR #14, are rewritten.
**Layout**: per-goal

## Goals

- [x] 01 — The stamp writes the closed form, keeping the note
- [x] 02 — Convert warns on the legacy close prose
- [ ] 03 — Rewrite this repository's closed and stale lines
