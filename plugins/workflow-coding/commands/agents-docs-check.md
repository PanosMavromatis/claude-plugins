---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/check-agents-md.sh:*)
description: Verify each AGENTS.override.md (root + every component) matches its Codex reviewer's guide, and lint the hand-authored AGENTS.md files.
---

# /agents-docs-check

Verify that every committed `AGENTS.override.md` (root and per-component, any depth) matches what `/agents-docs-build` would write from its `codex-review/AGENTS.md` guide, and lint the hand-authored `AGENTS.md` files. Intended for pre-commit hooks, CI, or a quick spot check after an edit.

The script builds the overrides into a temp directory and diffs each against its committed counterpart. It exits 0 when the pair is in sync and 1 on drift or a missing file. The exit status means that and nothing else: the lints warn, and never change it.

The lints read every `AGENTS.md` git lists outside `docs/agents/`, tracked or new and not ignored: the root's and each component's, not the guides. Every agent loads an `AGENTS.md` at session start, so each lint warns on stderr when one:

- runs over 200 lines;
- carries a dated line (`20\d\d-\d\d-\d\d`), giving up to five line numbers: dated prose belongs in `docs/agents/_history/`.

## Run

Invoke the script once via Bash:

```
"${CLAUDE_PLUGIN_ROOT}"/scripts/check-agents-md.sh
```

Show its output verbatim:

- Exit 0 and `Agent docs are in sync with docs/agents/`, with `(N warnings)` when the lints found any → report the pair clean, list each `warning:` line, and stop.
- Exit 1 with `--- drift in <file> ---` blocks or `missing: <file>` lines → surface them, and any warnings, and tell the user to run `/agents-docs-build` and commit the regenerated files.
- Exit 1 with an `error:` line → the build the check runs failed: there is no guide, or `docs/agents/` is in the dispatcher layout. Surface it as written.

Do not attempt to fix drift or a warning inside this command. The fix for drift is `/agents-docs-build` plus the user's review; a warning is the user's to act on, in the `AGENTS.md` it names.
