# chore/plan-regroup

**Status**: merged — PR #9 — 2026-08-29
**Created**: 2026-08-29
**Subgoal**: Exercise the identity/location decoupling by actually regrouping the accumulated plans

## Tasks

- [x] `git mv` the seven revision-2 branch plans into `docs/plan/rev-2/` and the revision-3 plan into `docs/plan/rev-3/`, leaving the master plan and any in-flight plan flat at the top level.
  > **Done:** Seven revision-2 plans moved to `docs/plan/rev-2/`, the revision-3 plan to `docs/plan/rev-3/`. Top level is now the master plan, two revision directories, and this in-flight plan — four entries instead of nine. Pure `git mv`; no command was touched, which was the whole point of the preceding PR.
- [x] Verify rung 2 resolves a **nested** plan: check out a branch whose flattened name now lives two levels down, and confirm the flat-path probe misses and the recursive glob hits.
  > **Done:** On branch `docs/mcp-convention` (recreated for the test), probe A `docs/plan/docs-mcp-convention/DO.md` missed and probe B `docs/plan/**/docs-mcp-convention/DO.md` resolved to `docs/plan/rev-2/docs-mcp-convention/DO.md`. Incidentally exercised the reopened-branch case for real: the resolved plan is stamped `merged — PR #5`, which rung 2 says to use but announce.
- [x] Verify the multi-match branch of rung 2: create a second directory of the same name, confirm both paths are found so the command would list and ask, then remove it.
  > **Done:** Copied the plan into `rev-3/` to create a genuine name collision; both paths were returned, which is the list-and-ask outcome. Duplicate removed afterwards. Confirms the multi-match branch is reachable and distinguishable from the single-match one — it is not dead prose.
- [x] Verify rung 3 and rung 4 still behave: the master plan still resolves on `main`, and the rung-4 glob still finds nested plans and still filters them by their `merged` stamp.
  > **Done:** Rung 3 unaffected (`docs/plan/DO.md` still resolves on `main`). Rung 4's glob found 11 plan files across depths 2, 3 and 4 — so nesting does not hide plans from it — and the stamp partition filtered 9 merged, leaving 2 active. That ratio is the argument for the filter: without it the disambiguation list would already be 11 entries after one evening.
