#!/usr/bin/env python3
"""PreToolUse hook: block direct writes to a generated AGENTS.override.md.

A project's AGENTS.md is hand-authored, and CLAUDE.md, where there is one, is the
project's own; both may be edited freely. The one generated agent doc is
AGENTS.override.md, which /agents-docs-build writes from the Codex reviewer's guide:

  docs/agents/codex-review/AGENTS.md          ->  AGENTS.override.md
  docs/agents/<path>/codex-review/AGENTS.md   ->  <path>/AGENTS.override.md

A direct edit to it would be overwritten by the next build, and /agents-docs-check would
flag the drift, so the hook blocks a Write, Edit or MultiEdit of it and says which guide
to edit instead. The target's component is its parent directory relative to the project
root, or empty at the root.

The guide is also the *sentinel*: when it does not exist, the write passes through. A
project that keeps an AGENTS.override.md by hand, without this plugin's build, is never
blocked, and neither is one still in the old dispatcher layout (docs/agents/codex.md),
which the build no longer reads.

The build writes AGENTS.override.md through a shell redirect, and this hook matches only
Write, Edit and MultiEdit, so the build itself passes through.

Exit codes:
  0 — allow the tool call
  1 — non-blocking error (malformed input)
  2 — block the tool call; stderr is returned to the model
"""
import json
import os
import sys
from pathlib import Path

PROTECTED = "AGENTS.override.md"
GUIDE = Path("codex-review") / "AGENTS.md"


def _component_path(target, project_root):
    """Return the component path (parent dir of `target` relative to
    `project_root`): "" for root-level targets, "ui" for ui/<basename>,
    "ui/components/buttons" for nested. Returns None if `target` is not
    under `project_root`."""
    try:
        rel_parent = target.parent.relative_to(project_root)
    except ValueError:
        return None
    s = str(rel_parent)
    return "" if s == "." else s


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"protect-agent-docs: malformed hook input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    file_path = payload.get("tool_input", {}).get("file_path")
    if not file_path:
        sys.exit(0)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    try:
        target = Path(file_path).resolve()
        project_root = Path(project_dir).resolve()
    except (OSError, RuntimeError):
        sys.exit(0)

    if target.name != PROTECTED:
        sys.exit(0)

    component = _component_path(target, project_root)
    if component is None:
        # Target lives outside the project root; not our business.
        sys.exit(0)

    docs_agents_root = project_root / "docs" / "agents"
    component_docs_dir = docs_agents_root / component if component else docs_agents_root
    guide_path = component_docs_dir / GUIDE
    if not guide_path.exists():
        sys.exit(0)

    rel_path = f"{component}/{PROTECTED}" if component else PROTECTED
    rel_guide = guide_path.relative_to(project_root).as_posix()
    print(
        f"Blocked: {rel_path} is generated from {rel_guide} and must not be edited directly.\n"
        f"Edit {rel_guide}, then run /agents-docs-build.\n"
        "/agents-docs-check will flag drift if this file is out of sync.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
