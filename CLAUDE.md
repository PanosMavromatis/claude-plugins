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

- **`/new-branch`** creates `<type>/<slug>` and writes `docs/git/<branch>.md` (purpose, scope, context). That doc is a working artifact for the branch's lifetime.
- **`/step`** executes the next unchecked item from `DO.md`; **`/hitl-step`** does the same against `TODO.md` but with a richer status-marker model (`[ ] [~] [x] [!] [-]`) and inline `> **Q:** / > **A:**` logging under each goal so reasoning survives `/clear` or compaction.
- **`/smart-commit`** invokes `/agents-docs-update` via the SlashCommand tool, then handles any version bump (tag + component-manifest sync), commits, tags, and pushes. It deliberately delegates all doc-sync logic rather than duplicating it.
- **`/smart-merge`** reads `docs/git/<branch>.md` to draft the PR title/body, deletes that doc as part of the merge (so it stays in branch history but doesn't pollute `main`), then merges via `gh pr merge`.
- **`/clean-gone`** deletes local branches whose upstream is `[gone]` (deleted on the remote, e.g. after a merge) and their worktrees. It is confirmation-required and warns prominently when more than one branch is in scope. It is the `workflow-claude` equivalent of `commit-commands`' `/clean_gone`, ported so the branch lifecycle is self-contained — but adapted to this plugin's confirm-before-delete and no-placeholder conventions (the original deletes without confirmation).

`/agents-docs-update` is the shared module for keeping documentation in sync with staged changes — it's both standalone and imported by `/smart-commit`. When editing one, consider whether the change belongs in the shared module instead.

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

## Coexistence with `commit-commands`

This plugin is loaded deliberately per-project via `claude --plugin-dir`, and overlaps with the official `commit-commands` plugin (`/commit`, `/commit-push-pr`, `/clean_gone`) — `/smart-commit`, `/smart-merge`, and `/clean-gone` supersede those with richer, confirm-first behaviour. The two should not both be active: running the `commit-commands` versions silently skips doc-sync, version/tag handling, and the branch-doc PR flow.

To make that self-enforcing, the plugin ships a second hook, `hooks/remind-disable-commit-commands.py` (registered in `hooks/hooks.json` as a `SessionStart` hook). Because it only runs when `workflow-claude` is loaded, its mere firing signals a `--plugin-dir` launch; it then checks the effective `enabledPlugins` state (merging user/project/local `settings.json`) and, if `commit-commands` is still enabled, surfaces a recommendation to disable it for that project. It is silent once disabled. The recommendation reaches the user via the hook JSON's top-level `systemMessage` field (printed to the terminal at launch); `additionalContext` is *model*-facing and `stderr`/`exit 2` was not surfaced in testing, so neither is sufficient on its own — see `_meta/plugin-conflict-report.md` §8. The full rationale, the consumer `.claude/settings.json` override template, and the `security-guidance` interaction note live in that report and the README. When editing this hook or `hooks.json`, keep that report in sync.

**Manifest gotcha — do not "declare" the hooks path.** `.claude-plugin/plugin.json` must **not** carry a `hooks` key pointing at `hooks/hooks.json`. Claude Code auto-loads that standard file by convention; a manifest reference to the same path raises a `Duplicate hooks file detected` error that fails the **entire** plugin load (commands included). The manifest's `hooks` key is only for *additional* hook files at non-standard paths. (This bit us once — commit `f94242d` added exactly such a declaration and silently broke `--plugin-dir` loading until it was removed.)

## Conventions when editing command prompts

- **Confirmation discipline.** Most commands here treat git writes (commit, push, branch deletion) and file deletions as confirmation-required. Keep that pattern — don't relax it without an explicit reason. Read-only diagnostics (`git status`, `git log`, `git diff`) run freely.
- **Hard stops on counters.** `/step` and `/hitl-step` take an `N` argument and must hard-stop at N iterations even if work remains. Don't add "would you like to continue?" prompts at the boundary.
- **Idempotency.** `/agents-docs-update` is designed to be run repeatedly during a session (standalone and via `/smart-commit`); preserve the "if the source already reflects the diff, do nothing" behavior when editing it.
- **No placeholders in emitted commands.** Commands like `/new-branch` and `/smart-merge` are explicit that branch names, PR numbers, etc. must be substituted before any shell command runs — never emitted with `<branch>` literals.
- **Scoped `allowed-tools`.** Every command allow-lists read-only git/diagnostics plus only the writes it actually performs; no command uses a blanket `Bash(git:*)`. Preserve this — broad patterns silently authorize destructive ops (`git reset --hard`, `git branch -D`, `git clean`) a command never needs, and for listing flags note the trap that `Bash(git branch:*)` also matches `git branch -D` (use `Bash(git branch --show-current:*)` / `Bash(git branch -vv:*)` instead).
