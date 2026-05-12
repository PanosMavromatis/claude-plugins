#!/usr/bin/env python3
"""PreToolUse hook: block direct writes to generated/dispatcher agent docs.

Projects following the docs/agents/ convention maintain CLAUDE.md as an
@import dispatcher and AGENTS.md / AGENTS.override.md as artifacts built
from docs/agents/ sources by /agents-docs-build. Direct edits to any of
these files would either be overwritten by the next build (and caught by
/agents-docs-check) or bypass the source-of-truth structure entirely.

In a monorepo layout, the same protection extends per-component: for every
docs/agents/<component>/ subdirectory (any nesting depth), the matching
<component>/CLAUDE.md, <component>/AGENTS.md, and <component>/AGENTS.override.md
are protected on the same basis. The hook resolves <component> from the
target file's parent directory relative to the project root.

Each protected basename has a *sentinel* — a file whose presence within the
component's docs/agents/<component>/ directory signals that the convention
is in use for that target. When the sentinel is absent, the write is
allowed through. This avoids two failure modes:

  1. /init on a fresh project would otherwise be blocked from creating
     CLAUDE.md, since this hook fires globally on every Write/Edit/MultiEdit.
  2. Projects that use AGENTS.md without the docs/agents/ build-script
     pattern (e.g., a plain OpenAI Codex setup) would otherwise be blocked
     from editing their own AGENTS.md.

Sentinel basenames (looked up under docs/agents/<component>/, where
<component> is the parent dir of the target file relative to the project
root, or empty for root-level files):

  CLAUDE.md           → docs/agents/<component>/core.md
  AGENTS.md           → docs/agents/<component>/core.md
  AGENTS.override.md  → docs/agents/<component>/codex.md

When the sentinel exists, the write is blocked. When it does not, the
write passes through. CLAUDE.md additionally allows Edit/MultiEdit calls
that mutate only HTML-comment-internal bytes (housekeeping edits to the
dispatcher header).

Migration note: /agents-docs-init's final step replaces a substantive
CLAUDE.md with the dispatcher *after* writing docs/agents/<component>/core.md.
At that moment the sentinel exists, so a Write/Edit on the dispatcher would
be blocked. The migration performs that final replacement via a Bash
heredoc instead; the hook only matches Write|Edit|MultiEdit, so Bash
redirects pass through.

Exit codes:
  0 — allow the tool call
  1 — non-blocking error (malformed input, etc.)
  2 — block the tool call; stderr is returned to the model
"""
import json
import os
import sys
from pathlib import Path

# Each protected basename has:
# - sentinel_basename: the file (within docs/agents/<component>/) whose
#   existence activates protection for this target. When absent, the write
#   is allowed.
# - message_template: format string shown to the model when a write is
#   blocked. Substituted variables: {path} (target's project-relative path),
#   {scope} ("project" for root, 'component "<path>"' for a component),
#   {core_path}, {claude_path}, {codex_path} (project-relative paths to the
#   component's source files).
# - allow_comment_edits: if True, Edit/MultiEdit calls that mutate only
#   HTML-comment-internal bytes are allowed through.
PROTECTED = {
    "CLAUDE.md": {
        "sentinel_basename": "core.md",
        "message_template": (
            "{path} is an @import dispatcher and must not be edited directly.\n"
            "Edits to shared {scope} knowledge go in {core_path}.\n"
            "Edits to Claude-Code-specific content go in {claude_path}.\n"
            "After editing, the @imports in {path} pick up changes automatically."
        ),
        "allow_comment_edits": True,
    },
    "AGENTS.md": {
        "sentinel_basename": "core.md",
        "message_template": (
            "{path} is a generated artifact and must not be edited directly.\n"
            "Edit {core_path}, then run /agents-docs-build.\n"
            "/agents-docs-check will flag drift if this file is out of sync."
        ),
    },
    "AGENTS.override.md": {
        "sentinel_basename": "codex.md",
        "message_template": (
            "{path} is a generated artifact and must not be edited directly.\n"
            "Edit {codex_path}, then run /agents-docs-build.\n"
            "/agents-docs-check will flag drift if this file is out of sync."
        ),
    },
}


def _is_comment_internal_edit(file_path: Path, old: str, new: str) -> bool:
    """Return True iff replacing `old` with `new` in `file_path` only mutates
    bytes inside a single HTML comment block, with no change to the comment
    delimiters themselves."""
    if not old:
        return False
    try:
        content = file_path.read_text()
    except OSError:
        return False
    idx = content.find(old)
    if idx == -1 or content.find(old, idx + 1) != -1:
        # Edit's uniqueness rule means a non-unique match would error anyway;
        # treat as not-allowed so the standard tooling produces the error.
        return False
    end = idx + len(old)
    open_idx = content.rfind("<!--", 0, idx)
    if open_idx == -1:
        return False
    if content.find("-->", open_idx + 4, idx) != -1:
        return False
    if content.find("-->", end) == -1:
        return False
    if "<!--" in new or "-->" in new:
        return False
    return True


def _all_edits_comment_internal(file_path: Path, tool_name: str, tool_input: dict) -> bool:
    if tool_name == "Edit":
        return _is_comment_internal_edit(
            file_path,
            tool_input.get("old_string", ""),
            tool_input.get("new_string", ""),
        )
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        if not edits:
            return False
        return all(
            _is_comment_internal_edit(
                file_path, e.get("old_string", ""), e.get("new_string", "")
            )
            for e in edits
        )
    return False


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

    rule = PROTECTED.get(target.name)
    if rule is None:
        sys.exit(0)

    component = _component_path(target, project_root)
    if component is None:
        # Target lives outside the project root; not our business.
        sys.exit(0)

    docs_agents_root = project_root / "docs" / "agents"
    component_docs_dir = docs_agents_root / component if component else docs_agents_root
    sentinel_path = component_docs_dir / rule["sentinel_basename"]
    if not sentinel_path.exists():
        sys.exit(0)

    if rule.get("allow_comment_edits") and _all_edits_comment_internal(
        target, tool_name, payload.get("tool_input", {})
    ):
        sys.exit(0)

    rel_path = f"{component}/{target.name}" if component else target.name
    rel_core = (component_docs_dir / "core.md").relative_to(project_root).as_posix()
    rel_claude = (component_docs_dir / "claude.md").relative_to(project_root).as_posix()
    rel_codex = (component_docs_dir / "codex.md").relative_to(project_root).as_posix()
    scope = f'component "{component}"' if component else "project"

    message = rule["message_template"].format(
        path=rel_path,
        scope=scope,
        core_path=rel_core,
        claude_path=rel_claude,
        codex_path=rel_codex,
    )
    print(f"Blocked: {message}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
