# feat/smart-merge-locate-plan

**Created**: 2026-10-10
**Base**: main at 176c262
**Status**: active

## Purpose

`/smart-merge` still finds its plans by hand. Step 2 resolves the branch plan with an exact
path and then a glob, and step 7 finds the master-plan backlink with `Grep`. Since 2.1.117
the main session has no `Grep`, so PR #8 fell back to read-only shell `grep -n -F`. Neither
step knows the per-goal layout or a revisions index: a per-goal branch plan must be stamped
on its index, and under a revisions index the backlinked subgoal lives in the revision's
`docs/plan/<label>/_TODO.md`, not the root. This branch moves both lookups onto the plugin's
scripts, so `/smart-merge` resolves plans by the same rules `/step` and `/hitl-step` use.

## Scope

- Measure what steps 2 and 7 need in each layout (legacy, per-goal, revisions index), and
  what `locate-plan.sh` and `SUBGOALS_AWK` already report. Decide whether locating the
  backlink needs a new script mode or an existing report covers it.
- Step 2 resolves the branch plan through `locate-plan.sh`.
- Step 7 stamps the resolved index, and locates and edits the backlinked item in the right
  master file, reporting zero or several hits rather than guessing.
- If the library changes: all three `dev/` suites and their mutant passes.
- Verify end to end. The user runs it; `check.py` grades.

## Context

- Master plan `docs/plan/TODO.md`, revision `06-subagent-refactor-R1`: the subgoal after
  PR #8's, which deferred step 7 here.
- Agreed plan `tmp/subagent-refactor-plan.md` §4.2, `/smart-merge` row: step 7.1–7.2 →
  `scripts/locate-plan.sh`; stamps the branch index; master-plan edit in `_TODO.md`.
- The plugin `CLAUDE.md`'s "Grep is allow-listed …" sentence is fixed in the later
  plan-convention subgoal, not here.

## Notes
