# fix/plan-pointer-identity

**Status**: active
**Created**: 2026-08-30
**Subgoal**: Stop writing decaying paths into immutable records

## Tasks

- [x] Rewrite the plan-pointer bullet in `/smart-merge` step 3: emit the plan's directory name and a resolution hint rather than a path, delete the "resolves permanently" claim, and state why it is a name so a later editor does not turn it back into a path.
  > **Done:** The bullet now emits `Plan: `feat-user-auth` under `docs/plan/``, the false "resolves permanently" claim is gone, and a paragraph states why it is a name — including the instruction not to turn it back into a path, since a path looks more helpful and is the natural thing for an editor to "fix".
- [x] Add the general rule to `CLAUDE.md`: anywhere this system writes a plan reference into something that cannot later be edited, write the identity and let the reader resolve it the way the commands do. Tie it to the identity-vs-location rule already stated for resolution.
  > **Done:** `CLAUDE.md` carries the rule with the distinction that makes it decidable: a path is fine in anything re-derived each time it is used (a `git add`, a report), provided it is the *resolved* path; it is wrong in anything written once and read later (a PR body, a commit message, a comment). Also records that PRs #1-#11 keep their broken paths deliberately.
- [x] Sweep for any other decaying references — grep the commands and docs for places that write a plan or branch path into a record that outlives the layout (PR bodies, commit messages, the branch doc). Fix or explicitly accept each.
  > **Found by the sweep:** step 7's commit example hardcoded `git add docs/plan/feat-user-auth/DO.md` — a reconstructed flat path that is simply wrong for a filed plan. Fixed to stage the path resolved in step 2, and the example now deliberately shows a *filed* plan (`docs/plan/rev-3/…`) rather than the more common flat one, because an example showing the flat case invites reconstruction. Nothing else in the commands writes a plan path into a durable record: the step 7 commit message carries no path, and `/new-branch`'s paths are all creation-time and flat by definition.
- [x] Amend README's "Known gap" bullet, which describes this as pending. It should describe the fix as landed and keep the workaround note for PRs #1-#11, whose bodies stay broken by design.
  > **Done:** The bullet now describes the pointer as name-based rather than flagging a pending gap, and keeps the read-older-PRs-as-names note, which stays true permanently.
