# feat/smart-merge-locate-plan

**Status**: active
**Created**: 2026-10-10
**Subgoal**: revision 06-subagent-refactor-R1 — `/smart-merge` step 7 through `locate-plan.sh`

## Tasks

- [ ] Measure what `/smart-merge` steps 2 and 7 need in each layout
  - [ ] What `locate-plan.sh`, `check-plan-index.sh` and `SUBGOALS_AWK` already report
  - [ ] Where the backlinked item lives: root `TODO.md`, or a revision's `_TODO.md`
  - [ ] Whether locating the backlink needs a new script mode
- [ ] Step 2 resolves the branch plan through `locate-plan.sh`
- [ ] Step 7 stamps the resolved index and edits the backlinked item in the right master file
  - [ ] Zero or several backlinks are reported, never guessed
- [ ] If the library changes, the three `dev/` suites and their mutant passes pass
- [ ] Verify end to end: the user runs it, `check.py` grades
