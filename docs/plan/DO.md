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

- [x] Rework `/smart-merge`'s GitHub operations to prefer MCP with a `gh` fallback: `pull_request_read` for status/checks, `create_pull_request` (body as a string, dropping the temp file), `merge_pull_request` for the merge. Every fallback announced per the rule above. Phrase availability as "if a GitHub MCP tool is present in your tool list" — there is no shell probe for this.
  > **Branch:** feat/smart-merge-mcp
  > **Done:** Preamble states the rule once; steps 1, 6 and 9 gained MCP paths with `gh` fallbacks; fallback triggers on 404 **or** 403 and is always announced with repo and operation named — PR #1
- [x] Handle the branch-cleanup divergence: after an MCP merge, explicitly delete the remote branch (`git push origin --delete <branch>`) and the local one, or state that `/clean-gone` is now required. Both paths must end in the same repository state, and the command should say which path it took.
  > **Branch:** feat/smart-merge-mcp
  > **Done:** New step 9a deletes remote and local branch on the MCP path (`git branch -d`, not `-D`), skipped on the `gh` path where `--delete-branch` already does it; step 11 reports which path ran — PR #1
- [x] Add a pre-merge CI check using `pull_request_read` with `get_check_runs` / `get_status` — currently `/smart-merge` merges without ever looking at CI. Report failing checks and confirm before merging; skip cleanly when the MCP path is unavailable.
  > **Branch:** feat/smart-merge-ci-prune
  > **Done:** New step 8 with four explicit outcomes — none configured, all passing, failing (named, confirmation required), pending (named, user chooses). Both-paths-failed reports as undetermined, not passing — PR #2
- [x] Resolve the deferred `allowed-tools` drift, now that the reshaping input has arrived. Decide per command whether to allow-list the `gh`/`git` fallback patterns narrowly, and leave MCP tool names off the allow-list (see the portability finding above) so they prompt rather than silently failing to match.
  > **Branch:** fix/allowed-tools-sync
  > **Done:** Principle settled as additive-yes/destructive-no and recorded in `CLAUDE.md`. `/new-branch`, `/smart-merge` and `/clean-gone` synced; `gh pr merge`, `git push origin --delete`, branch deletion, worktree removal and `git rm` deliberately omitted so they keep prompting. `Bash(git push:*)` proved unusable in `/smart-merge` — it matches `git push origin --delete` — which is why `/smart-commit` may allow-list push and `/smart-merge` may not. No MCP names anywhere — PR #4
- [x] Fix the stale remote-tracking ref in `/smart-merge` step 10: `git pull` does not prune, so `origin/<branch>` survives a `--delete-branch` merge. Use `git fetch --prune` (or `git pull --prune`) before reporting. This is not cosmetic — `/clean-gone` finds branches by their upstream showing `[gone]`, and that marking only appears after a prune, so the lifecycle's final command currently depends on a prune the flow never performs. Found by running the flow on PR #1, not by review.
  > **Branch:** feat/smart-merge-ci-prune
  > **Done:** Step 11 now uses `git pull --prune`, with the `/clean-gone` dependency spelled out in the step so it does not get 'simplified' away later — PR #2
- [x] Fix step 10a's ordering in `/smart-merge`: `git branch -d` runs before local `main` is synced, so the branch is not yet reachable from HEAD and `-d` refuses with "not fully merged" on **every** MCP merge. The safety check is correct; the ordering makes it a false alarm, and the step's own advice ("stop and investigate rather than forcing") would halt every cycle. Fix by deleting the remote branch in 10a, then syncing (step 11), then deleting the local branch — i.e. the local delete moves after the pull. Found executing PR #2.
  > **Branch:** fix/smart-merge-10a-ordering
  > **Done:** Cleanup split around the sync — 10a deletes the remote branch, new 11a deletes the local one after `git pull --prune`. The `-d` rationale now states what a refusal distinguishes before versus after the sync — PR #3
