"""guard-agent-git.py suite: drives the hook as hooks.json runs it, its command under /bin/sh,
through fail-closed.sh, with a PreToolUse input on stdin, and grades its exit status, stdout and
stderr. The w cases test the wrapper itself, with python3 or grep failing or a hook crashing,
and hooks.json's command for Write|Edit|MultiEdit. Writes only under $LOCATE_PLAN_WORK, which
must lie outside the repository.

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--first] [--hook PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

Every case runs twice under each python3 found, put first on PATH so the shebang finds it, and
must print the same thing each time; stdout must stay empty. --mutants applies each patch in
mutants/ to a copy of the plugin's hooks/ and runs the suite on it once, up to its first
failure: each must fail it, and a patch that no longer applies is reported stale. A patch names
its file relative to the plugin's root (hooks/guard-agent-git.py, hooks/fail-closed.sh,
hooks/hooks.json)."""
import hashlib, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
HOOK = REPO + "/plugins/workflow-coding/hooks/guard-agent-git.py"
if "--hook" in sys.argv:
    HOOK = os.path.abspath(sys.argv[sys.argv.index("--hook") + 1])
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
PYTHONS = [p for p in ("/usr/bin/python3", "/usr/local/bin/python3", "/opt/homebrew/bin/python3") if os.access(p, os.X_OK)]
if "--once" in sys.argv: PYTHONS = PYTHONS[:1]
def bindir(py): return f"{W}/bin/{hashlib.sha1(('gag-' + py).encode()).hexdigest()[:8]}"

DS = "workflow-coding:docs-sync"
ROOT = os.path.dirname(os.path.dirname(HOOK))   # the plugin's root: hooks/hooks.json and fail-closed.sh beside the hook
HOOKS = ("guard-agent-git.py", "fail-closed.sh", "hooks.json", "protect-agent-docs.py")
TREE = W + "/gag-tree"   # the input's cwd: a working tree with a docs/ directory and files in it
BUILD = ROOT + "/scripts/build-agents-md.sh"   # the plugin's, beside the hook
LINK = W + "/gag-link"   # a symlink to the hook's plugin root, so the same script by another path
CRASH = W + "/gag-crash/crashing-hook.py"   # a hook that fails as a Python traceback does, with exit 1
STUBS = {"nopython": ("python3", "echo 'python3: cannot start' >&2; exit 127"), "nogrep": ("grep", "exit 2")}
NOPY, CRASHED = "python3: cannot start\n", "Traceback (most recent call last): boom\n"
def blocked(agent, what):
    return (f"Blocked: {agent} may not run `{what}`. This plugin's agents run only git status, diff, log, show, "
            "rev-parse and ls-files, git add of the docs they may edit, gh pr list and pr view, and the plugin's "
            "build-agents-md.sh, each alone, with no shell syntax, wrapper or assignment: commits, pushes, tags "
            "and every other git or gh write are the main session's, made after the user confirms them.\n")
def failed(hook, status):
    return (f"Blocked: {hook}, the hook that guards this plugin's agents, failed with exit {status}, so the call "
            "is refused rather than let through unchecked. Check that python3 runs.\n")
WRITE = "Write|Edit|MultiEdit"
def doc(path): return dict(tool="Write", tool_input={"file_path": TREE + "/" + path, "content": "x\n"})

