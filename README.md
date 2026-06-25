# workflow-claude

A collection of Claude Code commands, skills, hooks, and scripts bundled together as a plugin, customized for my personal agentic workflow preferences. Applicable to most projects.

## What's in here

- **`commands/`** — slash commands that show up as `/<filename>` in any project that installs the plugin.
- **`hooks/`** — a `PreToolUse` hook (`protect-agent-docs.py`) that prevents direct edits to `CLAUDE.md`, `AGENTS.md`, and `AGENTS.override.md` (root and per-component) once the `docs/agents/` sources exist, and a `SessionStart` hook (`remind-disable-commit-commands.py`) that nudges you to disable the overlapping `commit-commands` plugin (see below).
- **`scripts/`** — `build-agents-md.sh` (regenerates the `AGENTS.*` artifacts from `docs/agents/` sources) and `check-agents-md.sh` (verifies they're in sync). Bundled so consumers don't need their own copies.

## Installing & the `commit-commands` overlap

This plugin is loaded deliberately per-project via the CLI flag, not through a marketplace:

```
claude --plugin-dir <path-to>/workflow-claude
```

The official `commit-commands` plugin (`/commit`, `/commit-push-pr`) overlaps with `/smart-commit` and `/smart-merge` — but with the opposite philosophy. Running the `commit-commands` versions silently skips doc-sync, version/tag handling, and the branch-doc PR flow. When both are active at once you risk reaching for the wrong, lossier command.

The recommended policy is to keep `commit-commands` enabled globally (it's a fine minimal fallback in projects that don't load this plugin) but **disable it in every project that loads `workflow-claude`**. Do that with a git-committed project settings file, which overrides the global setting only here:

```jsonc
// <consumer-project>/.claude/settings.json
{
  "enabledPlugins": {
    "commit-commands@claude-plugins-official": false
  }
}
```

A ready-to-copy template lives at [`_meta/consumer-settings.template.json`](_meta/consumer-settings.template.json) — `cp` it to your project's `.claude/settings.json`. As a safety net, the bundled `SessionStart` hook prints this recommendation at launch whenever `workflow-claude` is loaded and `commit-commands` is still enabled, and goes silent once you've disabled it. A fuller analysis of the overlap is in [`_meta/plugin-conflict-report.md`](_meta/plugin-conflict-report.md).

### Interaction with `security-guidance`

If you also run the official `security-guidance` plugin, expect extra activity around `/smart-commit` and `/smart-merge`. That plugin registers `PostToolUse` hooks with `asyncRewake` on `git commit` and `git push` (plus a `Stop` hook), and Claude Code **stacks** hooks from all plugins rather than overriding them. So each commit and push these commands run will kick off a background security review that re-wakes the session mid-workflow with its findings.

This is expected, not a conflict — nothing breaks, and the two plugins' hooks compose cleanly (this plugin's `protect-agent-docs` runs at `PreToolUse`, `security-guidance` reviews at `PostToolUse`/`Stop`). If the rewakes get noisy during a long commit loop, scope or disable `security-guidance` for that session. See [`_meta/plugin-conflict-report.md`](_meta/plugin-conflict-report.md) §4.1 for detail.

## Two workflows, one branch lifecycle

The commands are designed to chain. There's a **branch workflow** (outer loop) that brackets every change, and an **agent-docs workflow** (inner concern) that keeps documentation honest as code moves.

### Branch lifecycle

```
/new-branch  →  /step or /hitl-step (loop)  →  /smart-commit (loop)  →  /smart-merge  →  /clean-gone
```

