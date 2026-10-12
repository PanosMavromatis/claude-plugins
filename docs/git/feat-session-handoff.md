# feat/session-handoff

**Created**: 2026-10-12
**Base**: main at 3285123
**Status**: active

## Purpose

Add `/workflow-coding:session-handoff`, which writes `tmp/session-handoff.md` for the next session in `/smart-compact`'s three parts (Keep / Drop / Say where), and a root `CLAUDE.md` that has the next session read it first. The 0.10.0 driver cannot run a new command, so the command's text must work when a session follows it as a plain file. The root `CLAUDE.md` also carries the workflow's `# Compact instructions`, the static half of `/smart-compact`'s Compose. This is R1a subgoal 2, and it ships in `workflow-coding` 0.10.1.

## Scope

- `plugins/workflow-coding/commands/session-handoff.md` (new), needing no `$ARGUMENTS`, no `${CLAUDE_PLUGIN_ROOT}` and no `allowed-tools`.
- `CLAUDE.md` at the repository root (new): the conditional read-the-handoff-first line, and a `# Compact instructions` section with §4.4's Drop list and Say-where convention.
- A dogfood run on the 0.10.0 driver: one session follows the file and writes the handoff, and a fresh one reads it first.
- Not in scope: documenting the command in the READMEs (R1a subgoal 4, the release), or how the handoff couples with `/smart-compact` (R2 decides that by measurement).

## Context

- R1a subgoal 2 is at `docs/plan/07-subagent-refactor-R1a/_TODO.md:57`, with its settled decisions at `:19`–`33` and `:49`–`50`.
- The design is `tmp/subagent-refactor-plan.md` §4.4 (`/smart-compact`), including "What `/smart-compact` is for (2026-10-12)". It is untracked, since `tmp/` is gitignored.
- The model handoff is `tmp/session-handoff-r1-r1a.md`, written by hand in the R1→R1a session in the shape this command will produce. It was kept (renamed) rather than deleted, because its "For R2" section is still live.
- Settled in goal 02: a read handoff is archived to `tmp/handoffs/<YYYY-MM-DD>-<branch>.md` once the user confirms, not deleted; the dated settled decision at `_TODO.md:50` amends `:30`–`31`.
- The plugin's `protect-agent-docs.py` blocks `CLAUDE.md` writes only when `docs/agents/core.md` exists, and this repository has no `docs/agents/`.

## Notes

- 2026-10-12: the goal files are written with their subgoals, by hand from the subgoal's Acceptance line, until R1a subgoal 5 ships in 0.10.1.
- 2026-10-12, goal 01: `commands/session-handoff.md` takes the plan from the session's latest `locate-plan.sh` report and never searches for it (goal 01's Q&A), and first flushes unlogged decisions to the plan. Found on the way: §4.3's target has no `CLAUDE.md`, so wherever it is adopted, goal 02's `CLAUDE.md` must move into `AGENTS.md`.
- 2026-10-12, goal 02: the root `CLAUDE.md` (1014 bytes; 1278 after goal 03's fix) has the next session read the handoff first and archive it, and holds `# Compact instructions`, §4.4's Drop list and Say where with no static Keep. Claude Code's docs give that heading, place it under automatic compaction, and re-inject the project-root `CLAUDE.md` after every compaction.
- 2026-10-12, goal 03: a side agent found that `CLAUDE.md` said what to do with a handoff but not when, so a writer re-injected after compaction could archive its own; it now acts only at a session's start. Then this session wrote a 52-line handoff by following the command as text, and a fresh session read it first, summarised it and archived it on confirmation: 2 tool calls and about 3 KB before its first action, nothing restated. Found: once archived, a handoff's remaining steps reach only its reader, the reader-side Flush for R2.