# id, agent_type (None: the main session), command, expectation: 0 (allow), what the message
# names as refused (exit 2), or a dict for the odd ones.
C = [
 # what this plugin's agents may run: docs-sync's own commands first
 ("g01", DS, "git status", 0), ("g02", DS, "git diff --cached", 0), ("g03", DS, "git diff --name-only", 0),
 ("g04", DS, "git status --short", 0), ("g05", DS, "git add AGENTS.md docs/x.md", 0), ("g06", DS, BUILD, 0),
 ("g07", DS, "git add -- AGENTS.md", 0), ("g08", DS, "git add ./AGENTS.md docs/x.md", 0),
 ("g09", DS, "git add 'docs/a b.md'", 0), ("g10", DS, "git log --oneline -5", 0), ("g11", DS, "git show HEAD", 0),
 ("g12", DS, "git rev-parse HEAD", 0), ("g13", DS, "git ls-files -o", 0), ("g14", DS, "git log --format=%h", 0),
 ("g15", DS, "git diff --output-indicator-new=+", 0), ("g16", DS, "git diff --no-ext-diff --no-textconv", 0),
 ("g17", DS, "git diff --text", 0), ("g18", DS, "git log -c", 0),   # -c after the subcommand is a diff format, not config
 ("g19", DS, "gh pr list", 0), ("g20", DS, "gh pr view 3", 0), ("g21", DS, "gh -R o/r pr list", 0),
 ("g22", DS, LINK + "/scripts/build-agents-md.sh", 0), ("g23", DS, "  git status  ", 0), ("g24", DS, "", 0),
 ("g25", DS, os.path.relpath(BUILD, TREE), 0),   # relative to the input's cwd, not the hook's
 ("g26", DS, "git add .claude/agent-memory/workflow-coding-docs-sync/MEMORY.md", 0),   # its own memory
 ("g27", DS, "git add README.MD", 0), ("g28", DS, "git add .claude/../docs/x.md", 0),   # git stages docs/x.md
 # git and gh subcommands not on the list
 ("r01", DS, "git commit -m x", "git commit"), ("r02", DS, "git push", "git push"),
 ("r03", DS, "git push --follow-tags origin main", "git push"), ("r04", DS, "git tag v1", "git tag"),
 ("r05", DS, "git rm x", "git rm"), ("r06", DS, "git branch -d x", "git branch"), ("r07", DS, "git reset --hard", "git reset"),
 ("r08", DS, "git stash", "git stash"), ("r09", DS, "git checkout main", "git checkout"), ("r10", DS, "git fetch", "git fetch"),
 ("r11", DS, "git", "git"), ("r12", DS, "gh pr merge 3", "gh pr merge"), ("r13", DS, "gh pr create", "gh pr create"),
 ("r14", DS, "gh repo delete o/r", "gh repo delete"), ("r15", DS, "gh api /user", "gh api /user"),
 ("r16", DS, "'git' commit", "git commit"), ("r17", DS, '"git" "push"', "git push"),
 # global options, every one: config is code, and -C, --git-dir and --work-tree move what git add stages
 ("r18", DS, "git -c core.fsmonitor=x status", "git -c"), ("r19", DS, "git --config-env=core.pager=X log", "git --config-env=core.pager=X"),
 ("r20", DS, "git --exec-path=/tmp status", "git --exec-path=/tmp"), ("r21", DS, "git -C docs add x.md", "git -C"),
 ("r22", DS, "git --work-tree docs add sub", "git --work-tree"), ("r23", DS, "git --git-dir=/tmp/x status", "git --git-dir=/tmp/x"),
 ("r24", DS, "git -p log", "git -p"), ("r25", DS, "git --no-pager log", "git --no-pager"),
 # options with which an allowed subcommand writes a file or runs a program
 ("r26", DS, "git diff --output=/tmp/x", "git diff --output=/tmp/x"), ("r27", DS, "git log --output /tmp/x", "git log --output"),
 ("r28", DS, "git show --output=x HEAD", "git show --output=x"), ("r29", DS, "git diff --ext-diff", "git diff --ext-diff"),
 ("r30", DS, "git log -p --textconv", "git log --textconv"),
 # git add that would stage more than named files
 ("r31", DS, "git add .", "git add ."), ("r32", DS, "git add -A", "git add -A"), ("r33", DS, "git add --all", "git add --all"),
 ("r34", DS, "git add -u", "git add -u"), ("r35", DS, "git add docs/", "git add docs/"),
 ("r36", DS, "git add AGENTS.md docs", "git add docs"), ("r37", DS, "git add :/", "git add :/"), ("r38", DS, "git add", "git add"),
 ("r39", DS, "git add -p AGENTS.md", "git add -p"), ("r40", DS, "git add -- .", "git add ."),
 ("r41", DS, "git add docs/sub", "git add docs/sub"), ("r42", DS, "git add ./", "git add ./"),
 # shell syntax, each character where it comes first
 ("r43", DS, "git status && git commit -m x", "&"), ("r44", DS, "git status; git push", ";"),
 ("r45", DS, "true | git tag x", "|"), ("r46", DS, "git status\ngit push", "\n"), ("r47", DS, "echo $(git push)", "$"),
 ("r48", DS, "echo `git commit -m x`", "`"), ("r49", DS, "(git commit -m x)", "("), ("r50", DS, "git status)", ")"),
 ("r51", DS, "{ git commit -m x; }", "{"), ("r52", DS, "git status }", "}"), ("r53", DS, "! git commit -m x", "!"),
 ("r54", DS, "git log > .git/hooks/pre-commit", ">"), ("r55", DS, "bash <<< 'git commit -m x'", "<"),
 ("r56", DS, "gi\\t commit", "\\"), ("r57", DS, "git add '*.md'", "*"), ("r58", DS, "git add docs/x.m?", "?"),
 ("r59", DS, "git add 'app/[id]/AGENTS.md'", "["), ("r60", DS, "if true; then git push; fi", ";"),
 ("r61", DS, "G=git; $G commit -m x", ";"), ("r62", DS, "git status & git commit", "&"),
 # anything before the first word, and every other first word
 ("r63", DS, "timeout 5 git push", "timeout"), ("r64", DS, "nice git push", "nice"), ("r65", DS, "sudo git push", "sudo"),
 ("r66", DS, "env -u FOO git commit -m x", "env"), ("r67", DS, "env -S 'git commit -m x'", "env"),
 ("r68", DS, "exec -a x git commit -m x", "exec"), ("r69", DS, "/usr/bin/env git commit -m x", "/usr/bin/env"),
 ("r70", DS, "/usr/bin/git status", "/usr/bin/git"), ("r71", DS, "GIT status", "GIT"),
 ("r72", DS, "GIT_DIR=. git status", "GIT_DIR=."), ("r73", DS, "PAGER=x git log", "PAGER=x"),
 ("r74", DS, "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.pager GIT_CONFIG_VALUE_0=x git log", "GIT_CONFIG_COUNT=1"),
 ("r75", DS, "bash -c 'git commit -m x'", "bash"), ("r76", DS, "bash -lc 'git status'", "bash"),
 ("r77", DS, "xargs git commit", "xargs"), ("r78", DS, "eval git commit", "eval"), ("r79", DS, "find docs -name x.md", "find"),
 ("r80", DS, "cat docs/x.md", "cat"), ("r81", DS, "python3 -c 'import os'", "python3"),
 ("r82", DS, "/x/plugins/workflow-coding/scripts/build-agents-md.sh", "/x/plugins/workflow-coding/scripts/build-agents-md.sh"),
 ("r83", DS, BUILD + " x", BUILD + " x"), ("r84", DS, "git add 'AGENTS.md", "git add 'AGENTS.md"),
 ("r85", DS, "/opt/homebrew/bin/gh pr merge 3", "/opt/homebrew/bin/gh"),
 # paths that are directories once git or the shell has read them: each staged the user's work
 ("r86", DS, "git add ~+", "~"), ("r87", DS, "git add AGENTS.md/..", "git add AGENTS.md/.."),
 ("r88", DS, "git add nowhere/..", "git add nowhere/.."), ("r89", DS, "git add docs/x.md/..", "git add docs/x.md/.."),
 # files the agents may not write, so may not stage: protect-agent-docs.py's rule
 ("r90", DS, "git add src/app.py", "git add src/app.py"), ("r91", DS, "git add CLAUDE.md", "git add CLAUDE.md"),
 ("r92", DS, "git add .claude/commands/x.md", "git add .claude/commands/x.md"),
 ("r93", DS, "git add .claude/agent-memory/other-agent/MEMORY.md", "git add .claude/agent-memory/other-agent/MEMORY.md"),
 ("r94", DS, "git add docs/claude.md", "git add docs/claude.md"), ("r95", DS, "git add CLAUDE.local.md", "git add CLAUDE.local.md"),
 ("r96", DS, "git add AGENTS.md src/app.py", "git add src/app.py"),
 ("r97", DS, "git add CLAUDE~1/commands/x.md", "~"),   # the 8.3 name never reaches the rule: ~ is shell syntax
 ("r98", DS, "git add .claude./commands/x.md", "git add .claude./commands/x.md"),   # as Windows reads them
 ("r99", DS, "git add src/app.py:x.md", "git add src/app.py:x.md"),
 # what only the older checks catch, the paths being Markdown
 ("r100", DS, "git add :!docs/x.md", "git add :!docs/x.md"),   # an exclusion alone stages everything else
 ("r101", DS, "git add docs/dir.md", "git add docs/dir.md"),   # a directory, whatever its name
 ("r102", DS, "git add docs/dir.md/nowhere/..", "git add docs/dir.md/nowhere/.."),
 # calls the hook leaves alone
 ("o01", None, "git commit -m x", 0), ("o02", None, "git push --follow-tags", 0), ("o03", None, "gh pr merge 3", 0),
 ("o04", None, "ls docs && cat docs/x.md | wc -l", 0), ("o05", "general-purpose", "git commit -m x", 0),
 ("o06", "other-plugin:agent", "git tag v1", 0),
 ("o07", DS, None, dict(tool="Edit", tool_input={"file_path": "/x/AGENTS.md", "command": "git commit"}, exit=0)),
 ("o08", DS, None, dict(tool_input={}, exit=0)),
 # the seam, which replaces the set guarded
 ("s01", "general-purpose", "git commit -m x", dict(seam="general-purpose", exit=2, err=blocked("general-purpose", "git commit"))),
 ("s02", DS, "git commit -m x", dict(seam="general-purpose", exit=0)),
 ("s03", DS, "git push", dict(seam="someone, workflow-coding:docs-sync", exit=2, err=blocked(DS, "git push"))),
 ("s04", DS, "git commit -m x", dict(seam="", exit=0)),
 ("s05", "general-purpose", "git add .claude/agent-memory/general-purpose/MEMORY.md", dict(seam="general-purpose", exit=0)),
 # malformed input, and the message in full
 ("e01", None, None, dict(raw="{not json", exit=1, prefix="guard-agent-git: malformed hook input: ")),
 ("e02", None, None, dict(raw="[1, 2]", exit=1, prefix="guard-agent-git: malformed hook input: ")),
 ("m01", DS, "git commit -m x", dict(exit=2, err=blocked(DS, "git commit"))),
 # fail-closed.sh: a hook that cannot run refuses this plugin's agents, and only them
 ("w01", DS, "git status", dict(path="nopython", exit=2, err=NOPY + failed("guard-agent-git.py", 127))),
 ("w02", None, "git commit -m x", dict(path="nopython", exit=127, err=NOPY)),
 ("w03", "general-purpose", "git status", dict(path="nopython", exit=127, err=NOPY)),
 ("w04", "general-purpose", "git status", dict(path="nopython", seam="someone", exit=2, err=NOPY + failed("guard-agent-git.py", 127))),
 ("w05", DS, "git status", dict(via="crash", exit=2, err=CRASHED + failed("crashing-hook.py", 1))),
 ("w06", DS, "git status", dict(via="crash", compact=True, exit=2, err=CRASHED + failed("crashing-hook.py", 1))),
 ("w07", None, "git status", dict(via="crash", exit=1, err=CRASHED)),
 ("w08", None, "git status", dict(via="crash", path="nogrep", exit=2, err=CRASHED + failed("crashing-hook.py", 1))),
 ("w09", None, 'echo "agent_type": "workflow-coding:x"', dict(via="crash", exit=1, err=CRASHED)),   # text, not the key
 ("w10", DS, None, dict(doc("AGENTS.md"), via=WRITE, path="nopython", exit=2, err=NOPY + failed("protect-agent-docs.py", 127))),
 ("w11", DS, None, dict(doc(".git/config"), via=WRITE, exit=2, prefix=f"Blocked: {DS} may not write {TREE}/.git/config: ")),
 ("w12", None, None, dict(doc("AGENTS.md"), via=WRITE, exit=0)),
]

