# feat/session-export-full

**Created**: 2026-10-12
**Base**: main at bbd046f
**Status**: active

## Purpose

Add `/workflow-coding:session-export-full`, which exports a session's whole JSONL log as readable Markdown, compactions included, because `/export` writes only what is in context and loses everything before a compaction. The rendering moves from `tmp/export_session.py` into the plugin as `scripts/export-session.py`, with a no-model suite, and a thin command drives it. Subagent transcripts are optional, and the output goes outside the repository. This is R1a subgoal 3, and it ships in `workflow-coding` 0.10.1.

## Scope

- `plugins/workflow-coding/scripts/export-session.py`, started from `tmp/export_session.py` (untracked, 114 lines).
- Its suite under `dev/export-session/`, with a case for each of the four measured defects.
- Resolving a session by its current name through `<uuid>/custom-title.json`, and subagent transcripts (`<uuid>/subagents/`) only on request.
- The raw record beside the Markdown: the log as `<name>.jsonl` and the session's folder, `<uuid>/`, under the same name, as `<name>.tar.gz` (decided in goal 02).
- `plugins/workflow-coding/commands/session-export-full.md` (new), stating the verified `cleanupPeriodDays` default.
- An acceptance run: a real session exported to a path outside the repository.
- Not in scope: documenting the command in the READMEs (R1a subgoal 4, the release).

## Context

- R1a subgoal 3 is at `docs/plan/07-subagent-refactor-R1a/_TODO.md:63`, with its settled decisions at `:34`–`44`, `:47` and `:51`.
- The four defects, measured 2026-10-11 on the R1 session's log (55 MB, 16 compactions, 0.28 s): double-encoded em dashes, the `/compact` instructions never captured, a title hard-coded to `m2-tier-1a` (all three fixed that day), and a renamed session carrying several `custom-title` records (fixed in goal 02).
- `cleanupPeriodDays`: Claude Code's costs page (fetched 2026-10-12) says session data older than it is removed at startup, "30 days by default".
- The export script stays Python (settled 2026-10-12, `_TODO.md:47`).

## Notes

- 2026-10-12: the goal files are written with their subgoals, by hand from the subgoal's Acceptance line, until R1a subgoal 5 ships in 0.10.1.
- 2026-10-12, goal 01: `scripts/export-session.py` is ported, byte-identical in output to `tmp/export_session.py` on a real 15 MB log, with UTF-8 named on both ends: under a Latin-1 locale the original crashes and the port does not. For R1a subgoal 4: `plugins/workflow-coding/README.md:11` says every script but the two agent-docs ones serves the plan workflow and is read-only, and `export-session.py` is neither.
- 2026-10-12, goal 01 closed: `dev/export-session/` has 8 cases and 5 mutants, under a second each. Run against `tmp/export_session.py`, it fails only the encoding and usage cases, so the three 2026-10-11 fixes were already in it; mutant `m02` reproduces the double-encoded em dash byte for byte.
- 2026-10-12: two side agents found that the Markdown is not the full record, and neither is the log alone: the Markdown drops tool output, reasoning and token counts, and the log keeps only a 2 KB preview of a large tool output, whose full text is in `<uuid>/tool-results/`. The export now keeps both beside the Markdown (R1a `_TODO.md:51`); goal 02 adds the copies and decides directory or compressed tar.
- 2026-10-12, goal 02: the script takes a session's name as well as its log path, and finds a name through each log's `<uuid>/custom-title.json` in this project's log directory (honouring `CLAUDE_CONFIG_DIR`). The R1 log carries both its names, 586 and 632 times; by its current name it renders as 329 messages, 996 replies and 16 compactions, and its old name matches nothing. The suite has 13 cases and 6 mutants.
- 2026-10-12, goal 02: `--subagents` places each subagent's transcript after the call that spawned it, collapsed, and one whose call is missing in an appendix. Found on this session's log: a subagent's records are all sidechain records, which the main filter drops, and its answer comes back as a `SubagentHandback` call's `message`, here a 10.5 KB draft, not as text. The renderer is now one function, its main output byte-identical on a 15 MB log; the suite has 16 cases and 10 mutants.
- 2026-10-12, goal 02 closed: beside `<name>.md` the export writes the log as `<name>.jsonl`, byte for byte, and the session's folder as `<name>.tar.gz`, unpacking into `<name>/`. It refuses before writing anything when `<name>.jsonl` would be the log it reads, and creates the output directory. On the R1 session: a 61 MB copy identical to its log, and a 1.4 MB archive of 6 subagent transcripts and 21 tool results. The suite has 20 cases and 14 mutants.
