# workflow-claude

A collection of Claude Code commands, skills, hooks, and scripts bundled together as a plugin, customized for my personal agentic workflow preferences. Applicable to most projects.

## What's in here

- **`commands/`** — slash commands that show up as `/<filename>` in any project that installs the plugin.
- **`hooks/`** — a `PreToolUse` hook (`protect-agent-docs.py`) that prevents direct edits to `CLAUDE.md`, `AGENTS.md`, and `AGENTS.override.md` (root and per-component) once the `docs/agents/` sources exist, and a `SessionStart` hook (`remind-disable-commit-commands.py`) that nudges you to disable the overlapping `commit-commands` plugin (see below).
- **`scripts/`** — deterministic helpers the commands call, bundled so consumers don't need their own copies. Two serve the agent-docs workflow: `build-agents-md.sh` (regenerates the `AGENTS.*` artifacts from `docs/agents/` sources) and `check-agents-md.sh` (verifies they're in sync). Three serve the plan workflow and are all **read-only** — they propose, and the command that calls them performs every write: `open-revision.sh`, `file-plans.sh` and `close-revision.sh`. Because they never write, they are safe to run directly, in a hook, or in CI.

## Installing & the `commit-commands` overlap

This plugin is published in the **`mavromatis-ai-labs`** marketplace — the
[`PanosMavromatis/claude-plugins`](https://github.com/PanosMavromatis/claude-plugins)
monorepo. A consuming project registers the marketplace and enables the plugin in one
committed file:

```jsonc
// <consumer-project>/.claude/settings.json
{
  "extraKnownMarketplaces": {
    "mavromatis-ai-labs": {
      "source": { "source": "github", "repo": "PanosMavromatis/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "workflow-claude@mavromatis-ai-labs": true
  }
}
```

`claude plugin marketplace add PanosMavromatis/claude-plugins` followed by `claude plugin
install workflow-claude@mavromatis-ai-labs --scope project` writes the same keys
imperatively. Prefer the declaration: it is what a fresh clone reproduces from, and what a
reviewer sees in a diff. The same file is where you disable `commit-commands`, below.

**`--plugin-dir` is the development path, not the install path.** `claude --plugin-dir
<path-to>/workflow-claude` loads a directory for a single session with no marketplace
involved — what to reach for when editing this plugin rather than using it.

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

### Loading it by symlink, and what that costs

A third way to load this plugin, alongside a marketplace install and `--plugin-dir`, is to
place it in a consuming project's `.claude/skills/`. Doing that by **copying** the clone
works and then rots: the copy is byte-identical on the day it is made and goes stale at the
first edit, and the failure is silent — a stale copy still loads and still works, just from
the old text. A symlink makes that drift unrepresentable:

```bash
ln -s ../../path/to/workflow-claude <consumer>/.claude/skills/workflow-claude
```

Three costs come with it, and the third is the one that surprises people:

- **The clone becomes load-bearing.** Moving or deleting it breaks the consumer's plugin
  with a dangling symlink rather than an error that names the cause.
- **A directory-shaped ignore rule stops matching.** A pattern with a trailing slash —
  `/.claude/skills/workflow-claude/` in a `.gitignore` or `.git/info/exclude` — matches
  directories only, so replacing the directory with a symlink silently un-ignores it and the
  path starts appearing as untracked. Drop the trailing slash.
- **The consumer now loads whatever branch the clone has checked out.** A separate copy was
  pinned to `main` independently; a symlink is not. So `git checkout` in the clone puts that
  branch into every consuming session's load path immediately, including work that has not
  been reviewed. Either keep the clone on `main` except while a branch is actively being
  edited, or accept that editing this plugin edits the tooling running the edit.

That last one is not hypothetical, and it cuts both ways: it is also what makes a fix take
effect with no sync step at all, which is the reason to prefer the symlink over a copy.

### Interaction with `security-guidance`

If you also run the official `security-guidance` plugin, expect extra activity around `/smart-commit` and `/smart-merge`. That plugin registers `PostToolUse` hooks with `asyncRewake` on `git commit` and `git push` (plus a `Stop` hook), and Claude Code **stacks** hooks from all plugins rather than overriding them. So each commit and push these commands run will kick off a background security review that re-wakes the session mid-workflow with its findings.

This is expected, not a conflict — nothing breaks, and the two plugins' hooks compose cleanly (this plugin's `protect-agent-docs` runs at `PreToolUse`, `security-guidance` reviews at `PostToolUse`/`Stop`). If the rewakes get noisy during a long commit loop, scope or disable `security-guidance` for that session. See [`_meta/plugin-conflict-report.md`](_meta/plugin-conflict-report.md) §4.1 for detail.