def hook_command(matcher):
    """hooks.json's command for the PreToolUse matcher, as Claude Code runs it."""
    entries = json.load(open(ROOT + "/hooks/hooks.json"))["hooks"]["PreToolUse"]
    return next(e["hooks"][0]["command"] for e in entries if e["matcher"] == matcher)

def run(agent, cmd, exp, py):
    env = dict(os.environ); env.pop("WORKFLOW_CODING_GUARDED_AGENTS", None)
    spec = exp if isinstance(exp, dict) else {}
    env["PATH"] = (f"{W}/bin/gag-{spec['path']}:" if "path" in spec else "") + bindir(py) + ":" + env["PATH"]
    env["CLAUDE_PLUGIN_ROOT"] = ROOT
    if "seam" in spec: env["WORKFLOW_CODING_GUARDED_AGENTS"] = spec["seam"]
    if "raw" in spec: stdin = spec["raw"]
    else:
        d = {"session_id": "suite", "hook_event_name": "PreToolUse", "tool_name": spec.get("tool", "Bash"),
             "tool_input": spec.get("tool_input", {"command": cmd}), "tool_use_id": "t1", "cwd": TREE}
        if agent: d.update(agent_type=agent, agent_id="a1")
        stdin = json.dumps(d, separators=(",", ":") if spec.get("compact") else None)
    via = spec.get("via", "Bash")
    argv = [ROOT + "/hooks/fail-closed.sh", CRASH] if via == "crash" else ["/bin/sh", "-c", hook_command(via)]
    return subprocess.run(argv, input=stdin, capture_output=True, text=True, env=env, cwd=W)