- [x] Fix the CI gate's empty-status misclassification in `/smart-merge` step 8. GitHub's combined-status endpoint returns `state: "pending"` with `total_count: 0` for a commit that has **no** statuses — "pending" means "nothing has reported", not "something is running". The gate reads `state` and maps `pending` to "name them and ask whether to wait", so on every repo without CI the MCP path announces phantom pending checks and stops for something that will never arrive. Check `total_count` / `statuses.length` **before** `state`; zero means *none configured*. Masked for four cycles because `get_status` was 403 until the `Commit statuses` permission was granted.
  > **Branch:** fix/ci-gate-empty-status
  > **Done:** Step 8 now counts `total_count` and the result-array lengths before reading `state`; the "none configured" and "pending" outcomes reworded to match, with the quirk explained inline — PR #6
- [x] Document the `Checks` constraint: fine-grained PATs cannot grant it — it is absent from GitHub's permission list for that token type, confirmed against the UI and by a persistent 403 after `Commit statuses` was granted and started working. So `get_check_runs` will 403 on any PAT-backed install and the gate degrades to statuses-only. `/smart-merge` should keep attempting it (a GitHub-App-backed install may have it) but must not imply the 403 is something the user forgot to configure.
  > **Branch:** fix/ci-gate-empty-status
  > **Done:** Stated in step 8's MCP paragraph and in `CLAUDE.md`'s GitHub access section: the 403 is a property of the token type, so announce the fallback but do not send the user after a permission that does not exist — PR #6
- [x] Close the `allowed-tools` gaps in the `/agents-docs-*` commands, found during the survey for the `/smart-merge` pass: ~~`agents-docs-build` allow-lists only its script while performing `Write`, `Edit` and `git add`~~ — **that claim was wrong**: its body *prohibits* those operations, and the survey counted the prohibitions as actions. Script-only is correct there. The real gaps are `agents-docs-init` (no `allowed-tools`) and `agents-docs-codex-init` (**no frontmatter block at all**, so not even a `description`). Kept separate because both init commands write dispatchers via `cat <<'EOF'` heredoc redirects, which is exactly the path `protect-agent-docs.py` lets through on purpose — allow-listing there interacts with the hook and needs its own thought.
  > **Branch:** fix/agents-docs-frontmatter
  > **Done:** `agents-docs-codex-init` gained a whole frontmatter block (it had none, so no `description` either); `agents-docs-init` gained `allowed-tools`, with `Bash(cat:*)` deliberately omitted so the dispatcher heredoc keeps prompting. The `agents-docs-build` claim in this subgoal was wrong and is corrected above. `CLAUDE.md` now records that the allow-list and the `PreToolUse` hook are orthogonal layers — PR #7
- [x] Update `README.md` and `CLAUDE.md` for the MCP-preferred convention: the 404-or-403 rule, the announce-on-fallback rule and why it exists, the branch-cleanup divergence, and the tool-name portability constraint.
  > **Branch:** docs/mcp-convention
  > **Done:** README gained two conventions bullets (fallback rule, cleanup divergence) and a refreshed `/smart-merge` row; CLAUDE.md gained a "GitHub access" section documenting each rule beside the case that produced it, plus a refreshed compose bullet. The sweep caught one stale mechanism-specific claim in the plan-convention section — PR #5

## Subgoals — revision 3: plan layout at scale

Prompted by seven branch directories accumulating under `docs/plan/` in one evening. The concern is not this repo, which is small, but monorepos where that branch rate is normal for months at a time.

The organising decision: **do not adopt a taxonomy of goals and subgoals.** Classifying a branch by topic forces a judgement at creation time, when the shape of the work is least clear, and fails on the branches that touch two areas — which most do. Two cheaper axes exist. Grouping by **milestone** costs nothing, because exactly one is open at any moment; this file already does it informally via its `## Subgoals — revision N` headings. Grouping by **component** in a monorepo is a real taxonomy, but its authoritative source already exists as the directory tree under `docs/agents/`, so it should be read from there rather than invented a second time.

