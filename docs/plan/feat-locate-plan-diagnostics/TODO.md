# feat/locate-plan-diagnostics

**Status**: active
**Created**: 2026-10-09
**Subgoal**: revision 06-subagent-refactor-R1 — sharper diagnostics from `scripts/locate-plan.sh`

## Tasks

- [ ] Bring the goal-10 test suite, fixtures and answer key into the repository
  - [ ] Choose where it lives (`dev/` or inside the plugin) and what is tracked:
        generators, answer key and grader, or also built fixtures and results
  - [ ] Name the fault wrappers neutrally: the `-trunc` path leaked a hint
  - [ ] Run the suite from the repo against today's script and get today's pass count.
        Re-grading the stored baseline runs gives the goal-10 scores unchanged.
- [ ] Sharpen the `fix:` lines in `scripts/locate-plan.sh`
  - [ ] Create, not restore, a file that was never committed
  - [ ] `git mv` a plan written under the other model
  - [ ] Name the exact goal file, e.g. `TODO/02-two.md`
  - [ ] Say that the directory holds no plan
  - [ ] Remove a header that no file justifies
  - [ ] The suite and mutants still pass, and the spec is updated to match
- [ ] `/step` and `/hitl-step` offer a read-only investigation in the main session on an
      `error` or a failed run, and run it only when the user asks. The lockstep `sed`
      diff stays empty.
- [ ] Re-grade against the goal-10 answer key: 40/40. On every case, at least the best
      wrapper run; the full fix on e07, e08, e08b and e09; no case lower than today. The
      user runs the headless sessions.