## Companion plugins

`commit-commands` overlaps with this plugin and should be disabled beside it.
[`dp-compile`](https://github.com/PanosMavromatis/claude-plugins/tree/main/plugins/dp-compile) is the opposite case: it
**assumes** this plugin is loaded and hands work to it.

`dp-compile` guides a dynamic-programming algorithm through a staged translation — a
formalization, then pure Python, Cython, and two Numba backends — enforcing that every
backend agrees with the reference. It owns that lifecycle and nothing else. Branches go to
`/new-branch`, plans to `/step` or `/hitl-step`, commits to `/smart-commit`, merges to
`/smart-merge`, and documentation to `/agents-docs-update`; it runs no `git` command itself
and never edits a plan file.

**The dependency is one-directional, and nothing here maintains it.** `dp-compile` detects
this plugin by reading its own tool list for anything namespaced `workflow-claude:` — the
same judgement `/smart-merge` makes about MCP availability, and for the same reason: there
is no shell command that reports which plugins are loaded. There is **no detection contract,
no marker file and no hook handshake** between the two, which was a deliberate choice on
`dp-compile`'s side: a contract would have coupled both plugins forever for a check one of
them can make alone, and would have assumed hooks fire, which depends on the load path.

The practical consequence is the one to remember when editing this repository: unlike the
`commit-commands` hook — where changing `hooks.json` means updating the conflict report in
the same commit — **there is nothing on this side to keep in sync**. `dp-compile` names this
plugin's commands in its own prose; renaming one of them would break it, and no test here
would notice.

Two notes on how the two behave together:

- **Absence is not fatal.** A `dp-compile` command that delegates nothing prints one line
  and produces its full output; one that does delegate performs every step that needs
  nothing from this plugin and stops at the step that does. Its absence message names all
  three load paths, including a plugin tree placed in a project's `.claude/skills/` — which
  is neither a marketplace install nor `--plugin-dir`. That route stays supported and worth
  naming: pfsmgraph loaded *this* plugin that way until 2026-09-09, when it moved to a
  marketplace install.
- **The hooks cannot collide.** `dp-compile` ships a `PreToolUse` hook on `Bash` that gates
  a commit on the consumer's test suite when a kernel file is staged; this plugin's
  `protect-agent-docs.py` matches `Write|Edit|MultiEdit`. No tool call matches both. Because
  hooks stack, that gate fires inside the `git commit` `/smart-commit` runs — so delegating
  the commit does not bypass it. See
  [`_meta/plugin-conflict-report.md`](_meta/plugin-conflict-report.md) §4.4.

## Two workflows, one branch lifecycle

The commands are designed to chain. There's a **branch workflow** (outer loop) that brackets every change, and an **agent-docs workflow** (inner concern) that keeps documentation honest as code moves.

### Revision and branch lifecycle

A **revision** is a milestone: `/open-revision <label>` starts one, its subgoals each spawn a branch, and `/close-revision <label>` archives it when you say it is finished. Revisions are identified by a **label** such as `04-revision-lifecycle`, not by a number — the label names the master-plan heading and the directory alike, so `docs/plan/` and the master plan each read without cross-referencing the other. The leading ordinal is a sorting convention inside the label; nothing counts revisions or requires them to be consecutive.

```
/open-revision <label>
     │
     └─▶ /new-branch  →  /step or /hitl-step (loop)  →  /smart-commit (loop)  →  /smart-merge  →  /clean-gone
                                                                                             │
                                                              (periodically) /file-plans ────┘
                                                (when a revision ends) /close-revision <label>
```

`/new-branch` opens a branch with a doc and a plan; the step commands work the plan; `/smart-commit` commits as you go; `/smart-merge` drafts the PR, records the merge in both plans, gates on CI and merges; `/clean-gone` removes branches the remote has dropped. Then, every so often, `/file-plans` **files** the merged plans.

#### The filing sweep

Branch plans are never deleted — they land on `main` as the durable record — so `docs/plan/` gains one flat directory per merged branch. Filing moves each into a directory for the revision it belonged to:

```
docs/plan/
  DO.md                          ← master plan
  02-mcp-github-access/          ← that revision's branch plans, and its archive once closed
  03-subgoal-plan-management/
```

Run **`/file-plans`**. Nothing is being classified: `/new-branch` writes each plan's `> **Branch:**` backlink beneath a specific `## Subgoals — revision <label>` heading, so **a plan's revision is already recorded at creation time**, and the sweep reads it back —

```bash
awk '/^## Subgoals/{h=$0} /^[[:space:]]*> \*\*Branch:\*\*/{print $NF, h}' docs/plan/DO.md
```

— which is what the bundled `scripts/file-plans.sh` does. The script is read-only and prints proposed `git mv` commands; `/file-plans` presents them, confirms, executes and commits on a branch. Two cases it cannot derive are reported and left flat, never guessed: a plan with no backlink, and a backlink under a heading carrying no revision label. Nothing else needs updating — every command finds a plan by its directory *name*, not its path, so the layout beneath `docs/plan/` is yours to arrange. Grouping by revision is one option and nothing depends on it; a monorepo might group by component instead, reading the component list from the `docs/agents/` tree rather than inventing a second one.

A plan filed into the *wrong* revision is worse than one never filed, because the mistake becomes invisible once it is filed — hence report-don't-guess.

| Command         | Role |
|-----------------|------|
| `/new-branch`   | Creates `<type>/<slug>`, writes `docs/git/<branch>.md` (purpose, scope, context) and a status-stamped branch plan at `docs/plan/<type>-<slug>/` — always flat; the filing sweep moves it into a revision directory later. The doc is consumed and deleted at merge; the plan survives on `main`. |
| `/step N [path]` | Executes the next `N` unchecked items from a plan file. Plain checkbox model (`[ ]` / `[x]`), inline `> **Q:** / > **A:**` log under each item so reasoning survives `/clear` or compaction. Hard-stops at `N`. Resolves the branch plan on a branch, the master plan on `main`, or an explicit path. |
| `/hitl-step N [path]` | Same loop against a `TODO.md` plan file, resolved identically, but with a richer marker model (`[ ] [~] [x] [!] [-]`), explicit confirmation gates on writes, and parent/subgoal state propagation. Use this when each goal needs back-and-forth with you. |
| `/smart-commit` | Delegates to `/agents-docs-update` to sync docs with the staged diff, then commits and pushes. Reads the subject convention from the repository's own history rather than prescribing one. Confirmation-required. |
| `/smart-merge`  | Reads the branch doc and plan to draft PR title and body, warns on unfinished plan items, deletes the doc, stamps the plan `merged` and closes the master-plan item in one pre-merge commit, gates on CI, then merges. Prefers the GitHub MCP server and falls back to `gh`. Walks merge-strategy choice with tradeoffs. |
| `/file-plans`   | Files merged branch plans into revision directories under `docs/plan/`, deriving each plan's revision from the master-plan heading its backlink sits under. Read-only script proposes; the command confirms, moves and commits. Reports what it can't derive instead of guessing. |
| `/open-revision <label>` | Opens a revision — a milestone whose subgoals each spawn a branch. The label (`04-revision-lifecycle`) names both the master-plan heading and the directory. You supply the label and the preamble; the command does not invent either. |
| `/close-revision <label>` | Cuts a finished revision's section out of the master plan into `docs/plan/<label>/_DO.md`, leaving a pointer. Keeps the master plan an index rather than an ever-growing log. You decide the revision is finished; the command refuses if items are still open. |
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

#### Closing a revision

The master plan would otherwise grow forever: every subgoal ever completed stays in it, with its `> **Done:**` annotation. When a revision is finished and its branches are merged and filed, **`/close-revision <label>`** cuts that revision's section out of `docs/plan/DO.md` and into `docs/plan/<label>/_DO.md`, leaving a one-line pointer behind. The master plan then reads as an index of closed revisions plus whatever is open, and everything about a finished revision — its subgoals, its `> **Done:**` records, and the branch plans that executed them — lives in one directory.

Run `/file-plans` first, or the revision directory ends up holding an archive that describes branch plans still sitting flat elsewhere.

The archive is `_DO.md`, not `DO.md`, and the underscore is load-bearing: plan resolution globs `docs/plan/**/DO.md` and matches on filename, so an archive named `DO.md` would be offered in the disambiguation prompt as a place to do work. The underscore keeps a finished revision out of resolution entirely. It stays reachable by explicit path.

**This is the one step in the workflow with a real judgement in it, and the command does not make it.** A revision is closed when you say it is, not when its last checkbox ticks — you may still add subgoals to a revision whose earlier items have all shipped, as this project did, folding three new ones into revision 3 after its first three had merged. You supply the label; the command does the extraction, and refuses if the revision still has open items.

- **Confirm before writes.** Every command treats git writes (commit, push, branch deletion) and file deletions as confirmation-required. Read-only diagnostics (`git status`, `git log`, `git diff`) run freely.
- **Hard stops on counters.** `/step N` and `/hitl-step N` stop after `N` iterations even if work remains. They won't ask "continue?".
- **Never edit generated files directly.** The bundled `protect-agent-docs.py` hook blocks `Write`/`Edit`/`MultiEdit` against `CLAUDE.md`, `AGENTS.md`, and `AGENTS.override.md` once `docs/agents/` sources exist. Edit the sources and let `/agents-docs-build` regenerate.
- **GitHub work prefers MCP, falls back to `gh` — out loud.** `/smart-merge` uses the GitHub MCP server when one is available and `gh` otherwise. The fallback triggers on **404 or 403**: a fine-grained PAT that doesn't cover a repository returns 404, not 403, because GitHub masks private-repo existence — so a rule keyed only on 403 would never fire in the case it exists for. Every fallback is announced with the repository and operation named, which turns a recurring fallback into a legible signal that the PAT's scope wants widening. A silent fallback would make a narrowly-scoped token pointless.
- **The two merge paths clean up differently.** `gh pr merge --delete-branch` removes the branch locally and remotely in one call; the MCP `merge_pull_request` has no such parameter and removes neither. `/smart-merge` closes that gap explicitly — remote branch first, then sync `main`, then the local branch, in that order, because `git branch -d` evaluates against `HEAD` and would refuse on every merge if it ran before the sync.
- **Plans are two-tier, and both tiers live on `main`.** The **master plan** (`docs/plan/DO.md` or `TODO.md`) defines subgoals; each spawns a branch. A **branch plan** covers one branch's work, in a directory named for the branch with `/` flattened to `-`. That name is its identity, not its path: `/new-branch` creates it flat under `docs/plan/`, but every command finds it by searching for that name anywhere beneath `docs/plan/`, so plans can be regrouped into milestone or component directories with `git mv` and nothing needs updating. `/step` and `/hitl-step` resolve in priority order — explicit path, then the current branch's plan, then the master plan, then glob-and-ask, then a legacy root-level file — so neither normal working position ever prompts. Branch plans are **not** deleted at merge: they accumulate on `main` as the durable record of how each subgoal was executed, navigable by directory and filtered out of the disambiguation prompt by their `**Status**: merged` stamp.
- **The PR body is a pointer, not an archive.** `/smart-merge` puts a `Plan:` line in the body rather than pasting contents — GitHub caps PR bodies at 65,536 characters, and the plan file itself lands on `main` anyway. **And it names the plan rather than pointing at a path.** PR bodies are effectively immutable while plan locations are deliberately free, so a path pointer is correct only until the next filing sweep — the first one broke seven at once, including the pointer in the PR that performed the move. A name survives every regrouping and resolves the way the commands resolve a plan. The bodies of PRs #1-#11 predate this and keep their stale paths: read those as names to search for, not paths to follow.
- **Master-plan access is locate-then-window.** The master plan accumulates every subgoal of every revision and grows without bound; `/smart-merge` and the step commands each need one line out of it. They `Grep` for that line and read a bounded window rather than loading the file. Measured: at 250 subgoals a whole-file read is ~55k tokens and 0.39% of it is the part being edited, and past ~500 subgoals the file exceeds the default 2000-line read limit and truncates — after which a lookup that misses looks exactly like having nothing to do. Hence the second half of the rule: a zero-match lookup is always reported, never passed over in silence.
- **`docs/git/<branch>.md` is per-branch scratch.** Created by `/new-branch`, consumed and deleted by `/smart-merge`. It stays in the branch's history (recoverable via SHA) but never lands on `main`.
