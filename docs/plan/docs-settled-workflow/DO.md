# docs/settled-workflow

**Status**: active
**Created**: 2026-08-30
**Subgoal**: Document the settled workflow, including the plan-filing sweep

## Tasks

- [ ] README: add the filing sweep to the branch-lifecycle section — what it is, when to run it, and that a plan's revision is derived from the `## Subgoals — revision N` heading enclosing its backlink rather than chosen. Show the resulting `docs/plan/` shape.
- [ ] README: refresh the conventions bullets — the two-tier plans bullet should carry identity-vs-location plainly, and add one for locate-then-window master-plan access. Amend the PR-body bullet to note that a path pointer decays once plans move, flagging the fix as pending rather than describing it as solved.
- [ ] CLAUDE.md: state the same loop for the model, with the filing sweep, the derivation rule, and an explicit correction of the earlier "judgement worth keeping manual" framing so it does not get cited later.
- [ ] Verify no doc claims a path that the regrouping invalidated — grep both files for `docs/plan/<...>` forms and check each against the current layout.
