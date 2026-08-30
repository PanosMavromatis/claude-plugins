# feat/plan-path-decoupling

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Decouple branch-plan identity from location so `docs/plan/` can be reorganised freely

## Tasks

- [ ] Rewrite rung 2 in `/step` and `/hitl-step` as a search for a directory named `<flattened-branch>` anywhere under `docs/plan/`, replacing the hardcoded `docs/plan/<flattened-branch>/<file>` path. Define the multi-match case (stale copy — list and ask, never guess) and the zero-match case (fall through to rung 3, unchanged). Keep both Step 1 sections byte-identical apart from the filename and verify with a diff.
- [ ] Update the intro paragraph of Step 1 in both commands: the flattened name is now the plan's **identity**, not its address, and its parent path is free-form.
- [ ] Update `CLAUDE.md`'s "The plan convention" section — the flattening rule, the five rungs, and a statement that the layout beneath `docs/plan/` is deliberately unconstrained so plans can be regrouped by `git mv` without touching any command. Update `README.md` if it states the path form.
- [ ] Confirm `/new-branch` and `/smart-merge` need no change: `/new-branch` still creates flat, `/smart-merge` resolves the plan it was told about. If either hardcodes the path in a way that would break on a moved plan, fix it here.
