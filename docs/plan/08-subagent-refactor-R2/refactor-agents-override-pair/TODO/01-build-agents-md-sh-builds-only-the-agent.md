# 01 — build-agents-md.sh builds only the AGENTS.override.md pair

**Goal**: [x]
> **Done:** `build-agents-md.sh` builds only `AGENTS.override.md`, from each `codex-review/AGENTS.md` guide under `docs/agents/`, at the root and in components, and refuses the dispatcher layout by name. Goal 04's suite makes the fixtures tests.
> **Q:** §4.3 shows only the root layout. Where does a component's Codex guide live: at `docs/agents/<path>/codex-review/AGENTS.md`, generating `<path>/AGENTS.override.md` and found by searching `docs/agents/` for `codex-review/AGENTS.md` at any depth (A); beside the component, at `<path>/docs/agents/codex-review/AGENTS.md` (B); or nowhere, the root only (C)?
> **A:** A: it keeps today's `docs/agents/<path>/` → `<path>/` mapping, so subgoal 9 moves a component's `codex.md` one directory down, and only a `codex-review/` guide makes a component, so other guide directories (`plan/`, `kernel/`) produce nothing.
> **Q:** In a repository still in the dispatcher layout (`core.md`, `codex.md`, no `codex-review/` guide), should the build fail and name the move, warning on old sources left beside new guides (A), keep building the old pair as a fallback until subgoal 9 (B), or build nothing and exit 0 (C)?
> **A:** A: a miss is reported, never silent. B keeps the code this subgoal removes, and C would leave a stale `AGENTS.override.md` behind; consumers stay on 0.10.1 until subgoal 14 ships this with subgoal 9's `/agents-docs-migrate`.

- [x] On a fixture in the §4.3 layout, the build writes `AGENTS.override.md` from `docs/agents/codex-review/AGENTS.md`, and a component's from its own `codex-review/` guide, and nothing else: no `AGENTS.md` at any path
  > **Note:** On a fixture with a root guide, a `ui/` component's guide and `plan/` and `kernel/` guides, the build wrote exactly `AGENTS.override.md` and `ui/AGENTS.override.md`, each headed with the guide it came from; the other guides produced nothing. In the dispatcher layout it exits 1 naming the move; old sources beside the guides each get a warning; with no guide it exits 1.
- [x] A hand-authored `AGENTS.md` and a `CLAUDE.md` are left exactly as they were
  > **Note:** On the same fixture, `AGENTS.md`, `ui/AGENTS.md` and `CLAUDE.md` hashed the same before and after the build. The check needs no change for the pair: it builds into a temporary directory and compares what the build produced.
