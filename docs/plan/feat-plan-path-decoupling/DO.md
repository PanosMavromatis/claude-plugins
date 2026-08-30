# feat/plan-path-decoupling

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Decouple branch-plan identity from location so `docs/plan/` can be reorganised freely

## Tasks

- [x] Rewrite rung 2 in `/step` and `/hitl-step` as a search for a directory named `<flattened-branch>` anywhere under `docs/plan/`, replacing the hardcoded `docs/plan/<flattened-branch>/<file>` path. Define the multi-match case (stale copy — list and ask, never guess) and the zero-match case (fall through to rung 3, unchanged). Keep both Step 1 sections byte-identical apart from the filename and verify with a diff.
  > **Done:** Rung 2 in both commands now globs `docs/plan/<plan-name>/<file>` **and** `docs/plan/**/<plan-name>/<file>`, with three explicit outcomes (one match / several = copied-not-moved, list and ask / none = fall through). The rung tries the exact flat path first and falls back to the recursive glob. That ordering is a **cost** optimisation for large trees, not a correctness requirement: the first draft justified it by claiming `**` does not reliably match zero path segments, and testing refuted that — Python's `glob`, bash `globstar` and Node's `globSync` all match `docs/plan/**/<name>/<file>` against a flat `docs/plan/<name>/<file>`. Corrected in all four files before commit. Lockstep re-verified by diff after the edit.
- [x] Update the intro paragraph of Step 1 in both commands: the flattened name is now the plan's **identity**, not its address, and its parent path is free-form.
  > **Done:** The Step 1 intro in both commands now states that the flattened name is the plan's identity and its parent path is free-form, with `git mv` named as the reorganisation mechanism.
- [x] Update `CLAUDE.md`'s "The plan convention" section — the flattening rule, the five rungs, and a statement that the layout beneath `docs/plan/` is deliberately unconstrained so plans can be regrouped by `git mv` without touching any command. Update `README.md` if it states the path form.
  > **Done:** `CLAUDE.md`'s plan-convention section gained the identity-vs-location rule, the rationale for resolving by name rather than adopting a taxonomy, the milestone/component guidance for when a grouping is eventually wanted, and an explicit statement that reconstructing a plan path is a bug. Rung 2's description updated to match, including the two-pattern glob. The lockstep bullet gained the verification command. README's two-tier bullet reworded.
- [x] Confirm `/new-branch` and `/smart-merge` need no change: `/new-branch` still creates flat, `/smart-merge` resolves the plan it was told about. If either hardcodes the path in a way that would break on a moved plan, fix it here.
  > **Done:** `/new-branch` needed no behavioural change (it creates flat, which stays correct) but gained a paragraph on why the name — not the path — is the key. `/smart-merge` **did** need fixing: step 2 hardcoded `docs/plan/<flattened-branch>/DO.md`, so a moved plan would have read as absent and step 7 would have skipped the stamp, leaving a merged plan marked `active` permanently. Step 2 now resolves by name and instructs steps 3, 4 and 7 to reuse the resolved path.
