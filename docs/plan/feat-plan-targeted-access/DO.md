# feat/plan-targeted-access

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Make master-plan access cost independent of file size

## Tasks

- [ ] Rewrite `/smart-merge` step 7's master-plan update as locate-then-window: `grep -n '> \*\*Branch:\*\* <branch>'` to find the backlink, read a bounded window around the hit, edit in place. State the sequence explicitly — an LLM told only "update the master plan" will default to a whole-file read, which is the entire cost being avoided.
- [ ] Add the zero-match guard: if the `grep` returns no hit, report it. "No master-plan item is backlinked to this branch" (legitimate — a standalone branch) must be distinguishable from "the lookup failed" (a bug). Today both produce silence. Also handle >1 hit, which means a duplicated backlink.
- [ ] Apply the same treatment to rung 3 in `/step` and `/hitl-step`: locate the next unchecked item by `grep -n`, read the header plus a window rather than the whole file. Decide whether to keep a whole-file read below a size threshold, and say why in the prose. **Their Step 1 sections are byte-identical by contract** — land it in both and verify by diff.
- [ ] Record the rule and the measurement in `CLAUDE.md`: master-plan access is locate-then-window, a silent miss is a bug, and the numbers that justify it. Retire the Deferred item, noting that the split-into-milestone-files design it proposed was rejected *by measurement* — size was never the problem.
