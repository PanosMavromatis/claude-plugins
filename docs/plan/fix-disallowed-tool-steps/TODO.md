# fix/disallowed-tool-steps

**Status**: active
**Created**: 2026-10-10
**Subgoal**: revision 06-subagent-refactor-R1 — steps that rely on a tool their command does not allow

## Tasks

- [ ] Measure which steps rely on a tool their command does not allow
  - [ ] When `Grep` and `Glob` are missing from a session whose `allowed-tools` grants them
  - [ ] Every such step across the 11 command files, including any tool gap besides `Grep`, `Glob` and the legacy Step 6 `awk`
- [ ] `check-plan-index.sh` reports a legacy plan's open items, and Step 6 runs it for both layouts
- [ ] Rewrite the remaining steps onto tools their command allows
  - [ ] `/close-revision`'s pointer check
  - [ ] `/step` and `/hitl-step`: the out-of-order lookup, Step 4's subgoal check, Step 5's re-Grep, the investigation paragraph
  - [-] `/smart-merge` step 7
    > **Deferred:** rewritten once, through `scripts/locate-plan.sh`, by the next R1 subgoal.
- [ ] Verify: the three script suites pass, and per-goal-e2e `e4` passes Step 6 (the user runs it)
