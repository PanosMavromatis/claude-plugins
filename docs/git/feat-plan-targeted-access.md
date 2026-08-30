# feat/plan-targeted-access

**Created**: 2026-08-29
**Base**: main at 1d025a6
**Status**: active

## Purpose

Make the cost of reading the master plan independent of its size. `/smart-merge` step 7 and `/step` / `/hitl-step` rung 3 both want a single *line* — a `> **Branch:**` backlink, or the next unchecked item — but both currently load the whole file to find it. Locate by `grep -n` and read a bounded window instead.

This replaces the "split the master plan into an index plus per-milestone files" idea recorded under Deferred. Measurement killed that design: the file's size was never the problem, its access pattern was.

## Scope

- `/smart-merge` step 7: locate the backlink by `grep -n`, read a bounded window, edit in place.
- Zero-match guard: a `grep` returning nothing must be **reported**, never silently skipped.
- `/step` and `/hitl-step` rung 3: same treatment for locating the next unchecked item. Their Step 1 sections are byte-identical by contract, so this change must land in both.
- Record the measurement and the rule in `CLAUDE.md`; retire the Deferred item.

## Context

Measured on 2026-08-29 against synthetic master plans built by sampling the real file's subgoal blocks (mean 792 bytes each, 16 blocks in the current 20 KB file).

| Subgoals | Size | ~Tokens | Useful fraction |
|---:|---:|---:|---:|
| 16 (today) | 20 KB | ~4k | 5.4% |
| 100 | 85 KB | ~24k | 0.91% |
| 250 | 197 KB | ~55k | 0.39% |
| 500 | 408 KB | ~113k | 0.19% |
| 1000 | 798 KB | ~221k | 0.10% |

"Useful fraction" is one subgoal block as a share of what is loaded to close one checkbox.

Two findings shape the work:

- **The failure is a cliff, not a curve.** Past ~500 subgoals (2246 lines) the file exceeds the default 2000-line read limit and truncates. `/smart-merge` then looks for a backlink it cannot see, finds nothing, and skips the master-plan update **silently** — the same failure shape as the path-reconstruction bug fixed in PR #8, where a lookup that misses is indistinguishable from having nothing to do.
- **Targeted access removes the cliff; splitting only moves it.** On the 798 KB file, `grep -n` located a backlink in 9 ms and the surrounding 5-line window is 770 bytes — ~200 tokens instead of ~221,000, and flat in file size. A per-milestone file would still be read whole, and one busy milestone can carry 100+ subgoals.

At the user's stated rates (7 branches in an evening during busy periods, sustained for months in a large monorepo), 250 subgoals arrives in 7–25 weeks and 500 in 14–50 weeks. This is a real horizon.

Synthetic files used for the measurement are in the session scratchpad under `planbench/`; they are throwaway and deliberately not committed.

## Notes

- The caveat that makes or breaks this: an LLM handed "update the master plan" reaches for a whole-file read by default. The saving is only real if the prose states the sequence explicitly — locate, then read a window — rather than assuming it.
