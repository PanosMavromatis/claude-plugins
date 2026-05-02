---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git branch:*), Bash(find:*), Bash(cat:*), Bash(ls:*), Bash(dev/build-agents-md.sh:*), Read, Write, Glob, Grep
description: Update project docs and regenerate agent artifacts to match staged changes.
argument-hint: "[extra doc paths...]"
---

# Agent Docs Update

Review currently-staged changes and update documentation to match. Intended both as a standalone mid-stream checkpoint and as a shared module invoked by `/smart-commit`.

This command does not commit or push — its `allowed-tools` list does not include those git subcommands. It stops at staging.

## Step 1: Preflight Checks

1. Run `git status` to confirm there are staged changes. If nothing is staged, inform the user and stop — there is no diff to evaluate against.
2. Run `git diff --cached` to capture the full staged diff. This is the **only** diff you will work with.
3. Identify the current branch with `git branch --show-current` and retain it for downstream use.

## Step 2: Identify Documentation Files

Build a list of documentation files to consider for updates:

**Defaults (always check if they exist in the repo):**
- `README.md` — human-facing documentation
- `docs/agents/core.md` — tool-agnostic agent context (shared by Claude Code, Cursor, Codex)
- `docs/agents/claude.md` — Claude-Code-specific context
- `docs/agents/codex.md` — Codex-specific context (review priorities, gotchas)
- All `.md` files under `docs/git/` (find recursively)
- All `.md` files under `docs/ops/` (find recursively)

**Do not consider** `CLAUDE.md`, `AGENTS.md`, or `AGENTS.override.md`. `CLAUDE.md` is an `@import` dispatcher; the other two are generated artifacts built from the `docs/agents/` sources by `dev/build-agents-md.sh`. A PreToolUse hook will block direct edits to all three.

**Extra paths from arguments:** `$ARGUMENTS`
- For each extra path provided:
  - If it is a file, add it to the list.
  - If it is a directory, find all `.md` files within it recursively (`find <path> -name '*.md'`) and add them.
- If no extra arguments are provided, only use the defaults.
- Skip any file that does not exist.

## Step 3: Evaluate and Update Documentation

For **each** documentation file in the list:

1. Read its current contents.
2. Analyze whether the staged diff introduces changes that make the documentation **factually inaccurate, incomplete, or misleading**. Examples of changes that warrant a doc update:
   - New or removed CLI commands, flags, or API endpoints
   - Changed installation/setup steps
   - New or removed dependencies
   - Renamed or restructured modules/files referenced in the doc
   - Changed configuration options or environment variables
   - New features or removed functionality described in the doc
3. **If no update is needed, skip the file entirely.** Do not make cosmetic, stylistic, or speculative edits.
4. If an update is needed, make the minimal targeted edit to keep the doc accurate. Preserve the existing style, tone, and structure.

**Scope guidance for the agent docs**, to classify where an edit belongs:
- `core.md` — shared project facts: architecture, build/test/lint commands, conventions, domain invariants. Most code changes that affect agent docs land here.
- `claude.md` — Claude-Code-specific: skill references, slash commands, workflow patterns that name Claude Code features.
- `codex.md` — Codex-specific: review priorities, high-signal targets, gotchas discovered during Codex review sessions.

When an edit could plausibly belong in more than one, prefer `core.md` — broader reach, and the others can reference it.

**Idempotency note:** If a source file is already staged with edits that match the diff (e.g., because this command was run earlier), treat it as up-to-date and make no further changes.

## Step 4: Rebuild Generated Artifacts

If `docs/agents/core.md` or `docs/agents/codex.md` was modified in Step 3, run `dev/build-agents-md.sh` to regenerate `AGENTS.md` and `AGENTS.override.md`. Skip this step if neither was modified.

If only `docs/agents/claude.md` was modified, no build is needed — `CLAUDE.md` picks up changes via `@import` at the next session.

## Step 5: Stage Documentation Changes

If any documentation files were modified in Step 3 or regenerated in Step 4:
- Run `git add <file>` for each modified source and each regenerated artifact.
- Do **not** stage anything else.

## Step 6: Report

Print a concise summary:
- Source files updated in Step 3 (or "none")
- Whether artifacts were regenerated in Step 4
- Current staged set: run `git status --short` and show the output

Do not commit. The caller — either the user directly or `/smart-commit` — decides what to do next.
