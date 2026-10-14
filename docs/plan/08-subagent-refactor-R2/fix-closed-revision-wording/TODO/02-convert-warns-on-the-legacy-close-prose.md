# 02 — Convert warns on the legacy close prose

**Goal**: [x]
> **Q:** No script wrote the stale prose (`f8d837f` wrote the root plan by hand), and `convert` carries every non-pointer line verbatim. So it cannot leave "no prose saying a close extracts or moves a revision" without judging free text, nor drop the prose under `## Closed revisions`, which here also held revisions 02–04's history. Should `convert` warn on such prose (A), drop this half and fix only this repository's lines (B), or rewrite the exact sentences this repository used (C)?
> **A:** A: warn, don't rewrite. For `convert`, the master plan's "leaves no prose" becomes "warns on it"; this repository's own lines are still rewritten, in goal 03.
> **Q:** What counts as prose describing the legacy close: a paragraph naming `/close-revision` and a word starting extract or move (A), the two on one line (B), or any line naming `/close-revision` (C)?
> **A:** A: a paragraph, a run of non-blank lines outside fences, the verb matched at a word's start in any case; one warning per paragraph, naming its line that first names `/close-revision`.
> **Done:** `convert` warns, once per paragraph outside fences, on prose saying `/close-revision` extracts or moves a revision, naming the line, and renders the root plan as before. The suite gained `c16` and `c17` and seven mutants; the spec and the plugin's `CLAUDE.md` describe the warning.

- [x] `propose-revision.sh`'s `convert` reports a `warnings:` line for each prose line saying `/close-revision` extracts or moves a revision, naming the line, and renders the root plan otherwise unchanged
  > **Note:** A second awk pass, after the refusals, so a refused run carries no such warning; like every reader since 0.10.1 it reads the root plan to the end. On the suite's `CLOSED_LEGACY`, which holds this repository's own "Extracted by `/close-revision` once finished.", it warns on line 14, and `c02` and `c10` render that plan byte for byte as before.
- [x] The propose-revision suite passes, with a case that warns on such prose and one that doesn't warn on other prose, and `--mutants` catches every mutant, one that drops the warning among them
  > **Note:** 74 of 74 cases pass, twice under each Bash found; `--mutants` kills 43 of 43, none stale. `p27` (warning dropped) and `p32` (case-sensitive) die at `c01`; `p28` (by line), `p29` (fences read), `p30` (verb mid-word) and `p31` (any mention) at `c16`; `p33` (CR kept) at `c17`. Line 5 of `c16`'s fixture, a true sentence holding "removes", is what `p30`, `p31` and `p33` all wrongly warn on.
- [x] `propose-revision-spec.md` describes the warning
  > **Note:** Also the plugin's `CLAUDE.md:71`, where maintainers read what `convert` does. `/master-plan` already shows every `warnings:` line (`master-plan.md:37`), so the command's text is unchanged.
