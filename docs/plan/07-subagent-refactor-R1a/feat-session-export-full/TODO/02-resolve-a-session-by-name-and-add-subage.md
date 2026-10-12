# 02 — Resolve a session by name, and add subagents on request

**Goal**: [~]
> **Q:** The Markdown drops tool output, hidden reasoning and token counts, and Claude Code deletes the raw log after `cleanupPeriodDays`, so R2's token measure would have nothing to read. Should the export keep the raw log too?
> **A:** Yes: the raw `.jsonl` beside the `.md`, as `<name>.jsonl` next to `<name>.md`. The Markdown is for reading; the raw log is for an agent to dig into when needed.
> **Q:** Large tool outputs live only in the session's folder, `<uuid>/tool-results/`, with a preview and a pointer in the log, and subagent transcripts in `<uuid>/subagents/`. Should the export keep that folder too?
> **A:** Yes: the whole `<uuid>/` folder, named for the session's `/rename` name, so that `<name>.md`, `<name>.jsonl` and the folder sit side by side; perhaps as a compressed tar, unpacked only when needed.
> **Note:** Checked 2026-10-12 on this session's log: two tool results are 2 KB previews ("Output too large (50.3KB). Full output saved to: …") whose full text exists only in `tool-results/`. The folder held 112 KB of tool results, 216 KB of subagent transcripts, and `custom-title.json`.
> **Q:** How is `export-session.py` told which session to export: a name or a log path as its first argument, resolved by the script (A), a separate `--find` mode (B), or a log path only, with the command finding the log (C)?
> **A:** A.

- [x] A renamed session with several `custom-title` records takes its name from `<uuid>/custom-title.json`, and a suite case pins it
  > **Note:** A name is looked up among this project's logs, in `$CLAUDE_CONFIG_DIR` (else `~/.claude`)`/projects/<cwd, each non-letter, non-digit made ->`, by each log's `<uuid>/custom-title.json`; none or several is refused with exit 1. Checked on this project (2026-10-12): each of the three sessions with title records in its log has a `custom-title.json`, holding the last of them. The R1 log carries `multi-agent-refactor` 586 times and `multi-agent-refactor-r1` 632 times: by its current name it renders as 329 operator messages, 996 replies and 16 compactions, and its old name matches nothing. Cases `n01`–`n05`; `m06`, which matches any name a log has had, as the old runbook's `grep` did, is killed by `n02`. A missing output directory raises a traceback, and subgoals 3 and 4 write into that directory.
- [ ] Subagent transcripts (`<uuid>/subagents/`) appear only when asked for, with a suite case each way
- [ ] Beside `<name>.md` the script writes the raw log, byte for byte, as `<name>.jsonl`, refusing to overwrite the log it reads, and a suite case pins it
- [ ] Beside them it writes the session's folder, `<uuid>/`, under the same name: decide whether as a directory, `<name>/`, or a compressed `<name>.tar.gz`, log the decision here, and a suite case pins it
