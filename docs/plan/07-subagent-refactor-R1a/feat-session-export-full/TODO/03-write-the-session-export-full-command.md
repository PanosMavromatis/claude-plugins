# 03 — Write the session-export-full command

**Goal**: [ ]
> **Note:** Claude Code's costs page (fetched 2026-10-12) says session data older than `cleanupPeriodDays` is removed at startup, "30 days by default".

- [ ] `plugins/workflow-coding/commands/session-export-full.md` is a thin command over the script: it finds the session, picks an output path outside the repository, runs the script, and reports
- [ ] Its `allowed-tools` grants the script run and its read-only steps, and nothing else, as the plugin's other commands do
- [ ] Verify the `cleanupPeriodDays` default in Claude Code's settings reference, and the command's text states it
