#!/usr/bin/env python3
"""PreToolUse hook: run the repository's suite before a commit that touches a kernel.

Exit 0 allows the tool call; exit 2 blocks it.

**This script decides for itself whether the command is a `git commit`, rather than
relying on the hook entry's `if` matcher.** The two official plugins that use that field
spell their patterns incompatibly -- `Bash(git commit:*)` against
`Bash(python3 *scripts/*.py *)` -- so at least one of the two syntaxes matches nothing,
and a matcher that matches nothing produces a hook that never fires and says nothing about
it. The plugin whose pattern uses the colon form re-checks the command with its own regex
anyway, which is the precedent followed here. Checking in the script costs one process
spawn per Bash call and cannot fail silently.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

MANIFEST = "dp-compile.toml"


def allow(msg: str | None = None) -> None:
    if msg:
        print(msg)
    sys.exit(0)


def block(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def is_git_commit(command: str) -> bool:
    """True for a command that creates a commit, false for one that merely mentions it.

    Deliberately conservative in one direction only: a compound command containing a
    commit counts, because `uv run x && git commit` still commits.
    """
    for part in re.split(r"&&|\|\||;|\|", command):
        try:
            tokens = shlex.split(part)
        except ValueError:
            tokens = part.split()
        if len(tokens) >= 2 and os.path.basename(tokens[0]) == "git":
            # skip global flags such as -C <path>
            i = 1
            while i < len(tokens) and tokens[i].startswith("-"):
                i += 2 if tokens[i] in ("-C", "-c", "--git-dir", "--work-tree") else 1
            if i < len(tokens) and tokens[i] == "commit":
                return True
    return False


def repo_root() -> str | None:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    return r.stdout.strip() or None


def kernel_paths(cfg: dict) -> set[str]:
    r"""Every path a [phases] template resolves to, for every listed algorithm.

    Expanded against the manifest's `[algorithms]` keys rather than wildcarded. A
    wildcard would over-match badly in a flat layout: `_{algorithm}.py` becomes
    `_[^/]+\.py`, which matches every private module in the package -- helpers and
    parameter objects alongside kernels -- so an ordinary edit to a utility module would
    run the whole suite. Listing algorithms is what the manifest is for, and it is
    exactly the reason discovery-by-glob was rejected for it.

    The `formalization` phase is excluded. It is the specification stage rather than an
    implementation phase -- a Markdown document that compiles to nothing and is imported
    by nothing -- so staging it cannot break a backend, and rebuilding and running the
    whole suite over a prose edit is a cost with no corresponding risk. Staleness is a
    separate mechanism and reports the consequence of that edit on its own.
    """
    phases = {k: v for k, v in (cfg.get("phases") or {}).items()
              if k != "formalization"}
    algorithms = cfg.get("algorithms") or {}
    paths: set[str] = set()
    for name, meta in algorithms.items():
        package = (meta or {}).get("package", "")
        for template in phases.values():
            if not isinstance(template, str):
                continue
            if "{package}" in template and not package:
                # Unresolvable for this algorithm. Err toward running the suite: a
                # gate that misses a kernel edit is worse than one that runs twice.
                paths.add("\0unresolved")
                continue
            paths.add(template.format(algorithm=name, package=package))
    return paths


def main() -> None:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {}

    command = (event.get("tool_input") or {}).get("command", "")
    if command and not is_git_commit(command):
        sys.exit(0)          # not a commit; say nothing at all

    root = repo_root()
    if root is None:
        allow()

    path = os.path.join(root, MANIFEST)
    if not os.path.exists(path):
        allow(f"dp-compile: no {MANIFEST} in this repository — skipping the kernel test gate.")
    if tomllib is None:
        allow("dp-compile: Python 3.11+ is needed to read the manifest — skipping the gate.")

    with open(path, "rb") as fh:
        cfg = tomllib.load(fh)

    staged = subprocess.run(["git", "diff", "--cached", "--name-only"],
                            capture_output=True, text=True, cwd=root).stdout.split()
    kernels = kernel_paths(cfg)
    if "\0unresolved" in kernels:
        touched = staged            # cannot resolve every template; check everything
    else:
        touched = [f for f in staged if f in kernels]
    if not touched:
        sys.exit(0)          # no kernel in this commit; nothing to prove

    commands = cfg.get("commands") or {}
    build, test = commands.get("build"), commands.get("test")
    if not test:
        allow("dp-compile: the manifest defines no [commands].test — skipping the gate.")

    print(f"dp-compile: {len(touched)} kernel file(s) staged; running the suite.")
    for label, cmd in (("build", build), ("test", test)):
        if not cmd:
            continue
        r = subprocess.run(cmd, shell=True, cwd=root)
        if r.returncode != 0:
            block(f"dp-compile: [commands].{label} failed — commit blocked.\n"
                  f"  {cmd}\n"
                  f"  staged kernel files: {', '.join(touched)}")
    print("dp-compile: suite passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
