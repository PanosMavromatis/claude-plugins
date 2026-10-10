# feat/master-plan

**Status**: active
**Created**: 2026-10-10
**Subgoal**: revision 06-subagent-refactor-R1 — `/master-plan`, `plan-drafter` and `subdividing.md`

## Tasks

- [ ] Measure what the revision lifecycle does today, in the legacy and revisions layouts
  - [ ] What `open-revision.sh`, `close-revision.sh` and `file-plans.sh` read and write
  - [ ] Reproduce the reopen-guard miss on a closed revision
- [ ] The reopen guard matches `**Revision <label>** — closed`, with a test
- [ ] `references/subdividing.md` and `agents/plan-drafter.md`
  - [ ] Written with plugin-dev's `agent-development`, checked by `plugin-validator`
- [ ] `/master-plan <label> [spec]`, with `--dry-run <path>`; `/open-revision` is its alias
- [ ] `/close-revision` stamps, keeping the legacy path; `/file-plans` is legacy-only
- [ ] Verify end to end: the user runs it, I grade
