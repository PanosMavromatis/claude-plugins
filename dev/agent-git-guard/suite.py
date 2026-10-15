"""guard-agent-git.py suite: drives the hook as hooks.json runs it, the file itself by its
shebang, with a PreToolUse input on stdin, and grades its exit status, stdout and stderr.
Writes only under $LOCATE_PLAN_WORK, which must lie outside the repository.

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--first] [--hook PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

Every case runs twice under each python3 found, put first on PATH so the shebang finds it, and
must print the same thing each time; stdout must stay empty. --mutants applies each patch in
mutants/ to a copy of the hook and runs the suite on it once, up to its first failure: each
must fail it, and a patch that no longer applies is reported stale. A patch names its file
relative to the plugin's root (hooks/guard-agent-git.py)."""
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
TREE = W + "/gag-tree"   # the input's cwd: a working tree with a docs/ directory and files in it
def blocked(agent, what):
    return (f"Blocked: {agent} may not run `{what}`. This plugin's agents run only git status, diff, log, show, "
            "rev-parse and ls-files, git add of named files, and gh pr list and pr view: commits, pushes, tags "
            "and every other git or gh write are the main session's, made after the user confirms them.\n")

# id, agent_type (None: the main session), command, expectation: 0 (allow), a refused
# "git ..."/"gh ..." (exit 2, named in the message), or a dict for the odd ones.
C = [
 # what this plugin's agents may run
 ("g01", DS, "git status", 0), ("g02", DS, "git diff --cached", 0), ("g03", DS, "git add AGENTS.md docs/x.md", 0),
 ("g04", DS, "git log --oneline -5", 0), ("g05", DS, "git show HEAD", 0), ("g06", DS, "git rev-parse HEAD", 0),
 ("g07", DS, "git ls-files", 0), ("g08", DS, "git --no-pager log", 0), ("g09", DS, "git -C /tmp/x status", 0),
 ("g10", DS, "/x/plugins/workflow-coding/scripts/build-agents-md.sh", 0), ("g11", DS, "find docs -name '*.md'", 0),
 ("g12", DS, "echo 'git commit is the main session'\"'\"'s'", 0), ("g13", DS, "git", 0),
 ("g14", DS, "gh pr list", 0), ("g15", DS, "gh pr view 3", 0), ("g16", DS, "gh -R o/r pr list", 0),
 ("g17", DS, "git status --short && git diff --cached", 0),
 ("g18", DS, "git add -- AGENTS.md", 0), ("g19", DS, "git add ./AGENTS.md docs/x.md", 0),
 ("g20", DS, "git -C docs add x.md", 0),
 # what they may not
 ("r01", DS, "git commit -m x", "git commit"), ("r02", DS, "git push", "git push"),
 ("r03", DS, "git push --follow-tags origin main", "git push"), ("r04", DS, "git tag v1", "git tag"),
 ("r05", DS, "git tag -d v1", "git tag"), ("r06", DS, "git rm x", "git rm"), ("r07", DS, "git branch -d x", "git branch"),
 ("r08", DS, "git branch -D x", "git branch"), ("r09", DS, "git reset --hard", "git reset"), ("r10", DS, "git stash", "git stash"),
 ("r11", DS, "git checkout main", "git checkout"), ("r12", DS, "git -C /tmp commit", "git commit"),
 ("r13", DS, "git -c user.name=x commit", "git commit"), ("r14", DS, "GIT_DIR=. git commit", "git commit"),
 ("r15", DS, "env git commit", "git commit"), ("r16", DS, "env -i git push", "git push"),
 ("r17", DS, "/usr/bin/git commit", "git commit"), ("r18", DS, "git status && git commit -m x", "git commit"),
 ("r19", DS, "git status; git push", "git push"), ("r20", DS, "true | git tag x", "git tag"),
 ("r21", DS, "bash -c 'git commit -m x'", "git commit"), ("r22", DS, "(git commit -m x)", "git commit"),
 ("r23", DS, "gh pr merge 3", "gh pr merge"), ("r24", DS, "gh pr create", "gh pr create"),
 ("r25", DS, "gh repo delete o/r", "gh repo delete"), ("r26", DS, "git fetch", "git fetch"),
 ("r27", DS, "time -p git push", "git push"), ("r28", DS, "git status & git commit", "git commit"),
 ("r29", DS, "git status\ngit push", "git push"),
 # git add that would stage more than named files
 ("r30", DS, "git add .", "git add ."), ("r31", DS, "git add -A", "git add -A"), ("r32", DS, "git add --all", "git add --all"),
 ("r33", DS, "git add -u", "git add -u"), ("r34", DS, "git add docs/", "git add docs/"),
 ("r35", DS, "git add AGENTS.md docs", "git add docs"), ("r36", DS, "git add '*.md'", "git add *.md"),
 ("r37", DS, "git add :/", "git add :/"), ("r38", DS, "git add", "git add"),
 ("r39", DS, "git add -p AGENTS.md", "git add -p"), ("r40", DS, "git -C docs add .", "git add ."),
 ("r41", DS, "git add -- .", "git add ."), ("r42", DS, "git -C docs add sub", "git add sub"),
 ("r43", DS, "git -C nowhere add .", "git add ."),   # `.` refused where no directory can be checked
 # calls the hook leaves alone
 ("o01", None, "git commit -m x", 0), ("o02", None, "git push --follow-tags", 0), ("o03", None, "gh pr merge 3", 0),
 ("o04", "general-purpose", "git commit -m x", 0), ("o05", "other-plugin:agent", "git tag v1", 0),
 ("o06", DS, None, dict(tool="Edit", tool_input={"file_path": "/x/AGENTS.md", "command": "git commit"}, exit=0)),
 ("o07", DS, None, dict(tool_input={}, exit=0)),
 # the seam, which replaces the set guarded
 ("s01", "general-purpose", "git commit -m x", dict(seam="general-purpose", exit=2, err=blocked("general-purpose", "git commit"))),
 ("s02", DS, "git commit -m x", dict(seam="general-purpose", exit=0)),
 ("s03", DS, "git push", dict(seam="someone, workflow-coding:docs-sync", exit=2, err=blocked(DS, "git push"))),
 ("s04", DS, "git commit -m x", dict(seam="", exit=0)),
 # malformed input, and the message in full
 ("e01", None, None, dict(raw="{not json", exit=1, prefix="guard-agent-git: malformed hook input: ")),
 ("m01", DS, "git commit -m x", dict(exit=2, err=blocked(DS, "git commit"))),
]

