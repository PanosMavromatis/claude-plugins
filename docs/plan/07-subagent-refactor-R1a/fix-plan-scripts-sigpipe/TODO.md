# fix/plan-scripts-sigpipe

**Status**: active
**Created**: 2026-10-12
**Revision**: 07-subagent-refactor-R1a
**Subgoal**: 1. The plan scripts survive SIGPIPE: no reader exits before EOF on a pipe and kills its writer (`cat`, or `git show` under `--check`), starting with `close-revision.sh` at `:135`, `:217` and `:365`, and `die`'s hint no longer blames PATH or awk for a writer killed by SIGPIPE.
**Layout**: per-goal

## Goals

- [x] 01 — Fix close-revision.sh's early-exit pipes
- [ ] 01a — Make section_line and pointer_line read to EOF
- [x] 02 — Sweep the other plan scripts and lib for early-exit readers
- [x] 03 — Correct die's PATH and awk hint
- [ ] 04 — Add large-input suite cases and mutants
