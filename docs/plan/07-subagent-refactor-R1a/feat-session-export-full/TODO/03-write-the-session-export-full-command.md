# 03 — Write the session-export-full command

**Goal**: [x]
> **Done:** `commands/session-export-full.md` is one script run, the named session or this one, to `~/claude-exports/<project>/` unless an output is given; the script, now taking a session id and naming its export for the session, enforces the rest, with 25 cases and 18 mutants.
> **Note:** Claude Code's costs page (fetched 2026-10-12) says session data older than `cleanupPeriodDays` is removed at startup, "30 days by default".
> **Q:** With no argument, which session does `/session-export-full` export: this session, through `${CLAUDE_SESSION_ID}` (A), or none, so a name is required (B)?
> **A:** A.
> **Q:** Where do exports go by default, always outside the repository: `~/claude-exports/<project>/` (A), a path proposed and confirmed each time (B), or beside the session logs (C)?
> **A:** A.
> **Note:** Claude Code's docs list `${CLAUDE_SESSION_ID}` among the substitutions for skills and say nothing either way for a plugin's `commands/`; `${CLAUDE_PLUGIN_ROOT}` is substituted in this plugin's commands, so it likely is too. If it is not, the script refuses with "no session named '${CLAUDE_SESSION_ID}'" rather than exporting another session; the first run on 0.10.1 settles it.
> **Note:** Settled in goal 04 (2026-10-12): a run with no argument, through `claude --plugin-dir`, exported its own session, so a plugin command does get `${CLAUDE_SESSION_ID}` substituted.

- [x] `plugins/workflow-coding/commands/session-export-full.md` is a thin command over the script: it finds the session, picks an output path outside the repository, runs the script, and reports
  > **Note:** The command is one script run: the session the user names, else this one as `${CLAUDE_SESSION_ID}`, an output only if given, and `--subagents` only if asked; the script finds the session, names and writes the files, and refuses an output inside the repository. To keep the command that thin the script gained a session id, an optional output named for the session (its `/rename` name, else its id) in `~/claude-exports/<this directory's name>/` by default, and the repository guard. Checked on this session by id (written as `multi-agent-refactor-r1a.md` under a scratch `HOME`) and on a path inside this repository (refused, nothing written). Cases `i01`, `o01`–`o04`; mutants `m15`–`m18`.
- [x] Its `allowed-tools` grants the script run and its read-only steps, and nothing else, as the plugin's other commands do
  > **Note:** `allowed-tools` grants only `Bash(python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/export-session.py:*)`: the command runs nothing else, and the script writes only in the export's own directory, outside the repository.
- [x] Verify the `cleanupPeriodDays` default in Claude Code's settings reference, and the command's text states it
  > **Note:** The settings reference lists `cleanupPeriodDays` without its default; the `~/.claude` directory page (fetched 2026-10-12) gives it: "The default is 30 days and the minimum is 1; setting `0` fails with a validation error", and lists `<session>/subagents/` and `<session>/tool-results/` among what it deletes. The command states the default and the minimum.