def run(agent, command, exp, py):
    env = dict(os.environ); env.pop("WORKFLOW_CODING_GUARDED_AGENTS", None)
    env["PATH"] = bindir(py) + ":" + env["PATH"]
    spec = exp if isinstance(exp, dict) else {}
    if "seam" in spec: env["WORKFLOW_CODING_GUARDED_AGENTS"] = spec["seam"]
    if "raw" in spec: stdin = spec["raw"]
    else:
        d = {"session_id": "suite", "hook_event_name": "PreToolUse", "tool_name": spec.get("tool", "Bash"),
             "tool_input": spec.get("tool_input", {"command": command}), "tool_use_id": "t1", "cwd": TREE}
        if agent: d.update(agent_type=agent, agent_id="a1")
        stdin = json.dumps(d)
    return subprocess.run([HOOK], input=stdin, capture_output=True, text=True, env=env, cwd=W)

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
        shutil.copy2(HOOK, root + "/hooks/guard-agent-git.py")
        ap = subprocess.run(["patch", "-s", "-F0", "-p1", "-d", root, "-i", f"{d}/{fn}"], capture_output=True, text=True)
        if ap.returncode:
            bad += 1; print(f"STALE  {name}: the patch no longer applies ({(ap.stdout + ap.stderr).strip()[:120]})"); continue
        os.chmod(root + "/hooks/guard-agent-git.py", os.stat(HOOK).st_mode)
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
    shutil.rmtree(TREE, ignore_errors=True); os.makedirs(TREE + "/docs/sub")   # the hook runs in W, the input says TREE
    for f in ("AGENTS.md", "docs/x.md"): open(f"{TREE}/{f}", "w").write("x\n")
    want = [a for a in sys.argv[1:] if re.match(r"^[groesm]\d\d$", a)]
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
