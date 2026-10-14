---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/memory-check.sh:*)
description: Report the size of each plan file the commands read, and warn on any read whole that is over a threshold.
argument-hint: "[label] [--threshold <tokens>]"
---

# /memory-check

Measure what the plans feed into a command's context: each plan file's bytes, words, lines
and ≈ tokens, classed by how the commands read it, with totals per branch and for the
revision, and a warning for each file read whole that is over the threshold. A diagnostic:
it changes nothing, and its result gates nothing.

The bundled `scripts/memory-check.sh` does the measuring. It is read-only and deterministic.
Do not measure the files yourself, and do not read them.

Arguments: `$ARGUMENTS`. A word that is not an option is a revision's label, naming
`docs/plan/<label>/`, open or closed; with none, the script measures the open revision, or
under a legacy root plan the whole tree. `--threshold <tokens>` sets the warning's limit,
2000 by default.

## 1. Measure

Run it alone, in exactly this form, with nothing appended, chained or piped: `allowed-tools`
matches that command and nothing else. Pass `TODO.md`, any `--threshold` from the
arguments, then `--` and the label if one was given:

    ${CLAUDE_PLUGIN_ROOT}/scripts/memory-check.sh TODO.md [--threshold <tokens>] -- [<label>]

If the report is `result: none` and its `message:` says there is no root plan,
`docs/plan/TODO.md`, the project may use the other model: run it once more with `DO.md` in
place of `TODO.md`.

## 2. Relay

Show the report as printed: the numbers are the answer. Then act on `result:`:

- `measured`: say in a line or two what stands out: the largest file read whole, and each
  `warnings:` line. A goal file over the threshold is a goal that may have grown past one
  unit of work; `/hitl-step`'s split escape hatch divides one, and whether to is the user's
  call. A file marked `by line` is never a problem, whatever its size: commands read it in
  windows, so its size never reaches them.
- `ask`: several revisions are open. Show `candidates:` and ask which to measure, then run
  again with the user's choice as the label. Never pick one yourself.
- `none`: say what `message:` says.
- `error`: relay each `problem:` line with its `fix:` line, and stop. The fix is the user's.
- no `result:` line, or no `message:` line (the report was cut short): show the output and
  stop.

Never edit, split or move a plan here. ≈ tokens are bytes × 3 / 7, calibrated against
claude-opus-5-5 on plan files as Read returns them.
