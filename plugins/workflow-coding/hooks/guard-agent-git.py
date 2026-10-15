#!/usr/bin/env python3
"""PreToolUse hook on Bash: keep this plugin's agents to the git and gh subcommands they need.

A command's allowed-tools grant reaches every agent it spawns, so under /smart-commit, which
grants git commit, git push and git tag, an agent such as docs-sync could commit, push or tag
with nothing but its instructions to stop it. This hook stops it. For a call whose agent_type
names one of this plugin's agents, `git` may run only status, diff, add, log, show, rev-parse
and ls-files, and `gh` only pr list and pr view; any other git or gh subcommand is refused.
`git add` must name files: an option such as -A or -u, `.`, a glob, a magic pathspec or a
directory would stage the user's unrelated work for /smart-commit to commit and push.

A call from the main session carries no agent_type, and an agent of another plugin's or the
user's is not this plugin's, so both pass untouched, as does everything in Bash that is
neither git nor gh. Commits, pushes and tags stay the main session's, made after the user
confirms them.

The agents guarded are those whose agent_type starts with `workflow-coding:`.
WORKFLOW_CODING_GUARDED_AGENTS, a comma-separated list of agent types, replaces that set: the
headless test uses it to guard a general-purpose stand-in, which, unlike docs-sync, will try
a commit when told to.

Like dp-compile's gate, the hook reads the command itself rather than trusting an `if`
matcher: each part of a chain (&&, ||, ;, |, &, a newline) is checked on its own; leading
VAR=value assignments and the wrappers env, command, exec, nohup and time are skipped; a
`bash -c` or `sh -c` script is checked as a command; and git's global options, `-C <path>`
and `-c <name=value>` among them, are skipped to find the subcommand. It guards against an
agent's mistake, not its evasion: a git call hidden in an alias, a script or `eval` passes.

Exit codes:
  0 — allow the tool call
  1 — non-blocking error (malformed input)
  2 — refuse the tool call; stderr is returned to the model
"""
import json
import os
import re
import shlex
import sys

GIT_OK = ("status", "diff", "add", "log", "show", "rev-parse", "ls-files")
GH_OK = (("pr", "list"), ("pr", "view"))
PREFIX = "workflow-coding:"
GIT_VALUED = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
GH_VALUED = {"-R", "--repo"}
WRAPPERS = {"env", "command", "exec", "nohup", "time"}
SHELLS = {"sh", "bash", "zsh", "dash"}


def guarded(agent_type):
    """Whether calls from agent_type are held to the allowlist."""
    if not agent_type:
        return False
    named = os.environ.get("WORKFLOW_CODING_GUARDED_AGENTS")
    if named is not None:
        return agent_type in {a.strip() for a in named.split(",") if a.strip()}
    return agent_type.startswith(PREFIX)


def words(part):
    """A command part's words, with leading assignments, wrappers and opening parentheses gone."""
    try:
        tokens = shlex.split(part)
    except ValueError:
        tokens = part.split()
    tokens = [t.lstrip("(").rstrip(")") for t in tokens]
    tokens = [t for t in tokens if t]
    while tokens:
        if tokens[0] in WRAPPERS:              # env, time and the rest, and their options
            tokens = tokens[1:]
            while tokens and tokens[0].startswith("-"):
                tokens = tokens[1:]
        elif "=" in tokens[0] and not tokens[0].startswith("-"):   # VAR=value
            tokens = tokens[1:]
        else:
            break
    return tokens


def add_refused(args, base):
    """What makes a `git add` stage more than named files, or None. Every argument must be a
    path naming a file, after an optional `--`: an option (-A, -u, --all, -p ...), no path at
    all, `.`, a glob, a magic pathspec (`:/`) or a directory would stage what the agent did not
    edit, the user's unstaged work among it, for /smart-commit to commit and push."""
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
        if p.rstrip("/") in ("", ".") or any(c in p for c in "*?[") or p.startswith(":") \
                or os.path.isdir(os.path.join(base, p)):
            return p
    return None


def refused(command, cwd):
    """The first disallowed `git ...` or `gh ...` in command, run in cwd, or None."""
    for part in re.split(r"&&|\|\||[;|&\n]", command):
        w = words(part)
        if not w:
            continue
        name = os.path.basename(w[0])
        if name in SHELLS and "-c" in w[1:]:
            i = w.index("-c", 1)
            if i + 1 < len(w):
                inner = refused(w[i + 1], cwd)
                if inner:
                    return inner
            continue
        if name == "git":
            i, base = 1, cwd
            while i < len(w) and w[i].startswith("-"):
                if w[i] == "-C" and i + 1 < len(w):
                    base = os.path.join(base, w[i + 1])
                i += 2 if w[i] in GIT_VALUED else 1
            if i < len(w) and w[i] not in GIT_OK:
                return f"git {w[i]}"
            if i < len(w) and w[i] == "add":
                bad = add_refused(w[i + 1:], base)
                if bad is not None:
                    return f"git add {bad}".rstrip()
        elif name == "gh":
            rest, i = [], 1
            while i < len(w) and len(rest) < 2:
                if w[i].startswith("-"):
                    i += 2 if w[i] in GH_VALUED else 1
                    continue
                rest.append(w[i])
                i += 1
            if rest and tuple(rest) not in GH_OK:
                return "gh " + " ".join(rest)
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"guard-agent-git: malformed hook input: {e}", file=sys.stderr)
        sys.exit(1)
    if payload.get("tool_name") != "Bash" or not guarded(payload.get("agent_type")):
        sys.exit(0)
    found = refused((payload.get("tool_input") or {}).get("command") or "", payload.get("cwd") or os.getcwd())
    if not found:
        sys.exit(0)
    print(
        f"Blocked: {payload.get('agent_type')} may not run `{found}`. This plugin's agents run only "
        "git status, diff, log, show, rev-parse and ls-files, git add of named files, and gh pr "
        "list and pr view: commits, pushes, tags and every other git or gh write are the main "
        "session's, made after the user confirms them.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
