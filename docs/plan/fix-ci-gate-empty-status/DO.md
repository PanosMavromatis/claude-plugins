# fix/ci-gate-empty-status

**Status**: active
**Created**: 2026-08-29
**Subgoal**: Fix the empty-status misclassification, and document the `Checks` constraint.

## Tasks

- [ ] Rewrite step 8's result handling to inspect `total_count` / `statuses.length` before `state`: zero statuses means *none configured*, whatever `state` says. Explain the quirk inline so it does not get "simplified" back out.
- [ ] Add the `Checks` constraint to step 8: fine-grained PATs cannot grant it, so `get_check_runs` 403s by design on PAT-backed installs. Keep attempting it, announce the fallback as usual, but do not imply the user misconfigured something.
- [ ] Record both in `CLAUDE.md`'s "GitHub access" section, since they are properties of the mechanism rather than of this command.
