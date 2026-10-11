"""open-revision.sh suite: runs the script directly on a fixture repository built here, one
orphan branch per case (the script reads the repository's own master plan), and grades the
exit code and what it prints. Writes only under $LOCATE_PLAN_WORK, which must lie outside the
repository (the rule dev/locate-plan/ uses, for the same reasons).

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--script PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

Every case runs twice under each shell found and must print the same thing each time, and
must leave the fixture untouched. A refusal goes to stderr and prints no proposal; a
proposal goes to stdout and names the line it would insert at. --mutants applies each patch
in mutants/ to a copy of the script and runs the suite on it once; each must fail it. A
patch names its file relative to scripts/."""
import hashlib, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCRIPT = REPO + "/plugins/workflow-claude/scripts/open-revision.sh"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
FX = W + "/orv"
SHELLS = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if os.access(s, os.X_OK)]
if "--once" in sys.argv: SHELLS = SHELLS[:1]
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
AWK127 = f"{W}/bin/{h('orv-awk-127')}"

# Line numbers matter: the cases name them. The closed lines are the forms close-revision.sh
# writes, the second with a subtitle; 02-mcp-github-access is this repository's own, whose
# directory moved under docs/plan/workflow-claude/.
MASTER = """# Master plan

**Status**: active

## Subgoals — revision 07-rev-2

- [ ] a

## Subgoals — revision 08-c: A subtitled heading

- [ ] b

A paragraph that quotes the old form: - **Revision 09-p** — closed.

## Closed revisions

- **Revision 02-mcp-github-access** — closed. See `docs/plan/workflow-claude/02-mcp-github-access/_DO.md`.
- **Revision 04-sub** — plan layout at scale — closed. See `docs/plan/old/04-sub/_TODO.md`.
- **Revision 05-x-2** — closed. See `docs/plan/old/05-x-2/_TODO.md`.
- **Revision 06-here** — closed. See `docs/plan/06-here/_TODO.md`.
"""
M = {"docs/plan/TODO.md": MASTER, "docs/plan/06-here/_TODO.md": "# Revision 06-here\n",
     "docs/plan/07-dir/x/TODO.md": "# x\n"}
CRLF = {"docs/plan/TODO.md": MASTER.replace("\n", "\r\n")}
BSL = {"docs/plan/TODO.md": "# Master plan\n\n## Subgoals — revision a\\tb\n\n- [ ] a\n"}

# id, files on the case's branch, arguments (or a special), expectations
C = [
 ("o01", M, ["02-mcp-github-access"], dict(exit=1, err="refused: revision '02-mcp-github-access' is listed under Closed revisions (docs/plan/TODO.md:17)")),
 ("o02", M, ["04-sub"], dict(exit=1, err="refused: revision '04-sub' is listed under Closed revisions (docs/plan/TODO.md:18)")),
 ("o03", M, ["05-x"], dict(exit=0, insert='line 15, before "## Closed revisions"')),
 ("o04", M, ["07-rev"], dict(exit=0, insert='line 15, before "## Closed revisions"')),
 ("o05", M, ["07-rev-2"], dict(exit=1, err="refused: docs/plan/TODO.md:5 already has a section for revision '07-rev-2'")),
 ("o06", M, ["08-c"], dict(exit=1, err="refused: docs/plan/TODO.md:9 already has a section for revision '08-c'")),
 ("o07", M, ["07-dir"], dict(exit=1, err="refused: docs/plan/07-dir already exists")),
 ("o08", M, ["06-here"], dict(exit=1, err="refused: revision '06-here' is listed under Closed revisions (docs/plan/TODO.md:20)")),
 ("o09", M, ["09-p"], dict(exit=0, insert='line 15, before "## Closed revisions"')),
 ("o10", CRLF, ["07-rev-2"], dict(exit=1, err="refused: docs/plan/TODO.md:5 already has a section for revision '07-rev-2'")),
 ("o11", BSL, ["a\\tb"], dict(exit=1, err="refused: docs/plan/TODO.md:3 already has a section for revision 'a\\tb'")),
 ("o12", {"README.md": "x\n"}, ["01-first"], dict(exit=1, err="refused: no master plan at docs/plan/DO.md or TODO.md")),
 ("o13", {"README.md": "x\n"}, [], dict(exit=2, err="usage:")),
 ("o14", {"README.md": "x\n"}, ["feat/x"], dict(exit=2, err="contain no spaces or slashes")),
 ("o15", M, "awk127", dict(exit=3, err="error: awk failed reading docs/plan/TODO.md")),
]

