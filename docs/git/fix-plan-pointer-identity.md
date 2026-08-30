# fix/plan-pointer-identity

**Created**: 2026-08-30
**Base**: main at 804729b
**Status**: active

## Purpose

`/smart-merge` writes a `Plan:` pointer into every PR body as a **path**, and claims in the same breath that "the pointer resolves permanently". It does not. PR bodies are effectively immutable, plan locations are deliberately free, and the first filing sweep (PR #9) invalidated seven pointers at once — including the one in the PR that performed the move.

Write the plan's **identity** instead. That is the same rule the resolution order already follows: a plan is found by its directory name, wherever it sits. Applying it to records as well as lookups closes the gap for good, rather than making the paths correct until the next sweep.

## Scope

- Rewrite the plan-pointer bullet in `/smart-merge` step 3 to emit a name plus a resolution hint, and delete the false permanence claim.
- Note in the command *why* it is a name, so a later editor does not "improve" it back into a path.
- Record the general rule in `CLAUDE.md`: a path written into an immutable record decays; write identity.
- Do not attempt to repair the seven already-broken pointers in PRs #1-#11 — PR bodies can be edited through the API, but rewriting merged history to fix a pointer that a reader can resolve by name is not worth the risk. Note the interim workaround instead, which README already carries.

## Context

This must land before `/file-plans` (the next subgoal) automates the sweep. Automating a move that silently invalidates a batch of permanent records each time it runs would industrialize the defect rather than fix it — the ordering is the point, not an accident of what got noticed first.

Considered and rejected: emitting a GitHub permalink (`/blob/<sha>/…`) alongside the name. It is genuinely immutable and would survive any move, but it is mechanism-specific — it needs the head SHA and a GitHub URL, so it works on the MCP and `gh` paths and nowhere else, and it points at the plan as it was rather than as it is. A name resolves with `Glob`, `git`, or a file browser, on any host. Worth revisiting only if someone wants the frozen-at-merge snapshot specifically.

## Notes

- PR #12's own body already used the name-based form, ahead of this change formalising it.
