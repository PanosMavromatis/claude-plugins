# fix/plan-pointer-identity

**Status**: active
**Created**: 2026-08-30
**Subgoal**: Stop writing decaying paths into immutable records

## Tasks

- [ ] Rewrite the plan-pointer bullet in `/smart-merge` step 3: emit the plan's directory name and a resolution hint rather than a path, delete the "resolves permanently" claim, and state why it is a name so a later editor does not turn it back into a path.
- [ ] Add the general rule to `CLAUDE.md`: anywhere this system writes a plan reference into something that cannot later be edited, write the identity and let the reader resolve it the way the commands do. Tie it to the identity-vs-location rule already stated for resolution.
- [ ] Sweep for any other decaying references — grep the commands and docs for places that write a plan or branch path into a record that outlives the layout (PR bodies, commit messages, the branch doc). Fix or explicitly accept each.
- [ ] Amend README's "Known gap" bullet, which describes this as pending. It should describe the fix as landed and keep the workaround note for PRs #1-#11, whose bodies stay broken by design.
