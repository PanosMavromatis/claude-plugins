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
```

- **`/new-branch`** creates `<type>/<slug>`, writes `docs/git/<branch>.md` (purpose, scope, context) and a status-stamped branch plan under `docs/plan/<type>-<slug>/`. The doc is a working artifact for the branch's lifetime; the plan outlives it.
- **`/step`** executes the next unchecked item from a `DO.md`; **`/hitl-step`** does the same against a `TODO.md` but with a richer status-marker model (`[ ] [~] [x] [!] [-]`) and inline `> **Q:** / > **A:**` logging under each goal so reasoning survives `/clear` or compaction. Both resolve the plan file through the five-rung order described under "The plan convention" below. **Their Step 1 sections are byte-identical apart from the filename — keep them that way**; drift between them is a bug you only hit on whichever command you use less.
- **`/smart-commit`** invokes `/agents-docs-update` via the SlashCommand tool, then handles any version bump (tag + component-manifest sync), commits, tags, and pushes. It deliberately delegates all doc-sync logic rather than duplicating it.
- **`/smart-merge`** reads `docs/git/<branch>.md` and the branch plan to draft the PR title/body, deletes the doc as part of the merge (so it stays in branch history but doesn't pollute `main`), stamps the plan `merged` and closes the master-plan item, gates on CI, then merges — preferring the GitHub MCP server and falling back to `gh`. It deletes the doc but **never** the plan. See "GitHub access" below.
- **`/clean-gone`** deletes local branches whose upstream is `[gone]` (deleted on the remote, e.g. after a merge) and their worktrees. It is confirmation-required and warns prominently when more than one branch is in scope. It is the `workflow-claude` equivalent of `commit-commands`' `/clean_gone`, ported so the branch lifecycle is self-contained — but adapted to this plugin's confirm-before-delete and no-placeholder conventions (the original deletes without confirmation).

`/agents-docs-update` is the shared module for keeping documentation in sync with staged changes — it's both standalone and imported by `/smart-commit`. When editing one, consider whether the change belongs in the shared module instead.

## The plan convention (consuming-project convention)

Plans are two-tier, and unlike the branch doc, **both tiers are durable and land on `main`**:

- **Master plan** — `docs/plan/DO.md` or `docs/plan/TODO.md`. Its items are subgoals, each spawning a branch. Long-lived.
- **Branch plan** — `docs/plan/<flattened-branch>/{DO,TODO}.md`, where the directory is the branch name with `/` flattened to `-` (`feat/user-auth` → `docs/plan/feat-user-auth/`). Flattening avoids a `docs/plan/feat/` pseudo-namespace and stops `feat/export` and `fix/export` colliding.

`/step` and `/hitl-step` resolve in strict priority order, stopping at the first rung that yields a file:

1. explicit path argument — if it doesn't resolve, **stop**, never fall through (a typo would silently run a different plan);
2. `docs/plan/<flattened-current-branch>/<file>` — the answer on a feature branch;
3. `docs/plan/<file>` — the answer on `main`;
4. glob `docs/plan/**/<file>`, filter out merged plans, ask if several remain;
5. legacy root-level `DO.md`/`TODO.md`, with a migration nudge.

Rungs 2 and 3 mean neither normal working position ever prompts, which is what keeps accumulated merged plans from turning rung 4 into a permanent tax.

**The status stamp is a contract between three commands.** `/new-branch` writes `**Status**: active`; `/smart-merge` rewrites it to `**Status**: merged — PR #<n> — <date>`; `/step` and `/hitl-step` read it to filter rung 4. A plan counts as merged **only** if a `**Status**:` line's value begins with `merged` — everything else, including no stamp at all, counts as active. That asymmetry is deliberate: plans merged outside `/smart-merge` never get stamped, and a stale option in a list is cheaper than a hidden live plan. When changing the format, change all four commands together.

**Merge-time writes go on the branch, not `main`.** `/smart-merge` stamps the plan and closes the master-plan item in one commit between PR creation and merge — the only window where the PR number exists and the branch still does. (Stated mechanism-neutrally on purpose: either path may create the PR — see "GitHub access".) Recording it after the merge would mean committing directly to `main`, which branch protection commonly forbids.

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
- **Plan-file lockstep.** `/step` and `/hitl-step` share one resolution algorithm; their Step 1 sections must stay byte-identical apart from the filename. The status-stamp format is a four-command contract (`/new-branch` writes, `/smart-merge` rewrites, both step commands read) — see "The plan convention". Never add logic that deletes a branch plan at merge; only the branch doc is ephemeral.
- **Scoped `allowed-tools`: additive yes, destructive no.** Every command allow-lists read-only diagnostics plus the **additive** writes it performs (`Write`, `Edit`, `git add`, `git commit`, `git checkout -b`, `git tag`). Operations that remove or cannot be undone — `gh pr merge`, `git push origin --delete`, `git branch -d`/`-D`, `git worktree remove`, `git rm` — are **deliberately omitted** so the harness prompt stands as a second gate behind each command's own CONFIRM FIRST prose. An omission of this kind is a decision, not drift; `/clean-gone` says so in its own Guidelines so nobody "fixes" it.

  Two traps to remember. **Prefix patterns are broader than they look**: `Bash(git branch:*)` also matches `git branch -D`, and `Bash(git push:*)` also matches `git push origin --delete` — which is why `/smart-commit` may allow-list `git push` (it never deletes) while `/smart-merge` may not (it does). Use `Bash(git branch --show-current:*)`, `Bash(git branch -vv:*)`, `Bash(git checkout main:*)` and similar instead of the bare verb. **Never hardcode MCP tool names**: they are `mcp__plugin_github_github__*` in one install and something else in another, so an entry matches nothing on a consumer's machine and fails silently, where a missing entry merely prompts.
