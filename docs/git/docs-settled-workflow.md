# docs/settled-workflow

**Created**: 2026-08-30
**Base**: main at dd42a8a
**Status**: active

## Purpose

Bring `README.md` and `CLAUDE.md` up to date with the workflow that settled over revisions 2 and 3. Both describe pieces accurately but neither describes the loop end to end, and neither mentions the plan-filing sweep at all — which is now a real step a user has to know about, since `docs/plan/` grows by one flat entry per merged branch until someone runs it.

## Scope

- README: a section describing the settled end-to-end loop, including the periodic filing sweep, and refreshed conventions bullets covering plan identity-vs-location and locate-then-window access.
- CLAUDE.md: the same loop stated for the model, with the filing sweep and its derivation rule.
- Record the correction: filing was described as a judgement to keep manual; it is a lookup, since the enclosing `## Subgoals — revision N` heading of a plan's backlink already determines its revision.
- Record the stale-pointer finding without fixing it here — it is a later revision-3 subgoal.

## Context

The settled loop, as actually practised across PRs #1-#11:

```
/new-branch → /step or /hitl-step → /smart-commit → /smart-merge → /clean-gone
                                                          ↓
                                          (periodically) file merged plans into rev-N/
```

Two facts that the docs currently omit:

- **Filing is a lookup, not a judgement.** An earlier statement in this repo's history called the choice of revision directory "the one judgement worth keeping manual". That was wrong. `/new-branch` writes the `> **Branch:**` backlink beneath a specific `## Subgoals — revision N` heading, so the revision is already recorded and recoverable with one line of `awk`. The no-taxonomy argument does not apply: nothing is being classified, only read back.
- **Paths written into permanent records decay.** PR #8's body carries `Plan: docs/plan/feat-plan-path-decoupling/DO.md`; that plan now lives under `rev-3/`, and PR bodies are effectively immutable. The regrouping in #9 broke seven such pointers silently. The fix is to write the plan's *identity* rather than its address, which is a later subgoal of this revision and must land before automated filing makes moves routine.

## Notes

- Documenting the sweep as a manual step stays true whether or not `/file-plans` automates it later — a command changes the mechanics, not the workflow. Amending afterwards is one line.
