# fix/ci-gate-empty-status

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Fix the empty-status misclassification, and document the `Checks` constraint.

## Tasks

- [x] Rewrite step 8's result handling to inspect `total_count` / `statuses.length` before `state`: zero statuses means *none configured*, whatever `state` says. Explain the quirk inline so it does not get "simplified" back out.
  > **Done:** New "Count before you read state" paragraph, plus the two affected outcomes reworded — "no checks configured" now says *zero check runs and zero statuses*, and "pending" now says *at least one exists and has not concluded*. The quirk is explained inline with an explicit "do not simplify it away".
- [x] Add the `Checks` constraint to step 8: fine-grained PATs cannot grant it, so `get_check_runs` 403s by design on PAT-backed installs. Keep attempting it, announce the fallback as usual, but do not imply the user misconfigured something.
  > **Done:** Stated in the MCP-path paragraph: `get_check_runs` 403s on any fine-grained-PAT install because GitHub offers no `Checks` permission for that token type, so announce the fallback but do not send the user looking for a permission that does not exist. Notes that `get_status` needs `Commit statuses`, which is grantable.
- [x] Record both in `CLAUDE.md`'s "GitHub access" section, since they are properties of the mechanism rather than of this command.
  > **Done:** Added a paragraph covering both, and why neither was visible in the tool schemas — including that the `pending` bug stayed hidden for four cycles because the missing permission made the call 403 before it could return a misleading answer.
