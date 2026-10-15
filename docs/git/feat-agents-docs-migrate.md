# feat/agents-docs-migrate

**Created**: 2026-10-15
**Base**: main at 5b9262e
**Status**: active

## Purpose

R2 subgoal 9. One command, `/agents-docs-migrate`, takes a repository from a legacy `CLAUDE.md`, or from this plugin's dispatcher layout, to §4.3's target: a hand-authored `AGENTS.md` of 200 lines or fewer, one guide per subagent at `docs/agents/<guide>/AGENTS.md`, dated history under `docs/agents/_history/`, and no `CLAUDE.md` unless the shim is needed. A new read-only agent, `docs-classifier`, proposes where each section goes; the command makes every write, after the user confirms. It replaces `/agents-docs-init` and `/agents-docs-codex-init`, which are removed. Since PR #29 the build refuses the dispatcher layout those two write, so until this lands a consumer has no supported way into the new layout.

## Scope

- `plugins/workflow-coding/agents/docs-classifier.md`, new, per §4.1's row: sonnet; `Read, Grep, Glob, Bash(find:*)`; returns a destination table with flagged uncertainties.
- `plugins/workflow-coding/commands/agents-docs-migrate.md`, new, per §4.3: it detects the three states; Checkpoint 1 shows the destination table; the moves are verbatim, then Checkpoint 2 shows the results; the one destructive step comes last, CONFIRM FIRST; monorepo components are targets; the Codex sidecar becomes the `codex-review/` guide step.
- The version check and the two-line `@AGENTS.md` shim, per D-N6, with the `CLAUDE.local.md` check.
- `commands/agents-docs-init.md` and `agents-docs-codex-init.md` removed, and their mentions in the plugin's `README.md`, `CLAUDE.md` and `_meta/plugin-conflict-report.md` command list replaced.
- An end-to-end run on a copy of `tmp/pfsmgraph`, the dispatcher entrance, and on a repository with one legacy `CLAUDE.md`.

## Context

- Master plan: R2 subgoal 9, `docs/plan/08-subagent-refactor-R2/_TODO.md:71`. Builds on subgoal 7 (PR #29), after which the build reads only `codex-review/` guides and refuses the dispatcher layout, and follows the agent conventions subgoal 8 set for `docs-sync` (PR #30).
- Design: `tmp/subagent-refactor-plan.md` §4.1 (the agent's row, line 283, and the conventions every agent follows, bodies under 3,000 characters), §4.3 (the target layout and `/agents-docs-migrate`), D-N6 (the shim), §7.7 (the migration's verification) and §8 (the `CLAUDE.local.md` row).
- §4.1 asks of every agent first whether the job needs judgement or only rules. Placing prose needs judgement, so it is the agent's; detecting the state, comparing versions and checking that a move is verbatim are rules, so they belong in scripts with `problem:`/`fix:` diagnostics.
- `tmp/pfsmgraph` holds the dispatcher layout: `CLAUDE.md`, `docs/agents/{core,claude,codex}.md`, a generated `AGENTS.md` and `AGENTS.override.md`.
- Subgoal 12 owns §4 of `_meta/plugin-conflict-report.md`; subgoal 14 owns the release notes.
- The installed plugin is 0.10.1, so this branch's commands reach a session only at 0.11.0 (subgoal 14). End-to-end runs load the branch's plugin with `--plugin-dir`, as `dev/docs-sync-e2e/` does.

## Notes

- 2026-10-15 — Goal 01 under way. `agents/docs-classifier.md` is in: sonnet, `Read, Grep, Glob`, a 2,606-character body. Five Q&As in its goal file settle the table: one row per line range, every non-blank line in exactly one; a closed set of destinations, with `drop: obsolete` always flagged; each `codex.md` moved whole by rule; guide names from those with a reader, any other flagged. §4.1's `Bash(find:*)` was dropped, since `guard-agent-git.py` refuses `find` for this plugin's agents and subagents keep `Glob`. Reading anything under `tmp/pfsmgraph` loads its nested `CLAUDE.md` and both imports into the session, so goal 05's fixtures go outside the repository. Next is subgoal 3: a headless run on pfsmgraph's sources and a small legacy `CLAUDE.md`, graded by a scratchpad checker whose self-test passes 17/17.
- 2026-10-15 — Goal 01 done. Run c1 ($0.47) showed the first body routing 881 lines of pfsmgraph, ≈ 47.6k tokens, to `AGENTS.md` and flagging nothing. A revised body took that to 120 lines, ≈ 8.3k, in run c2 ($0.52), where both fixtures passed every rule and the legacy fixture's three judgement probes held. The rules the agent skipped as prose, flagging obsolete drops, new guides, dated lines bound for `AGENTS.md` and overlong lines, became flags goal 02's script sets, and the script reads a single-line row `<file>:<n>` as `<n>-<n>`. Next is goal 02, whose script and suite start from the scratchpad grader, now 20/20 on its self-test.
- 2026-10-15 — Goal 02 under way. `scripts/migrate-agents-docs.py` has its two read-only modes: `detect` finds each target's state, sources, `codex.md` and `CLAUDE.local.md`, and `check` checks docs-classifier's table and plans what `apply` will write. `dev/agents-docs-migrate/` tests them: 45 cases, 57 mutants, each killed by its rule. Six decisions are logged in goal 02's file, four of them prompted by side-agent notes: every link the moves would break is rewritten for its new folder; pointer lines in `AGENTS.md` carry only the moved text's own headings, since the agent's `what` cells are its own words; drops whose named file carries less than 80% of their text are flagged; and only links the move broke stop the delete. On c2's real reply, `check` covers pfsmgraph's 59 rows exactly and plans `AGENTS.md` at ≈ 9,350 tokens. Next: `apply`, `verify`, then the command file.
- 2026-10-15 — `apply` and `verify` landed; the suite is at 58 cases and 70 mutants. `apply` writes `check`'s plan and only over committed files, so a second run stops at its own work. `verify` finds every moved row in its destination, lists links already dead in their sources, and stops the destructive step on a link the move broke, such as one re-pointed to a component `AGENTS.md` that nothing writes because all its rows were dropped. On goal 01's c2 reply, `apply` wrote pfsmgraph's 15 files, `verify` found 53 of 53 moves, and an independent check found all 36 rewritten links resolving. `detect` had to learn that `apply`'s own `codex-review/AGENTS.md` is no clash. Next: the command file.
- 2026-10-15 — Two fixes to `7669e0b`. A commit security review found `apply` writing through symbolic links, reproduced on a scratch repository whose committed `docs/agents/release` linked outside it; no mode now reads or writes through a link at any component of a path. A side agent found that a commit between two `apply` runs hid the first from its git-based guard; `apply` now also refuses when a destination already carries its row's text, and `verify` fails a row found twice. The suite is at 65 cases and 79 mutants, one declared equivalent.
