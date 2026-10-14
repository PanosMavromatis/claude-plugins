# 03 — protect-agent-docs.py protects AGENTS.override.md only

**Goal**: [x]
> **Done:** `protect-agent-docs.py` protects only a generated `AGENTS.override.md`, root or component, when its `codex-review/` guide exists; `AGENTS.md` and `CLAUDE.md` are editable everywhere. Goal 04's suite makes the cases tests.

- [x] With the sentinel `docs/agents/codex-review/AGENTS.md` present, a `Write` or `Edit` of an `AGENTS.override.md`, at the root or in a component, is blocked; without it, it passes
  > **Note:** Driven with JSON on stdin and `CLAUDE_PROJECT_DIR` set, as Claude Code runs it: `Write`, `Edit` and `MultiEdit` of the root's and `ui/`'s `AGENTS.override.md` exit 2, naming the guide to edit; `svc/AGENTS.override.md`, with no guide, and every name in a dispatcher-layout project exit 0. A component's sentinel is `docs/agents/<path>/codex-review/AGENTS.md`, the build's mapping reversed.
- [x] `AGENTS.md` and `CLAUDE.md` pass at every path, and the hook's presence check for `CLAUDE.md` is gone
  > **Note:** `AGENTS.md` and `CLAUDE.md` pass at the root and in `ui/`, guides present. The `CLAUDE.md` rule went with its comment-edit exception, which only `/agents-docs-init`'s dispatcher header used; the hook is about 100 lines, from 220. `_meta/plugin-conflict-report.md` §4 still describes the old scope: R2 subgoal 12 updates it.
