---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/build-agents-md.sh:*)
description: Regenerate AGENTS.override.md from the Codex reviewer's guide, at the root and in every component.
---

# /agents-docs-build

Regenerate the one generated agent doc in this project, `AGENTS.override.md`. A project's `AGENTS.md` is hand-authored and never built. The bundled `scripts/build-agents-md.sh` builds each override from the Codex reviewer's guide:

- `docs/agents/codex-review/AGENTS.md` → `AGENTS.override.md`
- `docs/agents/<path>/codex-review/AGENTS.md` → `<path>/AGENTS.override.md`, for a component at any depth

Each override is a two-line header naming its guide, a blank line, and the guide verbatim. Only a `codex-review/` guide makes a component: the other guide directories under `docs/agents/` build nothing. The script is deterministic — the same guides give byte-identical output.

## Run

Invoke the script once via Bash:

```
"${CLAUDE_PLUGIN_ROOT}"/scripts/build-agents-md.sh
```

Show its stdout verbatim — every `wrote …/AGENTS.override.md (… lines)` line is the signal the user needs to confirm the right files were written. Show any `warning:` line on stderr too: it names an old `core.md` or `codex.md` left beside the guides, which the build ignores.

If the script exits non-zero, surface its stderr exactly as written and stop: there is no guide to build from, or `docs/agents/` is still in the dispatcher layout (`core.md`, `codex.md`), which the build no longer reads, and the message names the move. Do not retry, and do not attempt to write any `AGENTS.override.md` directly via `Write`/`Edit` — the `protect-agent-docs.py` hook would (correctly) block that.

## Do not

- Run `git add` or commit anything. The caller decides what to stage.
- Edit the guides under `docs/agents/` here. Those edits belong in `/agents-docs-update` or are made by the user directly.
