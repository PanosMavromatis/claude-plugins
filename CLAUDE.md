# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude Code **plugin** (`.claude-plugin/plugin.json`) that ships a curated set of slash commands, plus a couple of supporting hooks (`hooks/`) and helper scripts (`scripts/`). There is no build and no test suite; aside from the small Python/shell hooks and scripts, every artifact is a Markdown command in `commands/`, and edits are usually to the prompt text inside those Markdown files.

When the plugin is installed in a consuming project, files under `commands/` become available as `/<filename-without-md>` slash commands.

## Command-file format

Each file in `commands/` is a Markdown prompt. Optional YAML frontmatter configures Claude Code's harness:

- `allowed-tools:` — restricts which tools the command can call. Patterns are prefix-matched: `Bash(git status:*)` permits any `git status …` invocation without prompting, whereas a blanket `Bash(git:*)` would also silently authorize destructive ops like `git reset --hard` or `git branch -D`. The convention here (see "Conventions") is to allow-list read-only diagnostics plus exactly the writes a command performs, and leave everything else off so it prompts.
- `description:` — shown in the slash-command picker.
- `argument-hint:` — placeholder shown next to the command name.
- `$ARGUMENTS` inside the body is substituted with whatever the user typed after the command name.

When editing a command, keep `allowed-tools` and the prompt body in sync — a step that says "run `git push`" but omits `Bash(git push:*)` from `allowed-tools` will trigger a permission prompt every invocation.

## How the commands compose

The commands are designed to chain, not just stand alone. The intended end-to-end loop in a consuming project:

```
/new-branch  →  /step or /hitl-step (loop)  →  /smart-commit (loop)  →  /smart-merge  →  /clean-gone
                                                                                             │
                                                              (periodically) /file-plans ────┘
                                                     (when a revision ends) /close-revision N
```

