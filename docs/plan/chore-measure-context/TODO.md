# chore/measure-context

**Status**: active
**Created**: 2026-10-08
**Subgoal**: revision 05-subagent-refactor-R0 — add `dev/measure-context.sh` and record its baseline

## Tasks

- [ ] Write `dev/measure-context.sh`: read-only, takes a repository path, and reports
      the five measurements in bytes and ≈ tokens (bytes / 4)
- [ ] Run it on `tmp/pfsmgraph` at `5e8ad6e` and reproduce the working plan's §1
      numbers; any gap is a script bug or a §1 error, and gets resolved, not averaged
- [ ] Record the baseline under goal 3 in the root master plan
