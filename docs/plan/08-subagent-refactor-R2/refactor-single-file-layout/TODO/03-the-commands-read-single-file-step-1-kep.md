# 03 — The commands read single-file, Step 1 kept in lockstep

**Goal**: [x]
> **Done:** Every command now reads `layout: single-file`, the two Step 1 sections are still in lockstep, and all six library suites pass with every mutant caught; the root plan's `legacy` is unchanged.

- [x] No command's text reads `layout: legacy` for a resolved or proposed plan: `smart-merge.md` and `new-branch.md` read `single-file`
  > **Note:** `smart-merge.md:83` and `new-branch.md:150` now read `layout: single-file`, and `grep -rn "layout: legacy"` over the plugin finds nothing. `smart-merge.md`'s "legacy commit statuses" is GitHub's term and `master-plan.md:35`'s `legacy` the root plan's, both unchanged. The installed 0.10.1 commands and scripts both still say `legacy`, so they agree until the 0.11.0 release takes both.
- [x] The `sed` lockstep diff of `/step`'s and `/hitl-step`'s Step 1 sections is empty
  > **Note:** The check in the plugin's `CLAUDE.md:201`, run as one script (extract both Step 1 sections, substitute `TODO.md`→`DO.md` and `/hitl-step`→`/step`, diff): 65 lines each, diff empty. Neither Step 1 needed an edit, since both name only `kind: legacy-master`, the root plan's kind.
- [x] Every suite of the six scripts that source `lib/plan-rules.sh` passes, the root plan's `legacy` in `propose-revision.sh`, `close-revision.sh` and `propose-merge-record.sh` among them unchanged
  > **Note:** Cases: locate-plan 87, check-plan-index 39, propose-branch-plan 33, propose-merge-record 37, propose-revision 74, close-revision 67, all passing; the root-plan suites' cases still expect `layout: legacy` for a legacy root plan, and pass. Mutants of the three root-plan suites, run here on the renamed library: propose-merge-record 18 of 18, propose-revision 43 of 43, close-revision 50 of 50, none stale. With goals 01 and 02's runs, every mutant of the six suites has run on this branch's library.
