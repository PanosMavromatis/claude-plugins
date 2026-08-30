# feat/file-plans-command

**Status**: active
**Created**: 2026-08-30
**Subgoal**: Automate the plan-filing sweep

## Tasks

- [ ] Write `scripts/file-plans.sh`: build the branch→revision map from the master plan's backlinks and enclosing headings, find plan directories sitting flat under `docs/plan/` that carry a `merged` stamp, and print the proposed `git mv` for each. Read-only — it must never move anything. Handle `DO.md` and `TODO.md` masters, and a repo with neither.
- [ ] Make the two unplaceable cases explicit in the script's output: no backlink, and a heading with no revision number. Report them as skipped with the reason, and exit non-zero only on real errors, not on having nothing to do.
- [ ] Test the script against this repo's actual state and against synthetic edge cases — a plan with no backlink, a revision-1 heading, an already-filed plan, an active (unmerged) plan.
- [ ] Write `commands/file-plans.md` with frontmatter following the `/agents-docs-build` precedent: script in `allowed-tools`, `git mv` deliberately omitted. The command runs the script, presents the proposal, confirms, executes, and commits on a branch.
- [ ] Update README and `CLAUDE.md`: the filing sweep becomes `/file-plans`, with the derivation kept as the explanation of how it works rather than as the instruction.
