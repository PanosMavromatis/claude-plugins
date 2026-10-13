# fix/command-phrasing

**Status**: active
**Created**: 2026-10-13
**Revision**: 07-subagent-refactor-R1a
**Subgoal**: 6. Sessions running the plan commands phrase each command so `allowed-tools` matches it: `git` from the repository as `git <subcommand>`, never `git -C <path>`, and every command alone, never chained or piped, in the steps where a command does its work as well as where it runs its scripts.
**Layout**: per-goal

## Goals

- [x] 01 — State the phrasing rule in /hitl-step and /step
- [x] 02 — State it in /new-branch
- [x] 03 — State it in every other command that grants git
- [x] 04 — Check every command that grants git states the rule
- [x] 05 — Run e1, e3, e4 and e5 with no phrasing denials
