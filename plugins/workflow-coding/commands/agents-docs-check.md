---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/check-agents-md.sh:*)
description: Verify AGENTS.md and AGENTS.override.md (root + every component) are in sync with docs/agents/ sources.
---

# /agents-docs-check

Verify that every committed `AGENTS.md` and `AGENTS.override.md` (root and per-component, any depth) matches what `/agents-docs-build` would emit from the current `docs/agents/` sources. Intended for pre-commit hooks, CI, or a quick spot check after manual edits.

The script regenerates everything into a temp directory and diffs against the committed counterparts. It exits 0 on sync, non-zero on drift or missing artifacts.

## Run

Invoke the script once via Bash:

```
"${CLAUDE_PLUGIN_ROOT}"/scripts/check-agents-md.sh
```

Show its output verbatim:

- Exit 0 and `Agent docs are in sync with docs/agents/` → report clean and stop.
- Exit 1 with `--- drift in <file> ---` blocks or `missing: <file>` lines → surface them and tell the user to run `/agents-docs-build` and commit the regenerated artifacts.

Do not attempt to fix drift inside this command. The fix is `/agents-docs-build` plus the user's review.
