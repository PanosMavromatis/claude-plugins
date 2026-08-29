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

## GitHub access — settled decisions (revision 2)

GitHub operations prefer the GitHub MCP server when it is available, falling back to `gh`. Established by direct probing of the live server on 2026-08-29:

- **Fallback triggers on 404 *or* 403.** A fine-grained PAT lacking access to a repo gets **404**, not 403 — GitHub masks existence of private repos deliberately. A fallback keyed only on 403 would never fire in the case it exists for. Verified: `list_branches` on this repo 404'd before it was added to the PAT's repo list, while `gh api` on the same endpoint succeeded.
- **Announce every fallback, naming the repo and the operation.** e.g. "MCP `merge_pull_request` returned 404 for `PanosMavromatis/workflow-claude` — falling back to `gh pr merge`, which has full `repo` scope." A silent fallback turns a permission boundary into a speed bump; an announced one makes recurrence a legible signal that the PAT's scope should be widened. Never fall back without saying so.
- **`merge_pull_request` cannot delete the branch.** Its parameters are `owner`, `repo`, `pullNumber`, `merge_method`, `commit_title`, `commit_message` — there is no `delete_branch`. `gh pr merge --delete-branch` removes the branch both locally and remotely; the MCP path removes neither. The MCP path must clean up explicitly or hand off to `/clean-gone`.
- **`create_pull_request` takes `body` as a string**, so the MCP path drops the `/tmp/pr-body-<branch>.md` temp-file dance entirely — and with it the heredoc quoting hazard when a body contains backticks or `$`.
- **Tool names are installation-dependent.** They are `mcp__plugin_github_github__*` here, but that prefix encodes how the consumer installed the server. Do not hardcode these names in `allowed-tools`; a consumer with a different install would get an allow-list that matches nothing.
- **Diagnostic before concluding anything from a 404**: `get_me` (identity), the failing call (target access), `search_repositories` with `user:<owner>` (actual PAT scope). Distinguishes "not in PAT scope" from "wrong owner/repo" from "server down".

## Subgoals — revision 2: MCP-preferred GitHub access

- [ ] Rework `/smart-merge`'s GitHub operations to prefer MCP with a `gh` fallback: `pull_request_read` for status/checks, `create_pull_request` (body as a string, dropping the temp file), `merge_pull_request` for the merge. Every fallback announced per the rule above. Phrase availability as "if a GitHub MCP tool is present in your tool list" — there is no shell probe for this.
  > **Branch:** feat/smart-merge-mcp
- [ ] Handle the branch-cleanup divergence: after an MCP merge, explicitly delete the remote branch (`git push origin --delete <branch>`) and the local one, or state that `/clean-gone` is now required. Both paths must end in the same repository state, and the command should say which path it took.
  > **Branch:** feat/smart-merge-mcp
- [ ] Add a pre-merge CI check using `pull_request_read` with `get_check_runs` / `get_status` — currently `/smart-merge` merges without ever looking at CI. Report failing checks and confirm before merging; skip cleanly when the MCP path is unavailable.
- [ ] Resolve the deferred `allowed-tools` drift, now that the reshaping input has arrived. Decide per command whether to allow-list the `gh`/`git` fallback patterns narrowly, and leave MCP tool names off the allow-list (see the portability finding above) so they prompt rather than silently failing to match.
- [ ] Update `README.md` and `CLAUDE.md` for the MCP-preferred convention: the 404-or-403 rule, the announce-on-fallback rule and why it exists, the branch-cleanup divergence, and the tool-name portability constraint.

## Deferred

Not part of this revision — recorded so it isn't lost.

- ~~**`allowed-tools` drift in `/new-branch` *and* `/smart-merge`.**~~ **Un-deferred** — promoted to a revision-2 subgoal above, now that the MCP decision (the "new input" this was waiting on) has landed.

  Original note: **`allowed-tools` drift in `/new-branch` *and* `/smart-merge`.** Both perform writes their frontmatter never allow-lists: `/new-branch` does `Write`, `git add`, `git commit`; `/smart-merge` does `git rm`, `git add`, `git commit`, `git push`, `gh pr create`, `gh pr merge`, and now plan edits. Both allow-list only read-only git — a pre-existing violation of the repo's "keep `allowed-tools` and the body in sync" rule, made more visible (not caused) by this revision. Deferred: new input pending that may significantly reshape it, and it is independent of the plan-file convention.

  Scoping note for when this is picked up: `/smart-merge` needs `Bash(gh pr merge:*)` and `Bash(git push:*)`, which are the two genuinely destructive/outward-facing entries in this plugin — worth allow-listing narrowly, or deliberately leaving off so they keep prompting.