- **`/new-branch`** creates `<type>/<slug>`, writes `docs/git/<branch>.md` (purpose, scope, context) and a status-stamped branch plan at `docs/plan/<type>-<slug>/` — always flat, since the directory's *name* is what the other commands resolve by. The doc is a working artifact for the branch's lifetime; the plan outlives it.
- **`/step`** executes the next unchecked item from a `DO.md`; **`/hitl-step`** does the same against a `TODO.md` but with a richer status-marker model (`[ ] [~] [x] [!] [-]`) and inline `> **Q:** / > **A:**` logging under each goal so reasoning survives `/clear` or compaction. Both resolve the plan file through the five-rung order described under "The plan convention" below. **Their Step 1 sections are byte-identical apart from the filename — keep them that way**; drift between them is a bug you only hit on whichever command you use less.
- **`/smart-commit`** invokes `/agents-docs-update` via the SlashCommand tool, then handles any version bump (tag + component-manifest sync), commits, tags, and pushes. It deliberately delegates all doc-sync logic rather than duplicating it.
- **`/smart-merge`** reads `docs/git/<branch>.md` and the branch plan to draft the PR title/body, deletes the doc as part of the merge (so it stays in branch history but doesn't pollute `main`), stamps the plan `merged` and closes the master-plan item, gates on CI, then merges — preferring the GitHub MCP server and falling back to `gh`. It deletes the doc but **never** the plan. See "GitHub access" below.
- **`/file-plans`** files merged branch plans into revision directories under `docs/plan/`, deriving each plan's revision from the master-plan heading its backlink sits under. Runs out of band from the branch lifecycle — periodically, not per merge. The bundled `scripts/file-plans.sh` proposes; the command confirms, moves and commits. See "Filing merged plans" below.
- **`/clean-gone`** deletes local branches whose upstream is `[gone]` (deleted on the remote, e.g. after a merge) and their worktrees. It is confirmation-required and warns prominently when more than one branch is in scope. It is the `workflow-claude` equivalent of `commit-commands`' `/clean_gone`, ported so the branch lifecycle is self-contained — but adapted to this plugin's confirm-before-delete and no-placeholder conventions (the original deletes without confirmation).

`/agents-docs-update` is the shared module for keeping documentation in sync with staged changes — it's both standalone and imported by `/smart-commit`. When editing one, consider whether the change belongs in the shared module instead.

## The plan convention (consuming-project convention)

Plans are two-tier, and unlike the branch doc, **both tiers are durable and land on `main`**:

- **Master plan** — `docs/plan/DO.md` or `docs/plan/TODO.md`. Its items are subgoals, each spawning a branch. Long-lived.
- **Branch plan** — `{DO,TODO}.md` inside a directory named for the branch with `/` flattened to `-` (`feat/user-auth` → `feat-user-auth/`). Flattening avoids a `docs/plan/feat/` pseudo-namespace and stops `feat/export` and `fix/export` colliding.

**The flattened name is the plan's identity; its path is not.** `/new-branch` always creates the directory flat, directly under `docs/plan/`, but `/step`, `/hitl-step` and `/smart-merge` all resolve it by *searching for a directory of that name anywhere beneath `docs/plan/`*. Branch names are unique per repo, so the name alone is a sufficient key. The layout below `docs/plan/` is therefore deliberately unconstrained: plans can be regrouped into milestone or component directories with `git mv`, at any time, with no command to update and no migration.

**Filing merged plans is a lookup, not a judgement.** Branch plans are never deleted, so `docs/plan/` gains one flat directory per merged branch. They are periodically swept into revision directories — this repo's own history calls that step "the filing sweep" — and which directory a plan belongs to is **already determined**: `/new-branch` writes its `> **Branch:**` backlink beneath a specific `## Subgoals — revision N` heading in the master plan, so the mapping is recoverable mechanically. `/file-plans` (backed by the bundled `scripts/file-plans.sh`) automates the sweep on that basis.

```bash
awk '/^## Subgoals/{h=$0} /^[[:space:]]*> \*\*Branch:\*\*/{print $NF, h}' docs/plan/DO.md
```

An earlier note in this file's history described the choice of revision directory as "the one judgement worth keeping manual", and cited the no-taxonomy argument for it. **That was wrong** and should not be repeated: nothing is being classified at filing time, only read back from a classification that `/new-branch` recorded for free as a side effect of writing the backlink. The no-taxonomy argument applies to inventing a topical hierarchy at branch-creation time, which is a genuine judgement made when the work is least understood; it does not apply to a derivation. Two cases genuinely resist derivation and must be reported rather than guessed: a branch created without `/new-branch` has no backlink, and a `## Subgoals` heading carrying no revision number gives nothing to derive from. Leave those flat.

**Paths written into permanent records decay; identities do not.** `/smart-merge` puts a `Plan:` pointer in each PR body, and PR bodies are effectively immutable. Because plan locations are deliberately free, a path pointer breaks the moment a plan is filed — the first sweep silently invalidated seven of them, including the pointer in the PR that performed the move. The pointer is therefore a **name**: `Plan: \`feat-user-auth\` under \`docs/plan/\``, which a reader resolves the way every command does. Same rule as resolution, applied to records instead of lookups; do not "improve" it back into a path.

The bodies of PRs #1-#11 keep their broken paths. They are readable as names, and rewriting merged history to repair a pointer is not worth the risk — but treat a `Plan:` path in an older PR as a name to search for, not a path to follow.

The distinction that governs this: a path is fine in anything **re-derived each time it is used** — a `git add` in a command, a report to the user — provided it is the resolved path and not a reconstructed one. It is wrong in anything **written once and read later**: a PR body, a commit message, a comment. Ask which kind of thing you are writing into.

**`/file-plans` and its script split responsibilities the same way `/agents-docs-build` does.** `scripts/file-plans.sh` is read-only and deterministic: it builds the branch→revision map from the master plan, finds plan directories sitting flat under `docs/plan/` with a `merged` stamp, and *prints* the proposed `git mv` commands. It never moves, stages or commits — so it is safe in a hook or CI, and the command owns every write. `/file-plans` runs it, shows the output verbatim, confirms, executes the printed commands unchanged, and commits on a branch. `Bash(git mv:*)` is deliberately absent from the command's `allowed-tools`, per additive-yes/destructive-no.

The script's `awk` anchors the backlink match to `^[[:space:]]*`. That is load-bearing rather than tidy: without it, prose that merely *mentions* `> **Branch:**` matches too — and the master plan's own paragraph explaining this mechanism does exactly that, so an unanchored pattern misparses the file that documents it.

**Closing a revision extracts it from the master plan.** `/close-revision N` (backed by `scripts/close-revision.sh`) cuts the `## Subgoals — revision N` section out of `docs/plan/DO.md` and writes it to `docs/plan/rev-N/_DO.md`, leaving a one-line pointer. Without this the master plan accumulates every subgoal the project has ever completed, each with its `> **Done:**` annotation, and never sheds any of it.

The archive is `_DO.md`, **never** `DO.md`. Plan resolution globs `docs/plan/**/DO.md` and matches on filename, so an archive named `DO.md` would be indistinguishable from a branch plan and — carrying no `merged` stamp — would count as active and be offered in the disambiguation prompt as somewhere to do work. The underscore keeps a finished revision out of resolution entirely rather than merely filtered from it, which is the correct behaviour; rung 1's explicit path still reaches it. An earlier design instead stamped the archive `closed` and widened the four-command status contract to accept that value; the rename is strictly better and that contract still accepts only `merged`. Do not "normalize" the filename.

The extraction is a **cut**, not a copy — a section surviving in both files defeats the purpose and lets the copies drift — and the archive is **verbatim**, since summarizing a closed revision destroys the record the two-tier convention exists to keep. Run `/file-plans` before `/close-revision`, or `rev-N/` holds an archive describing plans still sitting flat elsewhere.

**Whether a revision is finished is the user's call and is never inferred.** Subgoals can be added to a revision whose earlier items have all merged — this repo's revision 3 took three more after its first three shipped — so any rule keyed on "all boxes ticked" would close revisions prematurely. The script refuses on unchecked items as a safety net, not as the decision.

**The layout in this repo, as an example of the above.** Merged plans are grouped by revision — `docs/plan/rev-2/<flattened-branch>/`, `docs/plan/rev-3/…` — while the master plan and any in-flight plan sit flat at the top level. `/new-branch` always creates flat; a plan is filed into its revision directory later, typically when the revision closes. Nothing enforces this and no command knows about it: it is one possible use of the freedom described above, not a convention to preserve. A consuming project can group differently, or not at all.

That decoupling is the answer to plan-directory sprawl, and it is deliberately not a taxonomy. Classifying a branch by topic at creation time demands a judgement when the shape of the work is least clear, and fails on branches that touch two areas — most do. Resolving by name instead defers the grouping decision indefinitely, to whenever the right shape is obvious. When a grouping is eventually wanted, prefer axes that cost nothing to assign: **milestone** (exactly one is open at a time) over topic, and for a monorepo's **component** axis read the component list from the `docs/agents/` tree rather than authoring a second one.

Any code that reconstructs a branch plan's path instead of searching for it is a bug: a moved plan reads as absent, and the caller silently does nothing — in `/smart-merge`'s case, skipping the merge stamp and leaving the plan marked `active` forever. Search by name, and pass the resolved path along.

`/step` and `/hitl-step` resolve in strict priority order, stopping at the first rung that yields a file:

1. explicit path argument — if it doesn't resolve, **stop**, never fall through (a typo would silently run a different plan);
2. a directory named `<flattened-current-branch>` anywhere under `docs/plan/`, holding `<file>` — the answer on a feature branch. Try the exact flat path `docs/plan/<name>/<file>` first and fall back to the glob `docs/plan/**/<name>/<file>`; the ordering is a cost optimisation for large trees, not a correctness requirement (`**` does match zero path segments — verified in Python, bash `globstar` and Node). Several matches mean a copied, not moved, plan — list and ask;
3. `docs/plan/<file>` — the answer on `main`;
4. glob `docs/plan/**/<file>`, filter out merged plans, ask if several remain;
5. legacy root-level `DO.md`/`TODO.md`, with a migration nudge.

Rungs 2 and 3 mean neither normal working position ever prompts, which is what keeps accumulated merged plans from turning rung 4 into a permanent tax.

**The status stamp is a contract between three commands.** `/new-branch` writes `**Status**: active`; `/smart-merge` rewrites it to `**Status**: merged — PR #<n> — <date>`; `/step` and `/hitl-step` read it to filter rung 4. A plan counts as merged **only** if a `**Status**:` line's value begins with `merged` — everything else, including no stamp at all, counts as active. That asymmetry is deliberate: plans merged outside `/smart-merge` never get stamped, and a stale option in a list is cheaper than a hidden live plan. When changing the format, change all four commands together.

**Merge-time writes go on the branch, not `main`.** `/smart-merge` stamps the plan and closes the master-plan item in one commit between PR creation and merge — the only window where the PR number exists and the branch still does. (Stated mechanism-neutrally on purpose: either path may create the PR — see "GitHub access".) Recording it after the merge would mean committing directly to `main`, which branch protection commonly forbids.

**Master-plan access is locate-then-window, never a whole-file read.** A branch plan covers one branch and stays small; the master plan accumulates every subgoal of every revision with its `> **Done:**` annotation and grows without bound. `/smart-merge` step 7 and Step 2 of `/step` / `/hitl-step` each need exactly one line out of it — a `> **Branch:**` backlink, or the first unchecked item — so they `Grep` for it and `Read` a bounded window, and the prose says so explicitly because the default instinct on "update the master plan" is to read the file.

Measured 2026-08-29 against synthetic master plans built by sampling this repo's own subgoal blocks (mean 792 bytes each). At 250 subgoals the file is ~197 KB / ~55k tokens and **0.39%** of a whole-file read is the block being edited. At ~500 subgoals it passes 2246 lines, exceeds the default 2000-line read limit, and **truncates** — after which `/smart-merge` looks for a backlink it cannot see and, without a guard, skips the master-plan update silently, while a step command could report "all tasks complete" about a file it only partly read. `Grep` located a backlink in a 798 KB file in 9 ms; the window around it is 770 bytes. Locating is flat in file size, which is the whole point.

**The write side is half the rule.** Targeting the read alone leaves the saving half-done: a `Write` that rewrites the whole file costs what the read cost, and a loop that re-reads the plan each iteration multiplies it by N. So `/step` and `/hitl-step` edit in place with `Edit` and re-`Grep` between iterations rather than re-reading. `/step` had no `Edit` in its `allowed-tools` at all until this was noticed, which forced a whole-file `Write` — a case of the allow-list quietly dictating an access pattern. `Write` stays in both for creating a plan file from scratch.

This replaced an earlier plan to split the master plan into an index plus per-milestone files. That design was rejected **by measurement**: a milestone file is still read whole and a busy milestone carries 100+ subgoals, so it moves the cliff instead of removing it, at the cost of a format change, a migration and a new resolution rung. Size was never the problem; the access pattern was. Do not reintroduce the split without new evidence — and note that `Grep` is allow-listed in all three commands while `Bash(grep:*)` deliberately is not, so the prose must say `Grep` or every invocation prompts.

**A silent miss is a bug.** Anywhere a command looks up a plan item by pattern, zero hits must be reported and disambiguated — "this branch legitimately has no master-plan item" is a different outcome from "the lookup failed", and both are silence unless the command distinguishes them. This is the same failure shape as reconstructing a plan path instead of resolving it: a lookup that misses is indistinguishable from having had nothing to do, and it leaves a subgoal open forever with no trace of why.

**The PR body points at the plan; it does not contain it.** GitHub caps PR bodies at 65,536 characters, and a HITL plan's `> **Q:** / > **A:**` logs can approach that. Since the plan lands on `main`, a `Plan: docs/plan/…/DO.md` pointer resolves permanently — don't add logic that inlines plan contents into a PR body.

## The agent-docs system (consuming-project convention)

Several commands assume the consuming project uses a specific layout for agent context. This layout is **not** present in this repo (this repo is the plugin, not a consumer), but the commands manipulate it:

- `CLAUDE.md` at the consumer's repo root is an **`@import` dispatcher only** — two lines that import `docs/agents/core.md` and `docs/agents/claude.md`. It is not a content file.
- `docs/agents/core.md` — tool-agnostic context (shared with Codex, Cursor, etc.).
- `docs/agents/claude.md` — Claude-Code-specific context (skills, slash commands, workflow patterns).
- `docs/agents/codex.md` — Codex-specific review priorities and gotchas.
- `AGENTS.md` and `AGENTS.override.md` are **generated artifacts** built from the `docs/agents/` sources by `/agents-docs-build` (bundled with this plugin at `scripts/build-agents-md.sh`). `/agents-docs-check` (bundled at `scripts/check-agents-md.sh`) verifies they are in sync — it re-runs the build into a temp dir and diffs, useful for pre-commit hooks or CI in the consumer project.
- This plugin ships `hooks/protect-agent-docs.py` (registered via `hooks/hooks.json`) as a PreToolUse hook that blocks `Write|Edit|MultiEdit` against `CLAUDE.md`, `AGENTS.md`, and `AGENTS.override.md` — root-level and per-component (`<path>/CLAUDE.md`, `<path>/AGENTS.md`, `<path>/AGENTS.override.md`). Bash redirects pass through, which is how the build script writes the generated files and how `/agents-docs-init` writes dispatchers via `cat <<'EOF'` heredocs. Each protected file uses a sentinel inside the relevant `docs/agents/[<path>/]` directory (`core.md` for `CLAUDE.md`/`AGENTS.md`, `codex.md` for `AGENTS.override.md`); when the sentinel is absent the write passes through, so projects that haven't adopted the convention (or component dirs that don't exist yet) aren't blocked.

