---
allowed-tools: Bash(python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/export-session.py:*)
argument-hint: "[session name | session.jsonl] [output dir | output.md] [--subagents]"
description: Export a session's whole log as Markdown, with its raw log and folder beside it, outside the repository.
---

# /session-export-full

`/export` writes only what is in context, so after a compaction it loses everything before
the summary. This command exports the whole session from Claude Code's own log, and keeps
the raw record beside the readable copy:

- `<name>.md`: the conversation, every compaction included, and with `--subagents` each
  subagent's transcript where it was spawned;
- `<name>.jsonl`: the session's log, byte for byte, with every tool result and token count;
- `<name>.tar.gz`: the session's folder, with large tool outputs and subagent transcripts,
  if the session has one.

`<name>` is the session's `/rename` name, or its id if it was never renamed.

Arguments: `$ARGUMENTS`

## 1. Run it

Run, alone, with nothing chained or piped:

    python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/export-session.py <session> [<output>] [--subagents]

- `<session>`: the session the user named, by its `/rename` name or its log's path. If they
  named none, this session: `${CLAUDE_SESSION_ID}`.
- `<output>`: a directory or a `.md` path, only if the user gave one. Without it, the
  export goes to `~/claude-exports/<this directory's name>/`.
- `--subagents`: only if the user asked for subagent transcripts.

The script finds the session, names the files, creates the directory and writes all three
files. Do not look for the session or work out the output path yourself.

## 2. Report

- **Exit 0**: its last line names the Markdown file and counts what it holds. Say where
  the three files are.
- **Exit 1**: the script says why: no session of that name, several, an output inside the
  repository, or an export that would overwrite the log it reads. Relay it, and stop.
- **Exit 2**: a usage error. Show it, and stop.

Then say how long the original lasts. Claude Code deletes a session's log and its folder
once they are older than `cleanupPeriodDays`, 30 days by default and at least 1, so the
export is the copy that stays.
