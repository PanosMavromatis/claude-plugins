# feat/open-revision

**Status**: active
**Created**: 2026-08-30
**Subgoal**: Give revisions a full lifecycle, identified by label

## Tasks

- [ ] Write `scripts/open-revision.sh <label>`: validate the label, refuse if a revision with it already exists (heading or directory), and print the section that would be inserted plus where. Read-only.
- [ ] Write `commands/open-revision.md` following the `/close-revision` precedent — script in `allowed-tools`, writes behind confirmation, section inserted above `## Closed revisions` / `## Deferred`.
- [ ] Switch `scripts/close-revision.sh` from number to label: match `## Subgoals — revision <label>`, derive the destination `docs/plan/<label>/_DO.md`. Keep refusing on open items, missing section, existing destination.
- [ ] Switch `scripts/file-plans.sh` to derive `docs/plan/<label>/` from the heading, and fix the `git mv` destination bug by having `/file-plans` `mkdir -p` before moving. Test that a plan files into a revision directory that does not yet exist.
- [ ] Migrate `rev-2/` → `02-mcp-github-access/` and `rev-3/` → `03-subgoal-plan-management/`, updating the master-plan heading and the closed-revisions pointer. Verify resolution afterwards.
- [ ] Update README and `CLAUDE.md`: the open→work→file→close lifecycle, labels rather than numbers, and the directory-naming rule.
