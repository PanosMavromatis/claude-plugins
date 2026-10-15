#!/usr/bin/env python3
"""PreToolUse hook on Bash: hold this plugin's agents to the few commands they need.

A command's allowed-tools grant reaches every agent it spawns, so under /smart-commit, which
grants git commit, git push and git tag, an agent such as docs-sync could commit, push or tag
with nothing but its instructions to stop it. This hook stops it. A call whose agent_type
names one of this plugin's agents may run one simple command, and only one of these:

  git status, diff, log, show, rev-parse or ls-files, with no global option (-c, -C,
    --git-dir, --work-tree and the rest) and none of --output, --ext-diff or --textconv,
    with which an allowed subcommand writes any file or runs a configured program;
  git add of named files: an option such as -A or -u, `.`, a magic pathspec or a directory
    would stage the user's unrelated work for /smart-commit to commit and push; and only of
    files the agents may write, by protect-agent-docs.py's rule: Markdown, never CLAUDE.md or
    CLAUDE.local.md, and under .claude/ only the agent's own memory;
  gh pr list or gh pr view;
  this plugin's scripts/build-agents-md.sh, with no arguments.

Every other Bash call from those agents is refused. A simple command has none of
; & | < > ( ) { } $ ` \\ * ? [ ~ or a newline, and nothing before its first word: no
assignment, wrapper or path. This is an allowlist, not a parser. An earlier version parsed
each command to find the git in it, and two security reviews and a validator then found 28
ways bash runs git that the parse missed (wrappers and their options, shell keywords,
environment variables that set config, `GIT` on a case-insensitive filesystem), each fix
leaving the next. A shape the hook does not know is refused rather than judged, which also
keeps a script the agent writes from running. protect-agent-docs.py holds the same agents'
Write and Edit to documentation, and out of .git/, where a hook or config would run at the
main session's next git command. What the user's own shell or git config makes of `git` is
out of its reach.

A call from the main session carries no agent_type, and an agent of another plugin's or the
user's is not this plugin's, so both pass untouched. Commits, pushes and tags stay the main
session's, made after the user confirms them.

The agents guarded are those whose agent_type starts with `workflow-coding:`.
WORKFLOW_CODING_GUARDED_AGENTS, a comma-separated list of agent types, replaces that set: the
headless test uses it to guard a general-purpose stand-in, which, unlike docs-sync, will try
a commit when told to.

Exit codes:
  0 — allow the tool call
  1 — non-blocking error (malformed input)
  2 — refuse the tool call; stderr is returned to the model
"""
import json
import os
import shlex
import sys
from pathlib import PurePath

GIT_OK = ("status", "diff", "add", "log", "show", "rev-parse", "ls-files")
GIT_UNSAFE = ("--output", "--ext-diff", "--textconv")   # write any file, or run a configured program
GH_OK = (("pr", "list"), ("pr", "view"))
GH_VALUED = {"-R", "--repo"}
PREFIX = "workflow-coding:"
CLAUDE_DIR = ".claude"
INSTRUCTIONS = ("claude.md", "claude.local.md")   # what every session loads
SHELL = set(";&|<>(){}$`\\*?[~\n")   # chains, substitution, redirection, escapes, globs and ~+, which is $PWD
BUILD = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "scripts", "build-agents-md.sh")


def guarded(agent_type):
    """Whether calls from agent_type are held to the allowlist."""
    if not agent_type:
        return False
    named = os.environ.get("WORKFLOW_CODING_GUARDED_AGENTS")
    if named is not None:
        return agent_type in {a.strip() for a in named.split(",") if a.strip()}
    return agent_type.startswith(PREFIX)


def fs_name(part):
    """A path component as a case-insensitive or Windows filesystem reads it."""
    return part.split(":", 1)[0].lower().rstrip(". ")


