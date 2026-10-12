# 02 — Resolve a session by name, and add subagents on request

**Goal**: [ ]
> **Q:** The Markdown drops tool output, hidden reasoning and token counts, and Claude Code deletes the raw log after `cleanupPeriodDays`, so R2's token measure would have nothing to read. Should the export keep the raw log too?
> **A:** Yes: the raw `.jsonl` beside the `.md`, as `<name>.jsonl` next to `<name>.md`. The Markdown is for reading; the raw log is for an agent to dig into when needed.
> **Q:** Large tool outputs live only in the session's folder, `<uuid>/tool-results/`, with a preview and a pointer in the log, and subagent transcripts in `<uuid>/subagents/`. Should the export keep that folder too?
> **A:** Yes: the whole `<uuid>/` folder, named for the session's `/rename` name, so that `<name>.md`, `<name>.jsonl` and the folder sit side by side; perhaps as a compressed tar, unpacked only when needed.
> **Note:** Checked 2026-10-12 on this session's log: two tool results are 2 KB previews ("Output too large (50.3KB). Full output saved to: …") whose full text exists only in `tool-results/`. The folder held 112 KB of tool results, 216 KB of subagent transcripts, and `custom-title.json`.

- [ ] A renamed session with several `custom-title` records takes its name from `<uuid>/custom-title.json`, and a suite case pins it
- [ ] Subagent transcripts (`<uuid>/subagents/`) appear only when asked for, with a suite case each way
- [ ] Beside `<name>.md` the script writes the raw log, byte for byte, as `<name>.jsonl`, refusing to overwrite the log it reads, and a suite case pins it
- [ ] Beside them it writes the session's folder, `<uuid>/`, under the same name: decide whether as a directory, `<name>/`, or a compressed `<name>.tar.gz`, log the decision here, and a suite case pins it
