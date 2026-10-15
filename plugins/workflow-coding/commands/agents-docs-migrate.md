---
allowed-tools: Bash(git status:*), Bash(git rev-parse --show-toplevel:*), Bash(git diff:*), Bash(python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-agents-docs.py:*), Agent, Read, Write, Edit
description: Move a project's agent instructions, from a legacy CLAUDE.md or the dispatcher layout, into AGENTS.md, a guide per agent and _history/.
---

# /agents-docs-migrate

Move this project's agent instructions into the layout every agent reads natively:

- `AGENTS.md` at the root, and `<path>/AGENTS.md` for each component: hand-authored, present tense, no dates, 200 lines or fewer. Every agent loads it at the start of every session.
- `docs/agents/[<path>/]<guide>/AGENTS.md`: a guide that one agent, or several, reads first.
- `docs/agents/_history/<area>.md`: dated prose, never loaded at session start.

There are two ways in: a legacy `CLAUDE.md`, or this plugin's dispatcher layout, a `CLAUDE.md` importing `docs/agents/[<path>/]core.md` and `claude.md`, beside a `codex.md`. The `docs-classifier` agent proposes where each part goes. The bundled script checks its table, moves each part verbatim, and checks the moves, so no line of the new files is a model's. You run them in order, and stop at each checkpoint for the user.

**Phrase each command so `allowed-tools` matches it.** Run `git` in the repository as `git <subcommand>`, never `git -C <path>`: the session already runs in the repository, and a permission matches the plain form only, so `git -C <path> status` is refused where `git status` is granted. Run every command alone, one `Bash` call each, with nothing chained (`;`, `&&`), piped (`|`) or appended (`2>&1`): Claude Code checks each part of a chain on its own, and one part not granted, a `git -C` or a read outside the repository, makes it prompt for the whole command, or refuse it in a headless run, and hides which part it was. Read a file with `Read`, not by piping it through `head`.

## The script

Run it from the repository's root, alone, in exactly this form, `<reply>` being the reply file (Step 1) for every mode but `detect`:

    python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/migrate-agents-docs.py <detect|check|apply|verify> [<reply>]

It reports in `key: value` lines, a key with several items continuing on lines indented two spaces, `—` for none, and `message:` last. Act on `result:`, and relay each `problem:` line with the `fix:` line beside it. A report with no `result:` or no `message:` line is a usage error or was cut short: show it, and stop. Never act on part of a report.

## Step 1: Preflight

1. Run `git status --porcelain`. If it lists anything, stop, and ask the user to commit or stash first: a migration is undone with `git restore` and by removing the files it created, which is safe only from a clean tree.
2. Run `git rev-parse --show-toplevel`. The **reply file** is `/tmp/agents-docs-migrate/<that path, each / as ->.md`: outside the repository, where neither `git status` nor the script sees it.

## Step 2: Detect

Run `detect`.

- `error`: relay each `problem:` with its `fix:`, and stop.
- `none`: there is nothing to migrate, no `CLAUDE.md`, no dispatcher sources and no `AGENTS.md`. Say so, and stop.
- `migrated`: the project is migrated already. Give each `AGENTS.md` under `sizes:` with its lines and ≈ tokens. Of one over 200 lines or ≈ 5,000 tokens, say so, and that `docs-sync`, the agent `/agents-docs-update` runs, keeps it in shape by its routing rule: dated prose to `_history/`, what only some agents need to their guide. Trimming a live `AGENTS.md` is not this command's work. Write nothing, and stop.
- `migrate`: show `targets:`, `sources:`, `codex:`, `delete:` and any `warnings:`, and go on. A target already migrated is left as it is.

## Step 3: Classify

