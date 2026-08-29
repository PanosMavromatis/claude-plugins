# Master plan — branch-scoped plan files

**Status**: active

Introduce a two-tier plan convention across the plugin's commands:

- **Master plan** — this file, `docs/plan/DO.md`, lives on `main`. Defines subgoals; each spawns a branch.
- **Branch plan** — `docs/plan/<type>-<slug>/{DO,TODO}.md`, created by `/new-branch`, worked by `/step` / `/hitl-step`, stamped `merged` by `/smart-merge`. **Survives on `main`** — the durable record of how a subgoal was executed.
- **PR body** — carries the distilled description plus a pointer to the branch plan directory. Not a verbatim archive.

Root-level `DO.md` / `TODO.md` are legacy; the commands still read them, with a nudge to migrate.

## Settled design decisions

- **Directory naming**: branch `feat/user-auth` → `docs/plan/feat-user-auth/`. Slash flattened to a hyphen: one level deep, sorts by type, no collision between `feat/export` and `fix/export`.
- **Resolution order** (identical in `/step` and `/hitl-step`, differing only in filename):
  1. explicit path argument
  2. `docs/plan/<flattened-current-branch>/DO.md`
  3. `docs/plan/DO.md` (master)
  4. glob `docs/plan/**/DO.md`, filter out `merged`, ask
  5. root-level `DO.md` (legacy, with migration nudge)
- **Status stamp**: `**Status**: active` written by `/new-branch`; rewritten to `**Status**: merged — PR #<n> — <YYYY-MM-DD>` by `/smart-merge`. Unstamped counts as active.
- **Model inheritance**: a branch inherits the master plan's model (`DO.md` → `DO.md`, `TODO.md` → `TODO.md`); `/new-branch` offers an override so a fiddly subgoal can use the HITL loop under a plain master plan.
- **Merge-time writes**: stamping the branch plan and updating this file's subgoal happen in one commit, on the branch, between `gh pr create` and `gh pr merge`. `main` is never written to directly.

## Subgoals

- [ ] Rewrite plan-file resolution in `/step` and `/hitl-step` to the five-rung priority order above, replacing the current flat glob. Both commands must stay in lockstep; add the `merged` filter and the "N merged plans not shown" line to rung 4.
- [ ] Teach `/new-branch` to create `docs/plan/<flattened-branch>/` with a status-stamped starter plan, seeded from the Scope answer it already collects. Model inherited from the master plan with an override prompt. Add a `> **Branch:**` backlink under this file's corresponding subgoal.
- [ ] Extend `/smart-merge`: read the branch plan; add a pointer line to the PR body; warn (don't block) on unfinished items; after `gh pr create`, stamp the branch plan `merged` and record `> **Done:** <summary> — PR #<n>` under this file's subgoal, in one commit pushed before the merge.
- [ ] Update `README.md` (command table, conventions section) and `CLAUDE.md` (`/step` bullet, plus a new subsection describing the two-tier plan convention and the merge-time stamp contract).

## Deferred

Not part of this revision — recorded so it isn't lost.

- **`/new-branch`'s `allowed-tools` drift.** The command performs `Write`, `git add`, and `git commit` while its frontmatter allow-lists only read-only git — a pre-existing violation of the repo's "keep `allowed-tools` and the body in sync" rule. Deferred: new input pending that may significantly reshape it, and it is independent of the plan-file convention.
