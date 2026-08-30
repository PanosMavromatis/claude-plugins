# feat/open-revision

**Created**: 2026-08-30
**Base**: main at e2b61b5
**Status**: active

## Purpose

Give revisions a full lifecycle. Today they can be closed but never opened — a revision comes into existence when someone types a `## Subgoals — revision N` heading by hand, which is undocumented, easy to get subtly wrong, and the reason `/file-plans` has a latent bug nobody hit. And they are identified by a bare number, which says nothing about what the revision was for.

`/open-revision <label>` creates one, and a **label** replaces the number: `03-subgoal-plan-management` sorts by its own ordinal prefix and says what it covers, so a directory listing and a master-plan heading each read without cross-referencing the other.

## Scope

- `scripts/open-revision.sh` + `commands/open-revision.md`.
- Label-based identity throughout `close-revision.sh` and `file-plans.sh`; a revision's directory becomes `docs/plan/<label>/`.
- Fix the `git mv` destination bug in `/file-plans`.
- Migrate `rev-2/` and `rev-3/`.
- README and `CLAUDE.md`.

## Context

**The label is the identity, one level up.** Branch plans already resolve by directory name rather than path, so a plan can be regrouped freely. Applying the same rule to revisions means the label — not an ordinal position in a sequence — is what identifies a revision, in the heading, in the directory name, and in the argument to `/close-revision`. The numeric prefix is a sorting convention inside the label, not a separate identifier.

**A latent bug surfaced while designing this.** `/file-plans` proposes `git mv docs/plan/<name> docs/plan/rev-N/<name>` without ensuring the destination exists, and `git mv` fails hard on a missing destination directory — verified, exit 128. It has only ever worked because `rev-2/` and `rev-3/` were created by hand during the regrouping cycle, before the command existed. A revision opened today and filed tomorrow would fail on the first plan. The fix is a `mkdir -p` in the command and is independent of labelling; it is included here because thinking about how a freshly opened revision gets its directory is what exposed it.

**Revision 1 stays as it is.** Its heading is a bare `## Subgoals` with no revision identifier at all. It predates the convention, cannot be closed by `/close-revision`, and will not gain a label. Migrating it would mean inventing a label for work that was never organised as a revision.

## Notes

- `/open-revision` cannot be dogfooded on the revision that builds it — this one was opened by hand. It gets tested against fixtures and will open revision 5 for real whenever there is one.