- [x] Decouple a branch plan's identity from its location: rewrite rung 2 in `/step` and `/hitl-step` to search for a directory *named* `<flattened-branch>` anywhere under `docs/plan/`, instead of hardcoding `docs/plan/<flattened-branch>/<file>`. Branch names are unique per repo, so the name alone is a sufficient key. Multiple matches mean a stale copy — list and ask, never guess. Rung 4 already globs `docs/plan/**/` and needs no change. This is a prerequisite for any regrouping: once it lands, plans can be moved by `git mv` with nothing else to update, so the grouping decision can be deferred to when the right shape is obvious rather than committed to now.
  > **Branch:** feat/plan-path-decoupling
  > **Done:** Rung 2 in `/step` and `/hitl-step` now resolves a plan by directory *name* anywhere under `docs/plan/` (flat path first, then recursive glob), so the layout below `docs/plan/` is free and plans can be regrouped by `git mv` with nothing to update. Exposed and fixed a latent `/smart-merge` bug: step 2 reconstructed the plan path, so a moved plan would have read as absent and the merge stamp would have been skipped silently. `CLAUDE.md` now states the general rule — reconstructing a plan path is a bug — plus the no-taxonomy rationale and the milestone/component guidance for a future grouping — PR #8
- [x] Exercise the decoupling by actually regrouping: `git mv` the accumulated branch plans into `docs/plan/rev-2/` and `docs/plan/rev-3/`, and verify by execution that rungs 2, 3 and 4 all still resolve against a nested layout — including rung 2's multi-match branch, which had never been reached.
  > **Branch:** chore/plan-regroup
  > **Done:** Nine top-level entries became four (`DO.md`, the in-flight plan, `rev-2/`, `rev-3/`), all by `git mv` recorded as renames, with no command touched. All four rung checks passed against the nested layout. Two findings: rung 2's multi-match branch had never executed before and needed a manufactured collision to reach; and rung 4 filtered 9 merged against 2 active after one evening, while nesting stayed invisible to its `**` glob — confirming directory grouping does nothing for master-plan growth, which stays filed under Deferred — PR #9

## Deferred

Not part of this revision — recorded so it isn't lost.

- ~~**`allowed-tools` drift in `/new-branch` *and* `/smart-merge`.**~~ **Un-deferred** — promoted to a revision-2 subgoal above, now that the MCP decision (the "new input" this was waiting on) has landed.

  Original note: **`allowed-tools` drift in `/new-branch` *and* `/smart-merge`.** Both perform writes their frontmatter never allow-lists: `/new-branch` does `Write`, `git add`, `git commit`; `/smart-merge` does `git rm`, `git add`, `git commit`, `git push`, `gh pr create`, `gh pr merge`, and now plan edits. Both allow-list only read-only git — a pre-existing violation of the repo's "keep `allowed-tools` and the body in sync" rule, made more visible (not caused) by this revision. Deferred: new input pending that may significantly reshape it, and it is independent of the plan-file convention.

  Scoping note for when this is picked up: `/smart-merge` needs `Bash(gh pr merge:*)` and `Bash(git push:*)`, which are the two genuinely destructive/outward-facing entries in this plugin — worth allow-listing narrowly, or deliberately leaving off so they keep prompting.

- **Master-plan growth is a context problem, not a cosmetic one.** `docs/plan/DO.md` is one flat file, read in full by rung 3 whenever `/step` runs on `main`, and read *and rewritten* by `/smart-merge` on every merge. At a few hundred subgoals carrying `> **Done:**` annotations, closing a single checkbox means loading the entire project history into context. Directory clutter is a browsing annoyance that costs a person a second; this cost recurs on every invocation and grows without bound.

  Likely shape of the fix, not yet designed: apply the same decoupling one level up, so the master plan becomes an **index of milestone plans** rather than a flat list of every subgoal ever. Each revision's subgoals live in that revision's own file; `/smart-merge` then rewrites a small closed file instead of a growing one, and rung 3 loads an index. Depends on the revision-3 subgoal above having landed. Worth confirming the failure is real before building for it — measure a plausible worst-case file rather than assuming.

- **Component axis for monorepos.** A monorepo wants `docs/plan/<component>/…`, which is a genuine taxonomy rather than a free one. Do not author a second list of components: the source of truth is already the directory tree under `docs/agents/`, per the monorepo extension in `CLAUDE.md`. A component grouping that reads from there stays consistent with the agent-docs layout by construction; one that maintains its own list will diverge.