def not_a_doc(parts, agent_type):
    """Why a guarded agent may not write or stage the path whose components are parts, or
    None: protect-agent-docs.py's rule, which says why. Its 8.3 names (CLAUDE~1) need no
    check here: `~` is shell syntax, refused before a path is read."""
    name = fs_name(parts[-1]) if parts else ""
    if not name.endswith(".md"):
        return "it is not a Markdown file"
    if name in INSTRUCTIONS:
        return f"every session loads {parts[-1]} as instructions"
    own = ["agent-memory", (agent_type or "").lower().replace(":", "-")]
    for i, p in enumerate(parts[:-1]):
        if fs_name(p) == CLAUDE_DIR and [fs_name(q) for q in parts[i + 1:i + 3]] != own:
            return "under .claude/ only its own memory is documentation"
    return None


def add_refused(args, base, agent_type):
    """What makes a `git add` stage more than named files, or None. Every argument must be a
    path naming a file, after an optional `--`: an option (-A, -u, --all, -p ...), no path at
    all, a magic pathspec (`:/`) or a directory would stage what the agent did not edit, the
    user's unstaged work among it, for /smart-commit to commit and push. Git reads `..` as
    text, so `AGENTS.md/..` is `.` even though AGENTS.md is a file: a path is normalised the
    same way before it is checked, and must then be a file the agent may write."""
    paths, rest = [], False
    for a in args:
        if not rest and a == "--":
            rest = True
        elif not rest and a.startswith("-"):
            return a
        else:
            paths.append(a)
    if not paths:
        return ""
    for p in paths:
        if p.startswith(":") or os.path.isdir(os.path.join(base, os.path.normpath(p))):
            return p
        if not_a_doc(PurePath(os.path.normpath(p)).parts, agent_type):
            return p
    return None


def git_refused(w, cwd, agent_type):
    """What the agents may not run in the git command w, run in cwd, or None."""
    sub = w[1] if len(w) > 1 else ""
    if sub not in GIT_OK:   # no subcommand, a global option, or a subcommand not on the list
        return " ".join(w[:2])
    unsafe = next((a for a in w[2:] if a.split("=", 1)[0] in GIT_UNSAFE), None)
    if unsafe:
        return f"git {sub} {unsafe}"
    if sub == "add":
        bad = add_refused(w[2:], cwd, agent_type)
        if bad is not None:
            return f"git add {bad}".rstrip()
    return None


def gh_refused(w):
    """What the agents may not run in the gh command w, or None."""
    rest, i = [], 1
    while i < len(w) and len(rest) < 2:
        if w[i].startswith("-"):
            i += 2 if w[i] in GH_VALUED else 1
            continue
        rest.append(w[i])
        i += 1
    return None if tuple(rest) in GH_OK else " ".join(["gh"] + rest)


def refused(command, cwd, agent_type):
    """What the agent may not run in command, run in cwd, or None."""
    syntax = next((c for c in command if c in SHELL), None)
    if syntax:
        return syntax
    try:
        w = shlex.split(command)
    except ValueError:   # an unbalanced quote
        return command
    if not w:
        return None
    if w[0] == "git":
        return git_refused(w, cwd, agent_type)
    if w[0] == "gh":
        return gh_refused(w)
    if os.path.realpath(os.path.join(cwd, w[0])) == BUILD:
        return None if len(w) == 1 else " ".join(w)
    return w[0]


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("not a JSON object")
    except ValueError as e:   # json.JSONDecodeError is one
        print(f"guard-agent-git: malformed hook input: {e}", file=sys.stderr)
        sys.exit(1)
    if payload.get("tool_name") != "Bash" or not guarded(payload.get("agent_type")):
        sys.exit(0)
    found = refused((payload.get("tool_input") or {}).get("command") or "", payload.get("cwd") or os.getcwd(),
                    payload.get("agent_type"))
    if not found:
        sys.exit(0)
    print(
        f"Blocked: {payload.get('agent_type')} may not run `{found}`. This plugin's agents run only "
        "git status, diff, log, show, rev-parse and ls-files, git add of the docs they may edit, "
        "gh pr list and pr view, and the plugin's build-agents-md.sh, each alone, with no shell syntax, "
        "wrapper or assignment: commits, pushes, tags and every other git or gh write are the "
        "main session's, made after the user confirms them.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
