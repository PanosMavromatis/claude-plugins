#!/usr/bin/env python3
"""SessionStart hook: if commit-commands is still enabled while workflow-claude
is loaded (i.e. this hook ran at all), recommend disabling it. Silent otherwise.

This hook ships inside workflow-claude, so it only runs when workflow-claude is
loaded -- which only happens when the session was launched with
`claude --plugin-dir <path>/workflow-claude`. The hook firing IS the
"--plugin-dir was used" signal; no need to inspect argv.
"""
import json
import os
import sys

PLUGIN = "commit-commands"  # match commit-commands@<any-marketplace>


def load(path):
    try:
        with open(os.path.expanduser(path)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def enabled_in(settings):
    """Return True/False if any commit-commands@* key is set here, else None."""
    result = None
    for key, val in (settings.get("enabledPlugins") or {}).items():
        if key.split("@", 1)[0] == PLUGIN:
            result = bool(val)
    return result


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    cwd = payload.get("cwd") or os.getcwd()

    # Precedence: user < project < project-local. Last defined wins.
    effective = None
    for path in (
        "~/.claude/settings.json",
        os.path.join(cwd, ".claude/settings.json"),
        os.path.join(cwd, ".claude/settings.local.json"),
    ):
        v = enabled_in(load(path))
        if v is not None:
            effective = v

    # Absent everywhere: enabled iff installed (marketplace default = on).
    if effective is None:
        installed = load("~/.claude/plugins/installed_plugins.json").get("plugins", {})
        effective = any(k.split("@", 1)[0] == PLUGIN for k in installed)

    if not effective:
        sys.exit(0)  # already disabled -- say nothing

    # User-facing channel: the top-level "systemMessage" JSON field is shown
    # directly to the user in the terminal (unlike stdout->additionalContext,
    # which only reaches the model, or stderr/exit-2, which this CLI build does
    # not surface). "additionalContext" is added alongside so the model also
    # knows to prefer the /smart-* commands. See the plugin conflict report, §8.
    user_msg = (
        "⚠️  workflow-claude is loaded, but commit-commands is still enabled. "
        "/smart-commit and /smart-merge supersede /commit and /commit-push-pr "
        "(the commit-commands versions skip doc-sync, version tagging, and the "
        "branch-doc PR flow). Disable it for this project by adding "
        '{"enabledPlugins": {"commit-commands@claude-plugins-official": false}} '
        "to ./.claude/settings.json (or toggle it off via /plugin). "
        "This reminder disappears once commit-commands is disabled."
    )
    model_ctx = (
        "commit-commands is enabled alongside workflow-claude. Prefer "
        "/smart-commit and /smart-merge over /commit and /commit-push-pr."
    )
    print(
        json.dumps(
            {
                "systemMessage": user_msg,
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": model_ctx,
                },
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
