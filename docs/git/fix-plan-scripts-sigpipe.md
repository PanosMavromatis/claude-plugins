# fix/plan-scripts-sigpipe

**Created**: 2026-10-12
**Base**: main at 1dd709a
**Status**: active

## Purpose

Make the plan scripts survive SIGPIPE. Under `set -euo pipefail`, a pipe whose reader exits before EOF (`awk '…{print; exit}'`) can kill its writer (`cat`, or `git show` under `--check`), and the script then dies with exit 3. That made closing R1 fail at random on plans over ~16 KB. This branch makes every reader read to EOF, corrects `die`'s hint, which blames PATH or awk, and adds large-input suite cases so the race can't come back. It ships in `workflow-coding` 0.10.1.

## Scope

- `close-revision.sh`: the measured sites at `:135` and `:217` (loud: exit 3) and `:365` (silent: `if ! printf | awk …exit` would read "not found").
- Sweep every other script under `plugins/workflow-coding/scripts/` and `scripts/lib/`, single- and multi-line awk alike.
- `lib/plan-rules.sh`'s `die`: the hint must not blame PATH or awk for a writer killed by SIGPIPE.
- `dev/close-revision/suite.py`: a >64 KB plan, both the close and its `--check`. Its `mutants/` and `README.md`. A large-input case in the suite of any other script changed.

## Context

- R1a subgoal 1: `docs/plan/07-subagent-refactor-R1a/_TODO.md`.
- Diagnosed while closing R1 (PR #13). It failed once on the 66 KB `feat-plan-locator/TODO.md` and once on the 22 KB `feat-locate-plan-diagnostics/TODO.md`. A standalone `cat | awk` loop (50 runs) did not reproduce it.
- Fix idea: `!done && /re/ {print; done=1}`, which reads to EOF and prints the first match only.

## Notes

- 2026-10-12, goal 01: `close-revision.sh` had five early-exit pipe readers, not three; `:177` (the layout under `--check`) and `:194` (`stamp`'s index line) too. All five now read to EOF (`got { next }`). Suite 58/58; `--mutants` 40/40 after re-anchoring the four patches the edit made stale (c05, c06, c08, c19).
- 2026-10-12, goal 02: no other plan script has an early-exit pipe reader. Every other pipe's reader reads to EOF (`sort`, `tr`, or an awk with no `exit`), and every awk that exits early reads a file argument or exits only in `END`. No code changed, so goal 04's large-input cases are close-revision's alone.
- 2026-10-12, correction to goal 02: `close-revision.sh:277` and `:282` pipe `src` into `section_line` and `pointer_line` through `/dev/stdin`, and both stop at the first match, so there are seven early-exit readers, not five. Goal 01a gives both awks the read-to-EOF guard.
- 2026-10-12, goal 03: `die` no longer blames PATH or a tool for status 141 (SIGPIPE) or 3 (its own, from a writer's `die` inside the failed pipeline). Close-revision cases `t04` and `t05` pin both hints with a `cat` stub that kills itself with SIGPIPE.
- 2026-10-12, goal 01a: `section_line` and `pointer_line` read to EOF (`got { next }`). That made 12 mutant patches stale and let none survive (close-revision `l01`–`l03`, propose-revision `v01`–`v08` and `v10`); re-anchored, close-revision kills 40 of 40 and propose-revision 36 of 36.
- 2026-10-12: this branch also adds R1a subgoal 5 to the revision's `_TODO.md`: `/new-branch` 0.10.0 wrote this branch's goal files as stubs with no subgoals, so they were fleshed out by hand, and the fix (goal files with their subgoals, never stubs) ships in 0.10.1.
- 2026-10-12: this branch also amends R1a subgoal 2: the root `CLAUDE.md` it creates holds the workflow's `# Compact instructions` too, since they are part of the workflow, not a personal preference. A dated settled decision in the revision's `_TODO.md` records the change.