def grade(exp, r):
    if isinstance(exp, dict):
        want_exit, want_err, prefix = exp["exit"], exp.get("err", ""), exp.get("prefix")
    elif exp == 0:
        want_exit, want_err, prefix = 0, "", None
    else:
        want_exit, want_err, prefix = 2, None, None
    probs = []
    if r.returncode != want_exit: probs.append(f"exit {r.returncode}, want {want_exit} (stderr {r.stderr.strip()[:90]!r})")
    if r.stdout: probs.append(f"stdout {r.stdout[:80]!r}")
    if prefix is not None:
        if not r.stderr.startswith(prefix): probs.append(f"stderr {r.stderr[:80]!r}")
    elif want_err is not None:
        if r.stderr != want_err: probs.append(f"stderr {r.stderr[:110]!r}")
    elif f"may not run `{exp}`." not in r.stderr:
        probs.append(f"stderr does not name `{exp}`: {r.stderr[:110]!r}")
    return probs

def mutants():
    d = HERE + "/mutants"; tmp = W + "/gag-mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; root = f"{tmp}/{name}"; os.makedirs(root + "/hooks")
        for h in HOOKS: shutil.copy2(f"{ROOT}/hooks/{h}", f"{root}/hooks/{h}")
        ap = subprocess.run(["patch", "-s", "-F0", "-p1", "-d", root, "-i", f"{d}/{fn}"], capture_output=True, text=True)
        if ap.returncode:
            bad += 1; print(f"STALE  {name}: the patch no longer applies ({(ap.stdout + ap.stderr).strip()[:120]})"); continue
        for h in HOOKS: os.chmod(f"{root}/hooks/{h}", os.stat(f"{ROOT}/hooks/{h}").st_mode)   # patch may rewrite the file
        r = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "--once", "--first", "--hook",
                            root + "/hooks/guard-agent-git.py"], capture_output=True, text=True, cwd=HERE)
        killed = r.returncode != 0
        why = next((l for l in r.stdout.splitlines() if l.startswith("FAIL")), "")
        print(f"{'KILLED' if killed else 'SURVIVED'} {name}" + (f"  ({why[:100]})" if killed else ""))
        bad += not killed
    shutil.rmtree(tmp); print(f"\n{bad} failing"); sys.exit(1 if bad else 0)

