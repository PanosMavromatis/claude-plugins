---
allowed-tools: Bash(git status:*), Bash(ls:*), Bash(find:*), Read, Write, Edit, Glob, Grep
description: Migrate CLAUDE.md (root + monorepo components) into docs/agents/[<path>/]{core,claude}.md and replace each with an @import dispatcher
---

# /agents-docs-init

One-time migration: for each location with a `CLAUDE.md` (the repo root, plus any per-component `<path>/CLAUDE.md` in a monorepo layout), move its content into the split sources used by `/agents-docs-build`, then replace the `CLAUDE.md` with a minimal `@import` dispatcher.

This is an interactive, destructive operation. Stop at each confirmation point and wait for the user before proceeding.

## Targets

The command processes one **target** per location to be migrated. Each target is identified by its `<path>` (the directory containing the `CLAUDE.md` being migrated):

- **Root target** — `<path>` is empty; affects `CLAUDE.md` and `docs/agents/{core,claude}.md`.
- **Component targets** — `<path>` is e.g. `ui/` or `ui/components/`; affects `<path>CLAUDE.md` and `docs/agents/<path>{core,claude}.md`. Component nesting is unrestricted — recursion follows whatever directory tree exists.

**The directory tree under `docs/agents/` is the source of truth for which components exist.** To declare a new component, the user creates `docs/agents/<path>/` (typically empty) before invoking this command. The init then detects the new directory and offers to fill in the rest. This keeps routine commands cheap in the non-monorepo case and avoids any second source of truth.

## Preflight

1. **Check git status.** Run `git status --porcelain`. If output is non-empty, stop and tell the user to commit or stash first. The recovery path for this command is `git restore` against any file it touches, which only works from a clean baseline.
2. **Discover targets.**
   - **Root.** The root target exists if `CLAUDE.md` is present at the repo root.
   - **Components from `docs/agents/`.** Run `find docs/agents -mindepth 1 -type d` (or equivalent). For each subdirectory, the component's `<path>` is its location relative to `docs/agents/` (with a trailing slash). Add a target for each.
   - **Implicit components from existing `<path>/CLAUDE.md`.** Search the repo for `<path>/CLAUDE.md` files that contain substantive prose but whose corresponding `docs/agents/<path>/` directory does not yet exist (use `find . -name CLAUDE.md -not -path './node_modules/*' -not -path './.git/*'` or equivalent; respect `.gitignore` where reasonable). Flag each as an implicit component — the user has started writing component-level context but hasn't yet declared the docs scaffolding. Plan to create `docs/agents/<path>/` for each.
3. **Classify each target's state.**
   - `migrate` — the `<path>/CLAUDE.md` exists and contains substantive prose (more than just `@import` directives plus an HTML comment).
   - `scaffold` — the `<path>/CLAUDE.md` is missing, empty, or already a dispatcher, *and* `docs/agents/<path>/{core,claude}.md` are missing or incomplete. The migration creates stub source files and writes the dispatcher.
   - `skip` — the target is already fully migrated (dispatcher in place, both source files exist with content).
4. **Check at least one target needs work.** If every detected target is `skip`, report that the migration appears to already be done across all locations and stop.
5. **Ensure target subdirectories exist.** For each non-`skip` target, create `docs/agents/<path>/` if missing (this also covers the implicit-component case).

## Classification

For each `migrate` target, read its `<path>/CLAUDE.md` in full. Partition each section (typically a heading and its contents) into one of two destinations:

- **`docs/agents/<path>core.md`** — tool-agnostic content. Project or component overview, architecture, module responsibilities, build/test/lint commands, coding conventions, domain invariants, general gotchas. Anything equally relevant to Codex, Cursor, Jules, or any other agent reading this codebase.
- **`docs/agents/<path>claude.md`** — Claude-Code-specific content. Skill references (`.claude/skills/`), slash command references, subagent or `context: fork` patterns, `/compact` instructions, MEMORY.md references, `@import` conventions, or anything that names Claude Code features by name.

If a section mixes both concerns, split it at the paragraph or bullet level. When uncertain, default to `core.md` — shared content has broader reach and the cost of over-sharing is low.

For each `scaffold` target, no classification is needed — the migration creates two stub files containing only a heading (e.g. `# <component> — core context` / `# <component> — Claude Code context`) for the user to fill in later.

Do **not** modify any `docs/agents/[<path>/]codex.md`. Codex sidecars are handled by `/agents-docs-codex-init` and are not a target of this migration.

## Checkpoint 1 — show the plan

Before writing anything, present the user with:

- A table listing every detected target — its `<path>`, its state (`migrate` / `scaffold` / `skip`), and (for `migrate` targets) the proposed section-by-section destination.
- Any sections, within any target, that you are uncertain about — explicitly flagged.
- Any **implicit components** (substantive `<path>/CLAUDE.md` files lacking a matching `docs/agents/<path>/`) and your plan to create the subdirectory as part of migration.
- For `scaffold` targets, the stub content you intend to write.

