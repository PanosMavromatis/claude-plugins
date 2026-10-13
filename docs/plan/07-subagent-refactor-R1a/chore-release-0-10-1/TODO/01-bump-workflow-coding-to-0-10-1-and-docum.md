# 01 — Bump workflow-coding to 0.10.1 and document the release

**Goal**: [x]
> **Done:** `plugin.json` reads 0.10.1; both READMEs describe the two commands, and the plugin README's new Releases section records 0.10.1; the plugin's `CLAUDE.md` describes both and records a clean validate run.
> **Q:** The repository has no `CHANGELOG.md`, tags or `VERSION`, so `plugin.json` is the release. Record 0.10.1's other changes in a `## Releases` section of the plugin README, newest first, with 0.10.0's rename moved into it (A), in a `plugins/workflow-coding/CHANGELOG.md` (B), or nowhere but where each change belongs and the PR body (C)?
> **A:** A.

- [x] `plugins/workflow-coding/.claude-plugin/plugin.json` reads 0.10.1, and no other file in the repository names a version that disagrees with it
  > **Note:** `plugin.json` is the only file naming the current version; it still parses. The other `0.10.0` mentions are history ("renamed at 0.10.0", "measured on 0.10.0") and stay, save the `claude plugin validate` entry, which the third subgoal updates.
- [x] The root `README.md` and `plugins/workflow-coding/README.md` describe `/session-handoff` and `/session-export-full`, and what else 0.10.1 changes: the plan scripts survive SIGPIPE, `/new-branch` writes each goal file with its subgoals, and every command that grants `git` states how to phrase a command, checked by `dev/command-phrasing`
  > **Note:** The plugin README gains a `### Session commands` table and, as answered above, a `## Releases` section, newest first, with 0.10.1's entry and 0.10.0's rename moved from its opening; its `scripts/` bullet names `export-session.py`. The root README's `workflow-coding` row names the two commands and links the Releases section. `dev/command-phrasing` is not named in the Releases entry, being a marketplace suite rather than part of the plugin; the root README lists it with the other suites.
- [x] The plugin's `CLAUDE.md` names both commands where it describes the others, and its `claude plugin validate` entry records a run at 0.10.1, which the user runs
  > **Note:** "How the commands compose" gains a bullet for both, after `/close-revision`. Run 2026-10-13 at 0.10.1: one warning, the one recorded, that the plugin's `CLAUDE.md` is not loaded as project context; the entry now records the run.