`/agents-docs-init` migrates a legacy single-file `CLAUDE.md` into this split layout. `/agents-docs-codex-init` generates the Codex sidecar. `/agents-docs-update` edits the `docs/agents/*.md` sources (never the generated artifacts) and invokes `/agents-docs-build` when `core.md` or `codex.md` changed.

**Monorepo layout (extension).** The same pattern repeats per-component: a consumer with a monorepo can have `<path>/CLAUDE.md` dispatchers (e.g. `ui/CLAUDE.md`, `api/CLAUDE.md`) backed by `docs/agents/<path>/{core,claude,codex}.md` sources, with `<path>/AGENTS.md` and `<path>/AGENTS.override.md` generated by `/agents-docs-build`. Nesting is unrestricted — recursion follows the directory tree. The **source of truth for which components exist is the directory tree under `docs/agents/`**: creating `docs/agents/<comp>/` declares a new component, and the init commands detect it on next run. In a non-monorepo project, `docs/agents/` has no subdirectories and every command behaves exactly as it did before, at no extra cost. Both the bundled `protect-agent-docs.py` hook and the bundled build/check scripts handle component paths at any nesting depth, so consumers do not need to author their own equivalents.

**`allowed-tools` and the hook are orthogonal layers.** `protect-agent-docs.py` is a `PreToolUse` hook on `Write|Edit|MultiEdit`; it fires regardless of what a command allow-lists. So allow-listing `Write` in `/agents-docs-init` or `/agents-docs-codex-init` does not weaken protection of `CLAUDE.md`/`AGENTS.md`/`AGENTS.override.md` — the hook still blocks those paths once the sentinel exists, and the allow-list only ever covers the `docs/agents/` sources. Conversely, the allow-list cannot re-enable a hook-blocked write. Reason about the two separately; neither substitutes for the other.