Use the `Agent` tool once, with `subagent_type` `workflow-coding:docs-classifier`, and give it this task: classify these sources, each for its target, naming each exactly as `sources:` does. A `<path>/CLAUDE.md` is for target `<path>`, as are `docs/agents/<path>/core.md` and `claude.md`; the root's `CLAUDE.md`, `docs/agents/core.md` and `claude.md` are for target `.`. Pass it no `codex.md`: the script moves each whole.

Act only on its hand-back: if it runs in the background, wait for its report. Do not read or classify a source yourself.

Write its report to the reply file with `Write`: from its `## Table` line to the end of its `## Notes`, each line as returned, without the frame Claude Code puts around a subagent's report or that frame's two-space indent.

## Step 4: Check

Run `check <reply>`.

- `problems`, its message saying the reply was copied in its frame: write it again as Step 3 says, and check again.
- `problems` otherwise: the table is the agent's to redo. Spawn it once more, with the same task and each `problem:` line with its `fix:` line, write its report over the reply file, and check again. If the second table fails too, show its problems, and stop.
- `error`: relay it, and stop.
- `clean`: go on.

## Step 5: Checkpoint 1 — the table, before anything is written

Show:

1. The table, row by row, grouped by target, with each row docs-classifier flagged `unsure`, and why.
2. `writes:`, each file `apply` would write, how, and its size. Every session loads a target's `AGENTS.md` whole: of each marked over 200 lines or ≈ 5,000 tokens, say so plainly, and by how much.
3. One decision per guide under `unread:`. No agent of this plugin reads it, so its ≈ tokens leave every session's start. Name its rows: the user keeps it, for an agent of the project's own, or routes its rows elsewhere.
4. The rule flags under `flags:`, grouped by kind: obsolete drops; dated rows bound for an `AGENTS.md`; lines over 2,000 characters, which `Read` cuts; and duplicate drops whose named file carries less than 80% of the row, with the share.
5. `repointed:`, and docs-classifier's `## Notes`.

Then ask the user to approve the table, or to change it; `AskUserQuestion` suits a choice between options, such as a guide's. A change is made in the reply file's table: `Edit` the rows the user names, a destination or a line range, and nothing else. Run `check` again and show this checkpoint again, until the user approves. A fresh table, if the user asks for one, is Step 3 again. Nothing is written in the repository before the user approves.

## Step 6: Apply

Run `apply <reply>`. It writes what `check` planned, and deletes nothing.

- `written`: go on.
- `problems` or `error`: nothing was written. Relay each `problem:` with its `fix:`, and stop.

## Step 7: Verify

Run `verify <reply>` at once. It is read-only.

- `clean`: go on.
- `problems` or `error`: the moves are not proven, and nothing may be deleted. Go on to Checkpoint 2, and show each `problem:` with its `fix:` there.

## Step 8: Checkpoint 2 — what was written

Show:

1. `wrote:`, each file with how it was written and its size. Show each target's `AGENTS.md` whole, since every session loads it; show any other file, or `git diff` of one appended to, when the user asks.
2. `repointed:`, each link pointed from a source being deleted to where its text went.
3. Every dropped row, in full: `Read` its lines from its source, and give the file it duplicates and the share found there, or why it is obsolete, from `drops:`. Once the sources go, this text is gone.
4. `dead:`, links already dead in their sources, which the move did not break.
5. `verify`'s `moved:` line, and its result.
6. `delete:`, the sources the move leaves redundant, and `pointers:`, each line elsewhere that points at one of them, for the user to repoint.

## Step 9: Report

Nothing has been deleted: the sources under `delete:` are still in place beside what `apply` wrote. Say so, and that `git restore` on each file `apply` appended to or replaced, and removing each file it created, undoes the move. Name the reply file, kept so that `verify` can run again. Delete nothing, and commit nothing.

## Never

- Write, edit or move a destination's text yourself: `apply` moves it, so every line of it is source text, a fixed template or a rewritten link. A change the user makes after Checkpoint 2 must pass `verify` again.
- Edit a source, or classify one yourself.
- Commit or push.