def sh(args, cwd, env=None): return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
def git(*a, cwd=FX):
    r = sh(["git", *a], cwd)
    if r.returncode: sys.exit(f"git {' '.join(a)} failed: {r.stderr}")
    return r.stdout

def build():
    shutil.rmtree(FX, ignore_errors=True); os.makedirs(FX)
    git("init", "-q", "-b", "main"); git("config", "user.email", "suite@example.invalid"); git("config", "user.name", "suite")
    git("config", "commit.gpgsign", "false")
    open(FX + "/README.md", "w").write("fixture\n"); git("add", "-A"); git("commit", "-q", "-m", "root")
    for cid, files, _, _ in C:
        git("checkout", "-q", "--orphan", f"case/{cid}"); git("rm", "-rq", "--cached", ".")
        for f in os.listdir(FX):
            if f != ".git": os.remove(FX + "/" + f) if os.path.isfile(FX + "/" + f) else shutil.rmtree(FX + "/" + f)
        for rel, text in files.items():
            p = f"{FX}/{rel}"; os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", newline="").write(text)
        git("add", "-A"); git("commit", "-q", "-m", cid)
    git("checkout", "-q", "main")
    os.makedirs(AWK127, exist_ok=True)
    open(AWK127 + "/awk", "w").write("#!/bin/sh\nexit 127\n"); os.chmod(AWK127 + "/awk", 0o755)

def run(cid, args, shell, script):
    env = dict(os.environ); git("checkout", "-q", f"case/{cid}")
    if args == "awk127": env["PATH"] = AWK127 + ":" + env["PATH"]; args = ["01-new"]
    return sh([shell, script, *args], FX, env)

def grade(exp, r):
    probs = []
    if r.returncode != exp["exit"]: probs.append(f"exit {r.returncode}, want {exp['exit']} (stderr: {r.stderr.strip()[:100]!r})")
    if "err" in exp and exp["err"] not in r.stderr: probs.append(f"stderr lacks {exp['err']!r}: {r.stderr.strip()[:140]!r}")
    if exp["exit"]:
        if r.stdout: probs.append(f"a refusal printed a proposal: {r.stdout[:80]!r}")
    else:
        if r.stderr: probs.append(f"a proposal wrote to stderr: {r.stderr.strip()[:100]!r}")
        if f"insert at    : {exp['insert']}" not in r.stdout: probs.append(f"stdout lacks the insert line {exp['insert']!r}: {r.stdout[:200]!r}")
    if W in r.stdout + r.stderr: probs.append("an absolute path in the output")
    return probs

def mutants():
    d = HERE + "/mutants"; tmp = W + "/orv-mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; root = f"{tmp}/{name}"; out = root + "/open-revision.sh"
        os.makedirs(root); shutil.copy2(SCRIPT, out)
        ap = sh(["patch", "-s", "-F0", "-p1", "-d", root, "-i", f"{d}/{fn}"], tmp)
        if ap.returncode:
            bad += 1; print(f"STALE  {name}: the patch no longer applies ({(ap.stdout + ap.stderr).strip()[:120]})"); continue
        r = sh([sys.executable, "-I", os.path.abspath(__file__), "--once", "--script", out], HERE)
        killed = r.returncode != 0
        why = next((l for l in r.stdout.splitlines() if l.startswith("FAIL")), "")
        print(f"{'KILLED' if killed else 'SURVIVED'} {name}" + (f"  ({why[:100]})" if killed else ""))
        bad += not killed
    shutil.rmtree(tmp); print(f"\n{bad} failing"); sys.exit(1 if bad else 0)

def main():
    if "--mutants" in sys.argv: mutants()
    want = [a for a in sys.argv[1:] if re.match(r"^o\d", a)]
    build()
    heads = git("for-each-ref", "--format=%(refname) %(objectname)")
    fails = 0
    for cid, _, args, exp in C:
        if want and cid not in want: continue
        outs, probs = set(), []
        for shell in SHELLS:
            for _ in range(1 if "--once" in sys.argv else 2):
                r = run(cid, args, shell, SCRIPT); outs.add((r.returncode, r.stdout, r.stderr))
                probs += [p for p in grade(exp, r) if p not in probs]
                if git("status", "--porcelain") or git("for-each-ref", "--format=%(refname) %(objectname)") != heads:
                    probs.append("the fixture changed")
        if len(outs) > 1: probs.append("output differs between runs or shells")
        print(f"{'PASS' if not probs else 'FAIL'} {cid:<4} " + "; ".join(probs))
        if "-v" in sys.argv: print("".join(o[1] + o[2] for o in sorted(outs)))
        fails += bool(probs)
    git("checkout", "-q", "main")
    print(f"\n{fails} failing"); sys.exit(1 if fails else 0)

main()
