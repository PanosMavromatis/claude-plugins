# feat/plan-path-decoupling

**Created**: 2026-08-29
**Base**: main at d5c8af7
**Status**: active

## Purpose

Decouple a branch plan's **identity** from its **address**. Today `docs/plan/<flattened-branch>/` is both — rung 2 of the resolution order hardcodes that exact path, so the layout under `docs/plan/` cannot change without breaking plan resolution. Making rung 2 search for a directory *named* `<flattened-branch>` anywhere beneath `docs/plan/` keeps the name as the key and frees the path, so plans can be reorganised at any time by `git mv` with nothing else to update.

This is a prerequisite, not the end goal. It unblocks grouping plans under milestone or component directories later, without committing to any grouping now — which is the point: an ontology is expensive only when it must be chosen at creation time, and this change moves that decision to whenever the right shape is obvious.

## Scope

- Rewrite rung 2 in `/step` and `/hitl-step` as a name search under `docs/plan/`, keeping the two Step 1 sections byte-identical apart from the filename.
- Define the ambiguity case: more than one directory of the same name means a stale copy — list and ask, never guess.
- Keep `/new-branch` writing flat at `docs/plan/<flattened-branch>/` for now; the change is about where plans *may* live, not where they are created.
- Record the scaling notes that motivated this (see Context) as deferred items rather than acting on them.

## Context

Prompted by seven branch directories accumulating under `docs/plan/` in a single evening across two revisions. The user's concern is explicitly **not** about this repo, which is small: they work in monorepos where this branch rate is normal for months at a time, and where two further problems bite that do not bite here.

- **Master-plan growth is a context problem, not a cosmetic one.** `docs/plan/DO.md` is a single flat file read in full by rung 3 on `main`, and read *and rewritten* by `/smart-merge` on every merge. With hundreds of subgoals carrying `> **Done:**` annotations, closing one checkbox means loading the whole history. Directory clutter is a browsing annoyance; this is a cost that scales with every invocation.
- **Monorepos add a component axis** that this repo does not have. Unlike a topical taxonomy, that axis has an authoritative source already: the directory tree under `docs/agents/`. Any component grouping should read from it rather than inventing a second, divergent list of what the components are.
- Grouping by revision/milestone needs no taxonomy at all — there is exactly one open milestone at any moment, so classification is free. `docs/plan/DO.md` already groups its subgoals under `## Subgoals` and `## Subgoals — revision 2` headings, assigned without deliberation.

## Notes

- Rung 4 already globs `docs/plan/**/DO.md`, so it needs no change — it is agnostic to depth today.
- Branch names are unique per repo, which is what makes the directory name a sufficient key on its own.