Wait for confirmation. The user may approve a subset — accept partial plans and only proceed with approved targets. If the user wants reclassification or wants to drop a target, adjust and re-show.

## Writing the splits

For each approved `migrate` target:

If `docs/agents/<path>core.md` or `docs/agents/<path>claude.md` already exists, **append-merge** rather than overwrite:

- Read the existing file first.
- For each incoming section, check whether a semantically equivalent section already exists (same heading, or same topic under a different heading).
  - If yes: merge new bullets or paragraphs under the existing heading. Skip items already present verbatim or near-verbatim.
  - If no: add the section at a position consistent with the file's existing structure.
- Preserve existing content verbatim. The goal is to add, not to refactor what's already there.

If a target source file does not exist, create it with the classified content.

For each approved `scaffold` target, write the two stub files. Do not overwrite a `core.md` or `claude.md` that already has content — for those, leave the existing content in place and only ensure the file exists.

## Checkpoint 2 — show the resulting files

For each processed target, show the user the full contents of the new or updated `core.md` and `claude.md` (or diffs if they pre-existed; or the stub for `scaffold` targets). Wait for confirmation that everything looks right.

## Replacing each CLAUDE.md

Only after confirmation, for each approved target replace `<path>CLAUDE.md` with the dispatcher content below, substituting `<path>` consistently in the `@docs/agents/...` paths. For the root target `<path>` is empty so the imports become `@docs/agents/core.md` and `@docs/agents/claude.md`; for a component like `ui/`, the imports become `@docs/agents/ui/core.md` and `@docs/agents/ui/claude.md`.

> **Use Bash heredoc, not Write/Edit, for this step.** By this point in the migration the sentinel `docs/agents/<path>core.md` exists (you wrote it in the previous step), so the `protect-agent-docs.py` hook will block any `Write` or `Edit` against `<path>CLAUDE.md`. The hook only matches `Write|Edit|MultiEdit`; Bash shell redirects pass through. Use a `cat <<'EOF' > <path>CLAUDE.md` heredoc (note the single-quoted `'EOF'` so `@import` lines are not interpreted by the shell). The same applies even for fresh dispatcher creation in `scaffold` targets, since the same hook is in force.
>
> **`Bash(cat:*)` is deliberately absent from this command's `allowed-tools`** — do not "fix" it by adding it. That heredoc replaces the user's existing `CLAUDE.md`, the one genuinely destructive operation here, so it should keep prompting. The `Write`/`Edit` entries that *are* allow-listed cover the `docs/agents/` sources only; the hook independently blocks them against the protected filenames regardless of the allow-list.

```markdown
<!-- Claude Code context dispatcher. Hand-authored (not a generated artifact).

     DO NOT EDIT this file directly. It is an @import dispatcher.
     - Shared project knowledge  → docs/agents/<path>core.md
     - Claude-Code-specific      → docs/agents/<path>claude.md

     The same sources feed AGENTS.md and AGENTS.override.md via
     /agents-docs-build. A PreToolUse hook shipped by the workflow-claude
     plugin blocks direct Write/Edit/MultiEdit to this file. -->

@docs/agents/<path>core.md
@docs/agents/<path>claude.md
```

## Checkpoint 3 — final report

Print a summary covering every processed target:

- For each target: the `<path>`, the action taken (`migrated` / `scaffolded` / `skipped`), and line counts of the new or updated `core.md` and `claude.md`.
- Any sections that were ambiguous and the classification decision made for each.
- A reminder to run `/agents-docs-build` and inspect every generated `AGENTS.md` and `AGENTS.override.md` (root and per-component) before committing.
- A reminder that `git restore` against the touched files will undo the migration if anything looks wrong (e.g. `git restore CLAUDE.md docs/agents/` for the root, plus `git restore <path>/CLAUDE.md` for each component processed).

> **Build & protection are plugin-provided.** Component-level generation is handled by the plugin's `/agents-docs-build` (and verified by `/agents-docs-check`); component-level protection of `<path>/CLAUDE.md`, `<path>/AGENTS.md`, and `<path>/AGENTS.override.md` is enforced by the bundled `protect-agent-docs.py` PreToolUse hook. No consumer-side scripting is required to make the component flow work — the hook activates per-component the moment `docs/agents/<path>/core.md` (or `codex.md`, for the override) exists.

## Do not

- Run `/agents-docs-build` automatically — the user should inspect the splits first.
- Modify any `docs/agents/[<path>/]codex.md`.
- Rewrite or "clean up" existing content in target files. Add only.
- Overwrite a non-empty `core.md` or `claude.md` during a `scaffold` action.
- Commit anything. The user reviews and commits manually.
