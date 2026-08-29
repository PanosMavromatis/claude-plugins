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

- [x] Rewrite plan-file resolution in `/step` and `/hitl-step` to the five-rung priority order above, replacing the current flat glob. Both commands must stay in lockstep; add the `merged` filter and the "N merged plans not shown" line to rung 4.
  > **Done:** Step 1 of both commands replaced with the five-rung order plus a shared "Status stamp" subsection defining the read contract (`merged` only when a `**Status**:` line starts with `merged`; unstamped counts as active). Sections verified byte-identical between the two commands modulo filename. No `allowed-tools` change needed — `git branch --show-current`, `Glob`, `Grep`, `Read` were already allow-listed in both.
- [x] Teach `/new-branch` to create `docs/plan/<flattened-branch>/` with a status-stamped starter plan, seeded from the Scope answer it already collects. Model inherited from the master plan with an override prompt. Add a `> **Branch:**` backlink under this file's corresponding subgoal.
  > **Done:** New step 6 creates the branch plan (model inherited from whichever master plan exists, ask when both do, `DO.md` when neither); steps 6-7 renumbered to 7-8, with the commit step now staging doc, plan, and the backlinked master plan together. Header carries `**Status**: active`, matching the read contract added in subgoal 1.
  > **Note:** this step adds another `Write` to a command whose `allowed-tools` still allow-lists only read-only git — the drift recorded under Deferred. Unchanged here by design; it will prompt at runtime as it already does for the branch doc.
- [x] Extend `/smart-merge`: read the branch plan; add a pointer line to the PR body; warn (don't block) on unfinished items; after `gh pr create`, stamp the branch plan `merged` and record `> **Done:** <summary> — PR #<n>` under this file's subgoal, in one commit pushed before the merge.
  > **Done:** Step 2 now reads the plan alongside the branch doc and warns on unfinished items; step 3 appends a `Plan:` pointer to the PR body (explicitly *not* the contents, per the 65k cap); step 4 spells out that only the branch doc is deleted; new step 7 stamps the plan and closes the master-plan item in one commit between `gh pr create` and `gh pr merge`; old steps 7-10 renumbered 8-11. Stamp format verified identical across all four commands.
- [x] Update `README.md` (command table, conventions section) and `CLAUDE.md` (`/step` bullet, plus a new subsection describing the two-tier plan convention and the merge-time stamp contract).
  > **Done:** README — all four command-table rows refreshed, and the interim `docs/plan` bullet replaced with two: the two-tier convention and the PR-body-is-a-pointer rule. CLAUDE.md — `/new-branch`, `/step`, `/smart-merge` bullets updated; new "The plan convention" section covering the flattening rule, the five rungs, the four-command stamp contract, the merge-time write window, and the 65k cap; plus a `Plan-file lockstep` bullet in the editing-conventions checklist.

## Deferred

Not part of this revision — recorded so it isn't lost.

- **`allowed-tools` drift in `/new-branch` *and* `/smart-merge`.** Both perform writes their frontmatter never allow-lists: `/new-branch` does `Write`, `git add`, `git commit`; `/smart-merge` does `git rm`, `git add`, `git commit`, `git push`, `gh pr create`, `gh pr merge`, and now plan edits. Both allow-list only read-only git — a pre-existing violation of the repo's "keep `allowed-tools` and the body in sync" rule, made more visible (not caused) by this revision. Deferred: new input pending that may significantly reshape it, and it is independent of the plan-file convention.

  Scoping note for when this is picked up: `/smart-merge` needs `Bash(gh pr merge:*)` and `Bash(git push:*)`, which are the two genuinely destructive/outward-facing entries in this plugin — worth allow-listing narrowly, or deliberately leaving off so they keep prompting.