`/agents-docs-build`'s script-only `allowed-tools` is correct, not drift: its body prohibits `git add`, direct `Write`/`Edit` of generated files, and source edits, so the script is genuinely all it runs.

When editing the doc-related commands here, do not add logic that writes to any `CLAUDE.md`, `AGENTS.md`, or `AGENTS.override.md` directly — root or component — it would (correctly) be blocked by the consumer's hook. Always edit the `docs/agents/[<path>/]*.md` sources and let the build script regenerate the rest.

## GitHub access (MCP preferred, `gh` fallback)

`/smart-merge` is the only command that touches the GitHub API; everything else in the pipeline is local git, which no MCP server covers. It prefers a GitHub MCP tool when one is present in the tool list — there is no shell probe for availability, so the command phrases it as a judgement, not a branch — and falls back to `gh` otherwise.

**Fall back on 404 *or* 403, and say so.** A fine-grained PAT that does not cover the repository returns **404**, because GitHub masks the existence of private repos; one that covers the repo but lacks a permission returns **403**. Both occur in practice — the plugin's own development hit 404 (repo outside the PAT's selection) and 403 (`Checks` permission missing) in consecutive cycles. A rule keyed only on 403 would never fire in the first case.

Every fallback is announced naming the repository and the operation. This is load-bearing, not decoration: a silent fallback turns a permission boundary into a speed bump nobody notices, and makes a deliberately narrow PAT pointless. Announced, a repeated fallback is a legible signal to widen the token's scope. Fall back at operation boundaries, never mid-sequence, so one operation completes on one mechanism.

