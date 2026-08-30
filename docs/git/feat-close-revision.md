# feat/close-revision

**Created**: 2026-08-30
**Base**: main at d065a0e
**Status**: active

## Purpose

The master plan accumulates every subgoal of every revision, with its `> **Done:**` annotation, and nothing ever removes any of it. `/close-revision N` extracts a finished revision's section into `docs/plan/rev-N/_DO.md`, leaving a one-line pointer behind, so the master plan reads as an index of closed revisions plus whatever is currently open — and stays roughly constant in size rather than growing indefinitely.

This is the last subgoal of revision 3, and closing revision 3 with it is the test.

## Scope

- `scripts/close-revision.sh` — read-only. Given a revision number, print the section it would extract, the destination, and the pointer that would replace it. Refuse clearly when the revision has open items, when the section does not exist, or when the destination already exists.
- `/close-revision N` — runs the script, presents, confirms, performs the extraction, commits on a branch.
- README and `CLAUDE.md`: the manual runbook becomes the command.
- Dogfood: close revision 3 with it.

## Context

**The filename is load-bearing.** Rung 4 resolves plans by globbing `docs/plan/**/DO.md`, matching on filename, so an extracted `rev-N/DO.md` would be indistinguishable from a branch plan and — unstamped — would count as *active*, polluting the disambiguation list the merged filter exists to keep clean. An earlier design fixed that by stamping the file `closed` and widening the four-command status contract to accept that value. `_DO.md` is strictly better: no contract change, no container guard in `scripts/file-plans.sh`, one fewer concept. It also makes an archived revision **invisible** to resolution rather than merely filtered out of it — correct, since a finished revision should never be offered as an answer to where to do work. Explicit path (rung 1) still reaches it.

**The trigger is human and must stay so.** A revision is closed when the user says it is, not when its last checkbox ticks. Revision 3 is the proof: three further subgoals were folded into it after its first three had already merged, and any rule keyed on "all boxes ticked" would have closed it prematurely. The command takes the revision number as an argument; it never decides that a revision is done.

**Ordering within revision 3.** This lands after `/file-plans` (PR #14) because closing a revision whose branch plans are still scattered flat would produce a `rev-N/` directory holding an archive and none of the plans it describes.

## Notes

- The extraction is a cut, not a copy. The section must not survive in both places, or the master plan keeps the growth this exists to stop and the two copies drift.
