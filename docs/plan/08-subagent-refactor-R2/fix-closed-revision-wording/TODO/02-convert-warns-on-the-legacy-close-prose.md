# 02 — Convert warns on the legacy close prose

**Goal**: [ ]
> **Q:** No script wrote the stale prose (`f8d837f` wrote the root plan by hand), and `convert` carries every non-pointer line verbatim. So it cannot leave "no prose saying a close extracts or moves a revision" without judging free text, nor drop the prose under `## Closed revisions`, which here also held revisions 02–04's history. Should `convert` warn on such prose (A), drop this half and fix only this repository's lines (B), or rewrite the exact sentences this repository used (C)?
> **A:** A: warn, don't rewrite. For `convert`, the master plan's "leaves no prose" becomes "warns on it"; this repository's own lines are still rewritten, in goal 03.

- [ ] `propose-revision.sh`'s `convert` reports a `warnings:` line for each prose line saying `/close-revision` extracts or moves a revision, naming the line, and renders the root plan otherwise unchanged
- [ ] The propose-revision suite passes, with a case that warns on such prose and one that doesn't warn on other prose, and `--mutants` catches every mutant, one that drops the warning among them
- [ ] `propose-revision-spec.md` describes the warning
