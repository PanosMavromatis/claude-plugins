# fix/closed-revision-wording

**Created**: 2026-10-13
**Base**: main at 187c221
**Status**: active

## Purpose

R2 subgoal 2. Under a revisions index a close only stamps, but the stamp keeps the index line's note and nothing else, where the revisions closed earlier read `— closed. See <path>.`; and the root plan's prose still describes the legacy close that extracts and moves a revision, carried over verbatim when R1a's opening converted it (PR #14 left it for R2). This branch makes the stamp write the closed form, keeping the note; makes `convert` warn on prose that describes the legacy close; and rewrites this repository's R1a line and its two stale lines.

## Scope

- `close-revision.sh`'s stamp and `--check`, with suite, mutants and spec; `commands/close-revision.md` and the plugin's `CLAUDE.md` where they describe the stamp
- `propose-revision.sh`'s `convert`: a warning on legacy close prose, with suite, mutants and spec
- `docs/plan/TODO.md`: R1a's line (25), and lines 6–8 and 12

## Context

- R2 subgoal 2: `docs/plan/08-subagent-refactor-R2/_TODO.md:43`; R2's review chose to keep the note and to rewrite R1a's line here
- PR #14's body: "Two prose lines carried over verbatim now describe the old layout; they are left for R2"
- No script wrote that prose: `f8d837f` wrote the root plan by hand when R0 opened, and `convert` carries non-pointer lines verbatim, so it warns rather than rewrites (goal 02's Q&A)
- `close-revision.sh:258` (the stamp's `edits:`) and `:439` (`--check`); `dev/per-goal-e2e`'s c1 takes its expected lines from the script's `edits:`, so it follows the change

## Notes
