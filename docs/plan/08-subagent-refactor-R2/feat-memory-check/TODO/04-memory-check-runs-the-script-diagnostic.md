# 04 — /memory-check runs the script, diagnostic only

**Goal**: [x]
> **Done:** `/memory-check` is a thin command over the script, granted that script alone, listed in the plugin's README and `CLAUDE.md`, and a headless session ran it as written.
> **Q:** Should `/memory-check` grant the script alone, run it with `TODO.md` and then `DO.md` when the report says there is no root `docs/plan/TODO.md`, show the report as printed with a short reading that never treats a `by line` file as a problem and leaves any split to `/hitl-step` and the user, and be listed in the plugin README's scripts list and plan-command table and in the plugin `CLAUDE.md`'s command and script-backed lists (A), or change part of it (B)?
> **A:** A, as drafted: the script's own `none` is the model check, so the grant stays one script path, and the reading keeps a large master plan, read in windows, from looking like a problem.

- [x] `commands/memory-check.md` runs the script alone and relays its report, writes nothing, and grants nothing it does not run
  > **Note:** One headless session (`claude -p "/workflow-coding:memory-check" --plugin-dir plugins/workflow-coding`, $0.30): one Bash call, `memory-check.sh TODO.md --`, run alone, with no permission denial under the one-script grant; the report shown as printed, then a reading that named the largest file read whole and called `_TODO.md` `by line`, never a problem; `git status` unchanged. Its one other call, a `Read` of `tmp/session-handoff.md`, came from this repository's root `CLAUDE.md`, not the command.
- [x] `dev/command-phrasing` passes with the new command
  > **Note:** `check.py` lists `memory-check.md` as skipped, since it grants no `git`, with 0 failing; the suite's 35 cases pass.
