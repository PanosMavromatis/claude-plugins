# workflow-claude

A collection of Claude Code commands, skills, hooks, and scripts bundled together as a plugin, customized for my personal agentic workflow preferences. Applicable to most projects.

## What's in here

- **`commands/`** — slash commands that show up as `/<filename>` in any project that installs the plugin.
- **`hooks/`** — a `PreToolUse` hook (`protect-agent-docs.py`) that prevents direct edits to `CLAUDE.md`, `AGENTS.md`, and `AGENTS.override.md` (root and per-component) once the `docs/agents/` sources exist.
- **`scripts/`** — `build-agents-md.sh` (regenerates the `AGENTS.*` artifacts from `docs/agents/` sources) and `check-agents-md.sh` (verifies they're in sync). Bundled so consumers don't need their own copies.

## Two workflows, one branch lifecycle

The commands are designed to chain. There's a **branch workflow** (outer loop) that brackets every change, and an **agent-docs workflow** (inner concern) that keeps documentation honest as code moves.

### Branch lifecycle

```
/new-branch  →  /step or /hitl-step (loop)  →  /smart-commit (loop)  →  /smart-merge
```

| Command         | Role |
|-----------------|------|
| `/new-branch`   | Creates `<type>/<slug>` and writes `docs/git/<branch>.md` capturing purpose, scope, and context. That doc is a working artifact for the branch's lifetime — `/smart-merge` later uses it as primary input for the PR. |
| `/step N`       | Executes the next `N` unchecked items from `DO.md`. Plain checkbox model (`[ ]` / `[x]`), inline `> **Q:** / > **A:**` log under each item so reasoning survives `/clear` or compaction. Hard-stops at `N`. |
| `/hitl-step N`  | Same loop against `TODO.md` but with a richer marker model (`[ ] [~] [x] [!] [-]`), explicit confirmation gates on writes, and parent/subgoal state propagation. Use this when each goal needs back-and-forth with you. |
| `/smart-commit` | Delegates to `/agents-docs-update` to sync docs with the staged diff, then commits and pushes. Conventional commit format. Confirmation-required. |
| `/smart-merge`  | Reads `docs/git/<branch>.md` to draft PR title and body, deletes the doc as part of the merge (so it stays in branch history but doesn't pollute `main`), then merges via `gh pr merge`. Walks merge-strategy choice with tradeoffs. |

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
