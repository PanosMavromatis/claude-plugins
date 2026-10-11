# docs/plan-convention

**Status**: active
**Created**: 2026-10-11
**Subgoal**: revision 06-subagent-refactor-R1 — rewrite the plan-convention sections of the plugin's `CLAUDE.md` and README

## Tasks

- [ ] Re-locate each drift item in today's files, and verify the claims before rewording
  - [ ] Whether `allowed-tools` grants or restricts, from the Claude Code docs
  - [ ] The branch-doc path: `docs/git/<flattened>.md` as practised, or `docs/git/<branch>.md` as the e2e has it
- [ ] Rewrite the plan-convention, lifecycle and artifact sections of `plugins/workflow-claude/CLAUDE.md`
  - [ ] "Do not reintroduce the split" gains the §4.2 distinction: a revision's file is located, not read whole, and a goal file is read whole because it is the unit
- [ ] Rewrite the README: "What's in here" with `agents/` and `references/`, `/master-plan` in the loop diagram, and the lifecycle without `/file-plans`
- [ ] `/new-branch`: drop "always flat", settle the branch-doc path, add an `argument-hint`
- [ ] Check the rewritten prose against the commands and scripts it describes