| Command         | Role |
|-----------------|------|
| `/new-branch`   | Creates `<type>/<slug>` and writes `docs/git/<branch>.md` capturing purpose, scope, and context. That doc is a working artifact for the branch's lifetime — `/smart-merge` later uses it as primary input for the PR. |
| `/step N`       | Executes the next `N` unchecked items from `DO.md`. Plain checkbox model (`[ ]` / `[x]`), inline `> **Q:** / > **A:**` log under each item so reasoning survives `/clear` or compaction. Hard-stops at `N`. |
| `/hitl-step N`  | Same loop against `TODO.md` but with a richer marker model (`[ ] [~] [x] [!] [-]`), explicit confirmation gates on writes, and parent/subgoal state propagation. Use this when each goal needs back-and-forth with you. |
| `/smart-commit` | Delegates to `/agents-docs-update` to sync docs with the staged diff, then commits and pushes. Conventional commit format. Confirmation-required. |
| `/smart-merge`  | Reads `docs/git/<branch>.md` to draft PR title and body, deletes the doc as part of the merge (so it stays in branch history but doesn't pollute `main`), then merges via `gh pr merge`. Walks merge-strategy choice with tradeoffs. |
| `/clean-gone`   | Deletes local branches whose upstream is `[gone]` (merged/deleted on the remote) and their worktrees. Confirmation-required, with a prominent warning when more than one branch is in scope. Closes the lifecycle so `commit-commands` isn't needed for cleanup. |

`/step` vs `/hitl-step`: pick based on how interactive each task needs to be. `/step` is fire-and-forget for routine work; `/hitl-step` is for goals where every decision should pass through you.

### Agent-docs workflow

The doc commands assume a specific layout in the consuming project:

- `CLAUDE.md` is an `@import` dispatcher only — two lines pulling in `docs/agents/core.md` and `docs/agents/claude.md`.
- `docs/agents/core.md` — tool-agnostic project context (shared with Codex, Cursor, etc.).
- `docs/agents/claude.md` — Claude-Code-specific context.
- `docs/agents/codex.md` — Codex-specific review priorities and gotchas.
- `AGENTS.md` and `AGENTS.override.md` — generated artifacts built from the `docs/agents/` sources.

In a monorepo, the same pattern repeats per component (`<path>/CLAUDE.md` backed by `docs/agents/<path>/{core,claude,codex}.md`). The directory tree under `docs/agents/` is the source of truth for which components exist.

| Command                  | Role |
|--------------------------|------|
| `/agents-docs-init`      | One-time migration: splits an existing `CLAUDE.md` into `docs/agents/{core,claude}.md` and replaces `CLAUDE.md` with the dispatcher. Handles root and every component (any nesting depth). |
| `/agents-docs-codex-init`| Generates `docs/agents/[<path>/]codex.md` sidecars that configure Codex as a cross-provider reviewer. One per target. |
| `/agents-docs-update`    | Standalone or invoked by `/smart-commit`. Reviews the staged diff, edits the relevant `docs/agents/*.md` sources to match, runs `/agents-docs-build` if `core.md` or `codex.md` changed, and stages everything. Idempotent. |
| `/agents-docs-build`     | Regenerates `AGENTS.md` and `AGENTS.override.md` (root and per-component) from the `docs/agents/` sources. Deterministic. |
| `/agents-docs-check`     | Verifies the committed `AGENTS.*` files match what `/agents-docs-build` would emit. Useful in pre-commit hooks or CI. |

Typical inner loop, once initialized: edit code → `/smart-commit` runs `/agents-docs-update` → docs stay in sync without you thinking about it.

## Conventions worth knowing

- **Confirm before writes.** Every command treats git writes (commit, push, branch deletion) and file deletions as confirmation-required. Read-only diagnostics (`git status`, `git log`, `git diff`) run freely.
- **Hard stops on counters.** `/step N` and `/hitl-step N` stop after `N` iterations even if work remains. They won't ask "continue?".
- **Never edit generated files directly.** The bundled `protect-agent-docs.py` hook blocks `Write`/`Edit`/`MultiEdit` against `CLAUDE.md`, `AGENTS.md`, and `AGENTS.override.md` once `docs/agents/` sources exist. Edit the sources and let `/agents-docs-build` regenerate.
- **`docs/git/<branch>.md` is per-branch scratch.** Created by `/new-branch`, consumed and deleted by `/smart-merge`. It stays in the branch's history (recoverable via SHA) but never lands on `main`.