def main():
    if "--mutants" in sys.argv: mutants()
    for py in PYTHONS:
        d = bindir(py); shutil.rmtree(d, ignore_errors=True); os.makedirs(d); os.symlink(py, d + "/python3")
    for stub, (prog, body) in STUBS.items():   # first on PATH: a python3 that cannot start, a grep that fails
        d = f"{W}/bin/gag-{stub}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        open(f"{d}/{prog}", "w").write(f"#!/bin/sh\n{body}\n"); os.chmod(f"{d}/{prog}", 0o755)
    os.makedirs(os.path.dirname(CRASH), exist_ok=True)
    open(CRASH, "w").write(f"#!/bin/sh\nprintf '{CRASHED}' >&2\nexit 1\n"); os.chmod(CRASH, 0o755)
    shutil.rmtree(TREE, ignore_errors=True); os.makedirs(TREE + "/docs/sub")   # the hook runs in W, the input says TREE
    os.makedirs(TREE + "/docs/dir.md")
    for f in ("AGENTS.md", "docs/x.md"): open(f"{TREE}/{f}", "w").write("x\n")
    if os.path.lexists(LINK): os.remove(LINK)
    os.symlink(os.path.dirname(os.path.dirname(HOOK)), LINK)
    want = [a for a in sys.argv[1:] if re.match(r"^[groesmw]\d\d\d?$", a)]
    if os.path.isdir(W + "/docs"): sys.exit(f"{W}/docs exists, so a hook judging directories by its own cwd could pass")
    fails = 0
    for cid, agent, command, exp in C:
        if want and cid not in want: continue
        outs, probs = set(), []
        for py in PYTHONS:
            for _ in range(1 if "--once" in sys.argv else 2):
                r = run(agent, command, exp, py); outs.add((r.returncode, r.stdout, r.stderr))
                probs += [p for p in grade(exp, r) if p not in probs]
        if len(outs) > 1: probs.append("output differs between runs or Pythons")
        print(f"{'PASS' if not probs else 'FAIL'} {cid:<4} " + "; ".join(probs))
        if "-v" in sys.argv: print("".join(o[2] for o in sorted(outs)))
        fails += bool(probs)
        if probs and "--first" in sys.argv: break
    print(f"\n{fails} failing"); sys.exit(1 if fails else 0)

main()