**The two paths clean up differently, and that dictates step order.** `gh pr merge --delete-branch` deletes the branch locally and remotely in one call. `merge_pull_request` takes no `delete_branch` parameter and deletes **neither** — verified against the live API, not inferred. So the MCP path cleans up explicitly, in this order: delete the remote branch (10a) → sync `main` with `--prune` (11) → delete the local branch (11a). The order is not stylistic: `git branch -d` evaluates reachability from `HEAD`, so before the sync it refuses on *every* merge — a correct check firing for the wrong reason. Running it after the sync is what makes a refusal mean "the merge did not land". Use `-d`, never `-D`.

`--prune` in step 11 is likewise required rather than tidy: `/clean-gone` finds branches by their upstream showing `[gone]`, and that marking only appears once the stale remote-tracking ref is pruned.

**Two CI-gate facts, both learned by calling the API.** `get_check_runs` returns 403 on any fine-grained-PAT-backed install: GitHub does not offer a `Checks` permission for that token type, so the gate degrades to commit statuses there and the 403 is expected rather than a misconfiguration. And `get_status` returns `state: "pending"` with `total_count: 0` for a commit with no statuses at all — "pending" meaning "nothing reported", not "something running" — so step 8 counts results *before* reading `state`. Reading `state` first makes every CI-less repo look like work is in flight. Neither fact is visible in the tool schemas; the second stayed hidden for four cycles because the `Commit statuses` permission was missing and the call 403'd before it could return a misleading answer.

