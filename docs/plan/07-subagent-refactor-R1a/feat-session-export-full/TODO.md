# feat/session-export-full

**Status**: active
**Created**: 2026-10-12
**Revision**: 07-subagent-refactor-R1a
**Subgoal**: 3. `/workflow-coding:session-export-full` exports a session's whole JSONL log, compactions included, through a script with a suite and a thin command. Subagent transcripts are optional, and the output goes outside the repo.
**Layout**: per-goal

## Goals

- [ ] 01 — Move the export script into the plugin, with a suite
- [ ] 02 — Resolve a session by name, and add subagents on request
- [ ] 03 — Write the session-export-full command
- [ ] 04 — Export a real session outside the repo
