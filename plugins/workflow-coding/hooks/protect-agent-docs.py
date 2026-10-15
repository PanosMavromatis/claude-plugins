#!/usr/bin/env python3
"""PreToolUse hook: block direct writes to a generated AGENTS.override.md, and hold this
plugin's agents to documentation.

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

This plugin's own agents are also held to documentation: an agent whose agent_type starts with
`workflow-coding:`, or that WORKFLOW_CODING_GUARDED_AGENTS names (the seam guard-agent-git.py
reads). Each path is judged as written and once its symlinks are resolved, in this project or
any other. A write is blocked
  - to git's directory: a hook or config written there runs at the main session's next git
    command, a commit the user confirms included;
  - to anything but a Markdown file: source and config are the user's to change, and
    /smart-commit would commit and push what the agent staged;
  - to CLAUDE.md or CLAUDE.local.md, which every session loads as instructions;
  - under .claude/, except the agent's own memory, .claude/agent-memory/<plugin>-<agent>/:
    Markdown there is a command, an agent, a skill or another agent's memory, each
    instructions a later session runs.
guard-agent-git.py holds the same agents' `git add` to the same paths. A component is read as
a case-insensitive or Windows filesystem reads it, without case, trailing dots or spaces, or
an NTFS stream suffix, so `.GIT`, `.git.` and `.git::$INDEX_ALLOCATION` are `.git`, and a
hidden directory's 8.3 short name, `GIT~1` or `CLAUDE~1`, is the directory, as git's own
is_ntfs_dotgit check reads it.
guard-agent-git.py holds the same agents' Bash. The main session's writes, and other agents',
pass.

Exit codes:
  0 — allow the tool call
  1 — non-blocking error (malformed input)
  2 — block the tool call; stderr is returned to the model
"""
import json
import os
import re
import sys
from pathlib import Path

PROTECTED = "AGENTS.override.md"
GUIDE = Path("codex-review") / "AGENTS.md"
GIT_DIR = ".git"
CLAUDE_DIR = ".claude"
INSTRUCTIONS = ("claude.md", "claude.local.md")   # what every session loads
PREFIX = "workflow-coding:"


def _guarded(agent_type):
    """Whether writes from agent_type are held to documentation: guard-agent-git.py's rule."""
    if not agent_type:
        return False
    named = os.environ.get("WORKFLOW_CODING_GUARDED_AGENTS")
    if named is not None:
        return agent_type in {a.strip() for a in named.split(",") if a.strip()}
    return agent_type.startswith(PREFIX)


def _fs_name(part):
    """A path component as a case-insensitive or Windows filesystem reads it."""
    return part.split(":", 1)[0].lower().rstrip(". ")


def _names_dir(part, name):
    """Whether a path component is the hidden directory name (.git, .claude), its 8.3 short
    name (GIT~1) included."""
    n = _fs_name(part)
    return n == name or re.fullmatch(name[1:] + r"~\d+", n) is not None


def _not_a_doc(parts, agent_type):
    """Why a guarded agent may not write the path whose components are parts, or None."""
    name = _fs_name(parts[-1]) if parts else ""
    if not name.endswith(".md"):
        return "it is not a Markdown file"
    if name in INSTRUCTIONS:
        return f"every session loads {parts[-1]} as instructions"
    own = ["agent-memory", (agent_type or "").lower().replace(":", "-")]
    for i, p in enumerate(parts[:-1]):
        if _names_dir(p, CLAUDE_DIR) and [_fs_name(q) for q in parts[i + 1:i + 3]] != own:
            return "under .claude/ only its own memory is documentation"
    return None


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

    agent_type = payload.get("agent_type")
    if _guarded(agent_type):
        written, resolved = Path(file_path).parts, target.parts
        if any(_names_dir(p, GIT_DIR) for p in written + resolved):
            print(
                f"Blocked: {agent_type} may not write {file_path}: a hook or config under .git/ runs "
                "at the main session's next git command, a commit the user confirms included.\n"
                "This plugin's agents edit documentation, never git's own files.",
                file=sys.stderr,
            )
            sys.exit(2)
        why = _not_a_doc(written, agent_type) or _not_a_doc(resolved, agent_type)
        if why:
            print(
                f"Blocked: {agent_type} may not write {file_path}: {why}.\n"
                "This plugin's agents edit documentation: Markdown, never CLAUDE.md, and under "
                ".claude/ only their own memory.",
                file=sys.stderr,
            )
            sys.exit(2)

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