**Never hardcode MCP tool names.** They are `mcp__plugin_github_github__*` in one install and something else in another, so an `allowed-tools` entry matches nothing on a consumer's machine and fails silently — where a missing entry merely prompts. See "Scoped `allowed-tools`" below.

## Coexistence with `commit-commands`

This plugin is loaded deliberately per-project via `claude --plugin-dir`, and overlaps with the official `commit-commands` plugin (`/commit`, `/commit-push-pr`, `/clean_gone`) — `/smart-commit`, `/smart-merge`, and `/clean-gone` supersede those with richer, confirm-first behaviour. The two should not both be active: running the `commit-commands` versions silently skips doc-sync, version/tag handling, and the branch-doc PR flow.

To make that self-enforcing, the plugin ships a second hook, `hooks/remind-disable-commit-commands.py` (registered in `hooks/hooks.json` as a `SessionStart` hook). Because it only runs when `workflow-claude` is loaded, its mere firing signals a `--plugin-dir` launch; it then checks the effective `enabledPlugins` state (merging user/project/local `settings.json`) and, if `commit-commands` is still enabled, surfaces a recommendation to disable it for that project. It is silent once disabled. The recommendation reaches the user via the hook JSON's top-level `systemMessage` field (printed to the terminal at launch); `additionalContext` is *model*-facing and `stderr`/`exit 2` was not surfaced in testing, so neither is sufficient on its own — see `_meta/plugin-conflict-report.md` §8. The full rationale, the consumer `.claude/settings.json` override template, and the `security-guidance` interaction note live in that report and the README. When editing this hook or `hooks.json`, keep that report in sync.

