---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git fetch:*), Bash(git tag:*), Bash(git ls-files:*), Bash(git rev-parse:*), Bash(git branch --show-current:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(find:*), Bash(cat:*), Bash(ls:*), Read, Write, Edit, Glob, Grep, SlashCommand(/workflow-claude:agents-docs-update)
description: Update docs to match staged changes, commit with an appropriate message, sync component versions, tag any version bump, and push.
argument-hint: "[extra doc paths...]"
---

# Smart Commit

End-to-end commit workflow: sync documentation with the staged diff via `/workflow-claude:agents-docs-update`, handle any version bump, then commit, tag, and push.

This command delegates all documentation handling to that command via the SlashCommand tool. Do not duplicate or override its steps here — let it run to completion, then resume with the steps below.

## Step 1: Sync Documentation

Invoke `/workflow-claude:agents-docs-update` via the SlashCommand tool, passing this command's `$ARGUMENTS` through unchanged as its arguments. Wait for it to complete its Step 6 (Report) before proceeding.

The invoked command stops at staging — it stages any documentation updates it makes but does not commit. Continue with the steps below using the staged set it produced (the original staged changes plus any doc edits or regenerated artifacts).

## Step 2: Version-Bump Preflight

Determine whether this commit bumps the project version, and prepare the release artifacts if it does. This runs before the commit message is written, so anything staged here is described by it.

- If there is no `VERSION` file at the repo root, this repo does not use version tags — skip this step entirely; no tag will be created and no manifests are synced.
- If `VERSION` exists, read it and trim whitespace. Form the tag name by prefixing `v`, stripping any leading `v` from the contents first (so `0.2.0` and `v0.2.0` both yield `v0.2.0`).
- Run `git fetch --tags --quiet` so the local tag list reflects tags pushed from elsewhere; if it fails (e.g. offline), proceed with the local tag list.
- Run `git tag --list "<tag>"`:
  - **If the tag already exists**, `VERSION` was not bumped — this is an ordinary commit. Skip the rest of this step; no tag will be created and no manifests are synced. (This keeps the step idempotent: ordinary commits never tag or sync; only a `VERSION` bump does. A version bumped earlier but never tagged is also caught here and handled now.)
  - **If the tag does not exist**, this commit bumps the version. Carry the tag name forward to Step 4 and perform both checks below.

### Release notes (required on a bump)

A release needs release notes. If a `CHANGELOG.md` exists at the repo root, it must contain a section for this version (a heading naming it, e.g. `## [0.2.0]`). If `CHANGELOG.md` exists but has **no** section for this version, **stop** — do not stage anything further, do not commit, tag, or push. Report that `VERSION` was bumped without a matching `CHANGELOG.md` entry and ask the user either to add one or to explicitly authorize tagging without release notes. This makes "no version ships without release notes" structural.

### Component version manifests (synced automatically on a bump)

A multi-component repo usually carries a per-component version manifest, and these must not drift from the root `VERSION`. Bring them into line automatically — `VERSION` is the single source of truth:

- Use `git ls-files` to list tracked files, and from them collect every component version manifest: `package.json` (npm) and `pyproject.toml` (PEP 621 / uv / Poetry). Working from tracked files skips ignored paths such as `node_modules/` and vendored plugin clones.
- Read each manifest's own declared version:
  - `package.json` — the top-level `"version"` key.
  - `pyproject.toml` — the `version` key in the `[project]` table, or in `[tool.poetry]`. Skip a file that declares `dynamic = ["version"]` or carries no version key.
- For each manifest whose version differs from `VERSION`, edit **only** that version field to match `VERSION`. Never touch a dependency's version specifier or any other field.
- `git add` every manifest you changed so it joins this commit.
- If you find a versioned manifest in a format not listed above, do not guess — leave it unedited and flag it in the final report so the user can bump it by hand.

## Step 3: Generate Commit Message

Based on the **full set of staged changes** now in the index (the original staged changes, any doc updates or regenerated artifacts from Step 1, and any version manifests synced in Step 2), write a commit message.

Follow conventional commit format:
```
<type>(<scope>): <short summary>

<optional body with bullet points for notable changes>
```

- `type`: feat, fix, refactor, docs, chore, test, style, perf, ci, build
- `scope`: the primary area affected (e.g., auth, api, cli, config)
- Summary: imperative mood, lowercase, no period, ≤72 chars
- If documentation was updated as part of this commit, mention it briefly in the body (e.g., "- update README to reflect new CLI flags", "- sync docs/agents/core.md with new module layout")
- If component version manifests were synced in Step 2, mention it briefly in the body (e.g., "- sync ui/package.json and engine/pyproject.toml to VERSION 0.2.0")

## Step 4: Commit, Tag, and Push

### Commit

Run the commit: `git commit -m "<message>"`.

### Tag

If Step 2 determined this commit bumps the version, create an annotated tag on the new commit:

- **If `CHANGELOG.md` has a section for this version**, use that section's body as the tag message — the lines under the version heading up to the next version heading, with surrounding blank lines trimmed. Write that body to a file under `/tmp/` (outside the repo, so it cannot be staged or left as clutter) and run `git tag -a <tag> -F <notes-file>`, so `git show <tag>` and GitHub Releases carry the real release notes.
- **If no `CHANGELOG.md` exists at all**, fall back to a generic message: `git tag -a <tag> -m "Release <tag>"`.

Otherwise (an ordinary commit, or no `VERSION` file), create no tag.

### Push

Push to the remote tracking branch. Use `--follow-tags` so a newly created annotated tag travels with the push:

- `git push --follow-tags`
- If no upstream is set, identify the branch with `git branch --show-current` and use `git push -u origin <branch> --follow-tags`.

### Report

Report the final result: commit hash, branch, whether a version tag was created (and its name), which component version manifests were synced (with old → new versions), and a summary of what was committed and which docs (if any) were updated or regenerated. This extends (not replaces) the report from Step 1.