**Manifest gotcha — do not "declare" the hooks path.** `.claude-plugin/plugin.json` must **not** carry a `hooks` key pointing at `hooks/hooks.json`. Claude Code auto-loads that standard file by convention; a manifest reference to the same path raises a `Duplicate hooks file detected` error that fails the **entire** plugin load (commands included). The manifest's `hooks` key is only for *additional* hook files at non-standard paths. (This bit us once — commit `f94242d` added exactly such a declaration and silently broke `--plugin-dir` loading until it was removed.)

## Conventions when editing command prompts

- **Confirmation discipline.** Most commands here treat git writes (commit, push, branch deletion) and file deletions as confirmation-required. Keep that pattern — don't relax it without an explicit reason. Read-only diagnostics (`git status`, `git log`, `git diff`) run freely.
- **Hard stops on counters.** `/step` and `/hitl-step` take an `N` argument and must hard-stop at N iterations even if work remains. Don't add "would you like to continue?" prompts at the boundary.
- **Idempotency.** `/agents-docs-update` is designed to be run repeatedly during a session (standalone and via `/smart-commit`); preserve the "if the source already reflects the diff, do nothing" behavior when editing it.
- **No placeholders in emitted commands.** Commands like `/new-branch` and `/smart-merge` are explicit that branch names, PR numbers, etc. must be substituted before any shell command runs — never emitted with `<branch>` literals.
- **Plan-file lockstep.** `/step` and `/hitl-step` share one resolution algorithm; their Step 1 sections must stay byte-identical apart from the filename. Verify with a diff after editing either — `sed -n '/^## Step 1/,/^### Status stamp/p'` on both, with `TODO.md`→`DO.md` and `/hitl-step`→`/step` substituted, must come out empty. The status-stamp format is a four-command contract (`/new-branch` writes, `/smart-merge` rewrites, both step commands read) — see "The plan convention". Never add logic that deletes a branch plan at merge; only the branch doc is ephemeral.
- **Scoped `allowed-tools`: additive yes, destructive no.** Every command allow-lists read-only diagnostics plus the **additive** writes it performs (`Write`, `Edit`, `git add`, `git commit`, `git checkout -b`, `git tag`). Operations that remove or cannot be undone — `gh pr merge`, `git push origin --delete`, `git branch -d`/`-D`, `git worktree remove`, `git rm` — are **deliberately omitted** so the harness prompt stands as a second gate behind each command's own CONFIRM FIRST prose. An omission of this kind is a decision, not drift; `/clean-gone` says so in its own Guidelines so nobody "fixes" it.

  Two traps to remember. **Prefix patterns are broader than they look**: `Bash(git branch:*)` also matches `git branch -D`, and `Bash(git push:*)` also matches `git push origin --delete` — which is why `/smart-commit` may allow-list `git push` (it never deletes) while `/smart-merge` may not (it does). Use `Bash(git branch --show-current:*)`, `Bash(git branch -vv:*)`, `Bash(git checkout main:*)` and similar instead of the bare verb. **Never hardcode MCP tool names**: they are `mcp__plugin_github_github__*` in one install and something else in another, so an entry matches nothing on a consumer's machine and fails silently, where a missing entry merely prompts.
