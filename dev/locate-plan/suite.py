"""locate-plan.sh suite: runs the script directly (no claude -p) on the fx fixture (built by
build-fixtures.sh) and on the fx-diag fixture (built here on first use), and grades every
report. Writes only under $LOCATE_PLAN_WORK, which must lie outside the repository.

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--script PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

By default every case runs twice under each shell found, and must print the same thing each
time. --once runs each case once, under the first shell. --mutants applies each patch in
mutants/ to a copy of the script and runs the suite on it once: every mutant must fail it,
except the known equivalent ones, and a patch that no longer applies is reported stale."""
import hashlib, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCRIPT = REPO + "/plugins/workflow-claude/scripts/locate-plan.sh"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
P = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(P, exist_ok=True); P = os.path.realpath(P)
if (P + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {P} is inside the repository")
FX, FD, NOGIT = P + "/fx", P + "/fx-diag", P + "/nogit"
SHELLS = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if os.access(s, os.X_OK)]
SKIPPED = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if s not in SHELLS]
if "--once" in sys.argv: SHELLS = SHELLS[:1]
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]   # as build-fixtures.sh
# mutants that no input can tell from the script: n05 drops `|| exit 3` after rung 4's
# status read, but rung4 runs at top level, so `set -e` exits there with the same status
EQUIVALENT = {"n05-status-unchecked-rung4"}
KEYS = ["result", "rung", "plan", "kind", "layout", "status", "lines", "next", "goal-file",
        "subgoals", "blocked", "candidates", "warnings", "problem", "fix", "message"]
MASTER = "docs/plan/TODO.md"

def sh(args, cwd, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)

def git(*a, cwd=FD):
    r = sh(["git", *a], cwd)
    if r.returncode: raise SystemExit(f"git {' '.join(a)} failed: {r.stderr}")
    return r.stdout

# --- the diagnostics fixture ---------------------------------------------------------------

def plan(status, *items, title="plan", extra=""):
    head = f"# {title}\n\n" + (f"**Status**: {status}\n" if status else "") + extra + "\n## Tasks\n\n"
    return head + "".join(i + "\n" for i in items)

LEGACY = "# Master plan\n\n**Status**: active\n\n## Subgoals\n\n- [x] 1. done\n- [ ] 2. the master plan's open item\n"
def index(*lines): return "# Plans\n\n**Layout**: revisions\n\n## Revisions\n\n" + "".join(l + "\n" for l in lines)
REV = "# Revision\n\n**Status**: open\n\n## Subgoals\n\n- [ ] 1. open in the revision\n"
def pergoal_index(*lines, status="active"):
    return f"# idx\n\n**Status**: {status}\n**Layout**: per-goal\n\n## Goals\n\n" + "".join(l + "\n" for l in lines)
def goalfile(marker, *items):
    return f"# goal\n\n**Goal**: [{marker}]\n\n```\n- [ ] fenced example, never an item\n```\n\n" + "".join(i + "\n" for i in items)

# id, branch, files, args, expectations. Expectations: report keys (exact), plus
#   exit, warn / prob / fix (substrings that must appear), nowarn (no warnings at all),
#   nprob (number of problems), cand (substrings), env, cwd, detach, raw (usage cases).
D = [
 ("e01", "d/e01", {"docs/plan/x/TODO.md": plan("active", "- [ ] x")}, ["TODO.md", "docs/plan/nope"],
  dict(exit=1, result="error", rung="1", prob=["nothing exists at 'docs/plan/nope'"])),
 ("e02", "d/e02", {"docs/plan/d2/DO.md": plan("active", "- [ ] x")}, ["TODO.md", "docs/plan/d2"],
  dict(exit=1, result="error", rung="1", prob=["holds no TODO.md, but docs/plan/d2/DO.md exists"], fix=["/step"])),
 ("e02b", "d/e02b", {"docs/plan/d2b/README.md": "not a plan\n"}, ["TODO.md", "d2b"],
  dict(exit=1, result="error", rung="1", prob=["docs/plan/d2b/ holds no TODO.md"])),
 ("e03", "d/e03", {}, ["TODO.md", P],
  dict(exit=1, result="error", rung="1", prob=["lies outside the repository"])),
 ("e04", "d/e04", {"docs/plan/d-e04/DO.md": plan("active", "- [ ] x"), MASTER: LEGACY}, ["TODO.md"],
  dict(exit=1, result="error", rung="2", prob=["exists only as DO.md", "docs/plan/d-e04/DO.md"], fix=["/step"])),
 ("e05", "d/e05", {MASTER: "# Plans\n\n**Layout**: revisions\n\n## Other\n"}, ["TODO.md"],
  dict(exit=1, result="error", rung="3", prob=["has no `## Revisions` section"])),
 ("e06", "d/e06", {MASTER: index("- [x] 06-old — closed", "- [~]07-alpha — x", "- [?] 08-beta — y")}, ["TODO.md"],
  dict(exit=1, result="error", rung="3", nprob=2, prob=["TODO.md:8 is not a revision line", "TODO.md:9 is not"])),
 ("e07", "d/e07", {MASTER: index("- [~] 07-alpha — open"), "docs/plan/07-alpha/_DO.md": REV}, ["TODO.md"],
  dict(exit=1, result="error", rung="3", prob=["docs/plan/07-alpha/_TODO.md is missing (docs/plan/07-alpha/_DO.md exists)"], fix=["mark line 7 [x]"])),
 ("e07b", "d/e07b", {MASTER: index("- [~] 07-alpha", "- [~] 08-beta")}, ["TODO.md"],
  dict(exit=1, result="error", rung="3", nprob=2, prob=["revision 07-alpha", "revision 08-beta"])),
 ("e08", "d/e08", {"docs/plan/d-e08/TODO.md": plan("active", "- [ ] x", extra="**Layout**: pergoal\n")}, ["TODO.md"],
  dict(exit=1, result="error", rung="2", prob=["d-e08/TODO.md:4 has `**Layout**: pergoal`"])),
 ("e08b", "d/e08b", {MASTER: "# M\n\n**Layout**: per-goal\n\n- [ ] x\n"}, ["TODO.md"],
  dict(exit=1, result="error", rung="3", prob=["docs/plan/TODO.md:3 has `**Layout**: per-goal`"])),
 ("e09", "d/e09", {"docs/plan/d-e09/TODO.md": pergoal_index("- [x] 01 — one", "- [ ] Rewrite without a number"),
                   "docs/plan/d-e09/TODO/01-one.md": goalfile("x", "- [x] a")}, ["TODO.md"],
  dict(exit=1, result="error", rung="2", prob=["d-e09/TODO.md:9 has no goal number"])),
 ("e10", "d/e10", {"docs/plan/d-e10/TODO.md": pergoal_index("- [x] 01 — one", "- [~] 02 — two"),
                   "docs/plan/d-e10/TODO/01-one.md": goalfile("x", "- [x] a")}, ["TODO.md"],
  dict(exit=1, result="error", rung="2", prob=["goal 02 has no file matching docs/plan/d-e10/TODO/02-*.md"], fix=["d-e10/TODO.md:9"])),
 ("e11", "d/e11", {"docs/plan/d-e11/TODO.md": pergoal_index("- [~] 02 — two"),
                   "docs/plan/d-e11/TODO/02-a.md": goalfile("~", "- [ ] a"),
                   "docs/plan/d-e11/TODO/02-b.md": goalfile("~", "- [ ] b")}, ["TODO.md"],
  dict(exit=1, result="error", rung="2", prob=["goal 02 matches several files", "TODO/02-a.md", "TODO/02-b.md"])),
 ("e12", "d/e12", {"docs/plan/d-e12/TODO.md": plan("active", "- [ ] x")}, ["TODO.md", "--goal", "999"],
  dict(exit=1, result="error", rung="2", prob=["--goal 999 is past the end"])),
 ("e12b", "d/e12b", {"docs/plan/d-e12b/TODO.md": plan("active", "- [ ] x", "  - [ ] sub")}, ["TODO.md", "--goal", "8"],
  dict(exit=1, result="error", rung="2", prob=["--goal 8 is not a top-level item"])),
 ("e13", None, {}, ["TODO.md"],
  dict(exit=1, result="error", rung="—", prob=["not inside a git repository"], cwd=NOGIT, env={"GIT_CEILING_DIRECTORIES": P})),
 ("e14", "d/e14", {MASTER: index("- [x] 06-old — closed")}, ["TODO.md", "docs/plan/TODO.md"],
  dict(exit=1, result="error", rung="1", prob=["is the revisions index and no revision in it is [~]"])),
 ("w01", "d/w01", {"docs/plan/d-w01/TODO.md": plan("", "- [ ] x")}, ["TODO.md"],
  dict(exit=0, result="found", rung="2", warn=["has no **Status** line"])),
 ("w02", "d/w02", {"docs/plan/d-w02/TODO.md": plan("wip", "- [ ] x")}, ["TODO.md"],
  dict(exit=0, result="found", rung="2", status="wip", warn=["status 'wip'"])),
 ("w03", "d/w03", {"docs/plan/d-w03/TODO.md": plan("merged — PR #3 — 2026-10-01", "- [ ] x")}, ["TODO.md"],
  dict(exit=0, result="found", rung="2", warn=["stamped merged"])),
 ("w04", "d/w04", {MASTER: LEGACY, "docs/plan/HEAD/TODO.md": plan("active", "- [ ] decoy")}, ["TODO.md"],
  dict(exit=0, result="found", rung="3", plan=MASTER, warn=["detached HEAD"], detach=True)),
 ("w04b", "d/w04b", {MASTER: LEGACY, "docs/plan/d-w04b/TODO.md": plan("active", "- [ ] decoy")}, ["TODO.md", "--branch", ""],
  dict(exit=0, result="found", rung="3", plan=MASTER, warn=["detached HEAD"])),
 ("w06", "d/w06", {"docs/plan/d-w06/TODO.md": plan("active", "- [X] capital", "* [ ] star", "- [ ] real")}, ["TODO.md"],
  dict(exit=0, result="found", next="docs/plan/d-w06/TODO.md:9 - [ ] real", warn=[":7 looks like an item", ":8 looks like an item"])),
 ("w07", "d/w07", {"docs/plan/other/DO.md": plan("active", "- [ ] x")}, ["TODO.md", "docs/plan/other/DO.md"],
  dict(exit=0, result="found", rung="1", plan="docs/plan/other/DO.md", warn=["is a DO.md plan"])),
 ("w08", "d/w08", {"docs/plan/DO.md": LEGACY, "docs/plan/feat-x/TODO.md": plan("active", "- [ ] x")}, ["TODO.md"],
  dict(exit=0, result="found", rung="4", plan="docs/plan/feat-x/TODO.md", warn=["master plan uses DO.md"])),
 ("w09", "d/w09", {"x/TODO.md": plan("active", "- [ ] root x"), "docs/plan/x/TODO.md": plan("active", "- [ ] plan x")}, ["TODO.md", "x"],
  dict(exit=0, result="found", rung="1", plan="x/TODO.md", warn=["also resolves under docs/plan/"])),
 ("w10", "d/w10", {MASTER: index("- [~] 07-alpha — open", "- [x] 06-old"), "docs/plan/07-alpha/_TODO.md": REV}, ["TODO.md", "docs/plan/TODO.md"],
  dict(exit=0, result="found", rung="1", plan="docs/plan/07-alpha/_TODO.md", kind="revision-master", warn=["revisions index, not a plan"])),
 ("w11", "d/w11", {"docs/plan/d-w11/TODO.md": pergoal_index("- [~] 01 — one"),
                   "docs/plan/d-w11/TODO/01-one.md": goalfile("x", "- [x] a")}, ["TODO.md"],
  dict(exit=0, result="found", warn=["has [~] but docs/plan/d-w11/TODO/01-one.md says **Goal**: [x]"])),
 # edge rules and reading rules
 ("x01", "d/x01", {"docs/plan/a/TODO.md": plan("active", "- [ ] only plan")}, ["TODO.md"],
  dict(exit=0, result="found", rung="4", plan="docs/plan/a/TODO.md", nowarn=True)),  # no docs/plan/TODO.md: rung 3 falls through
 ("x02", "d/x02", {"docs/plan/d-x02/TODO.md": pergoal_index("- [x] 01 — one", "- [~] 02 — two", "- [!] 03 — three"),
                   "docs/plan/d-x02/TODO/01-one.md": goalfile("x", "- [x] a"),
                   "docs/plan/d-x02/TODO/02-two.md": goalfile("~", "- [x] a", "  - [ ] nested", "- [ ] b")}, ["TODO.md"],
  dict(exit=0, result="found", layout="per-goal", next="docs/plan/d-x02/TODO.md:9 - [~] 02 — two",
       **{"goal-file": "docs/plan/d-x02/TODO/02-two.md"},
       subgoals=["docs/plan/d-x02/TODO/02-two.md:9", "docs/plan/d-x02/TODO/02-two.md:10", "docs/plan/d-x02/TODO/02-two.md:11"],
       blocked="docs/plan/d-x02/TODO.md:10", nowarn=True)),
 ("x03", "d/x03", {"docs/plan/d-x03/TODO.md": plan("active", "```", "- [ ] fenced", "**Layout**: per-goal", "```", "- [ ] real")}, ["TODO.md"],
  dict(exit=0, result="found", layout="legacy", next="docs/plan/d-x03/TODO.md:11 - [ ] real", nowarn=True)),
 ("x04", "d/x04", {"docs/plan/d-x04/TODO.md": plan("active", "- [~] first", "- [ ] second", "  - [x] s1", "  - [-] s2", "- [ ] third")}, ["TODO.md", "--goal", "8"],
  dict(exit=0, result="found", next="docs/plan/d-x04/TODO.md:8 - [ ] second",
       subgoals=["docs/plan/d-x04/TODO.md:9", "docs/plan/d-x04/TODO.md:10"])),
 ("x05", "feat/a,b", {"docs/plan/feat-a,b/TODO.md": plan("active", "- [ ] x", "  - [ ] one", "  - [ ] two")}, ["TODO.md"],
  dict(exit=0, result="found", rung="2", plan="docs/plan/feat-a,b/TODO.md",
       subgoals=["docs/plan/feat-a,b/TODO.md:8", "docs/plan/feat-a,b/TODO.md:9"])),
 ("x06", "plan", {MASTER: LEGACY}, ["TODO.md"],
  dict(exit=0, result="found", rung="3", plan=MASTER, kind="legacy-master")),  # branch `plan` must not take the root plan at rung 2
 ("x07", "d/x07", {"docs/plan/d-x07/TODO.md": plan("active", "- [ ] x")}, ["TODO.md"],
  dict(exit=0, result="found", rung="2", plan="docs/plan/d-x07/TODO.md", cwd_sub="docs/plan")),
 ("x08", "d/x08", {"docs/plan/d-x08/DO.md": plan("active", "- [x] a", "  - [ ] nested", "- [ ] b")}, ["DO.md", "--", "docs/plan/d-x08"],
  dict(exit=0, result="found", rung="1", next="docs/plan/d-x08/DO.md:8   - [ ] nested", subgoals="—")),
 # usage
 ("u01", "d/u", {}, [], dict(raw=True, exit=2)),
 ("u02", "d/u", {}, ["foo.md"], dict(raw=True, exit=2)),
 ("u03", "d/u", {}, ["TODO.md", "--goal", "abc"], dict(raw=True, exit=2)),
 ("u04", "d/u", {}, ["TODO.md", "a", "b"], dict(raw=True, exit=2)),
 ("u05", "d/u", {}, ["TODO.md", "--bogus"], dict(raw=True, exit=2)),
 ("u06", "d/u", {}, ["TODO.md", "--goal"], dict(raw=True, exit=2)),
 ("u07", "d/u", {}, ["TODO.md", "--goal", "0"], dict(raw=True, exit=2)),
]

def build_diag():
    os.makedirs(FD); os.makedirs(NOGIT, exist_ok=True)
    git("init", "-q", "-b", "main")
    open(FD + "/README.md", "w").write("diagnostics fixture\n")
    git("add", "-A"); git("-c", "user.name=suite", "-c", "user.email=suite@example.invalid", "commit", "-q", "-m", "Base")
    done = set()
    for cid, br, files, *_ in D:
        if not br or br in done: continue
        done.add(br)
        git("checkout", "-q", "main"); git("checkout", "-q", "-b", br)
        for path, text in files.items():
            os.makedirs(os.path.dirname(FD + "/" + path), exist_ok=True)
            open(FD + "/" + path, "w").write(text)
        git("add", "-A"); git("-c", "user.name=suite", "-c", "user.email=suite@example.invalid", "commit", "-q", "--allow-empty", "-m", cid)
    git("checkout", "-q", "main")

# --- the plan-locator fixture's cases, graded by the same expectations ---------------------------

FXC = [  # id, branch, args, expectations
 ("c01", "case/r1-valid", ["TODO.md", "docs/plan/some-plan"], dict(result="found", rung="1", plan="docs/plan/some-plan/TODO.md", next=":10")),
 ("c02", "case/r1-bad", ["TODO.md", "docs/plan/nope"], dict(exit=1, result="error", rung="1", prob=["nothing exists"])),  # was `stop`
 ("c03", "case/r2-flat", ["TODO.md"], dict(result="found", rung="2", plan="docs/plan/case-r2-flat/TODO.md", kind="branch", next=":10", subgoals=":11")),
 ("c04", "case/r2-moved", ["TODO.md"], dict(result="found", rung="2", plan="docs/plan/group/sub/case-r2-moved/TODO.md", next=":9")),
 ("c05", "case/r2-dup", ["TODO.md"], dict(result="ask", cand=["docs/plan/case-r2-dup/TODO.md", "docs/plan/archive/case-r2-dup/TODO.md"])),
 ("c06", "case/r3-legacy", ["TODO.md"], dict(result="found", rung="3", plan=MASTER, kind="legacy-master", lines="2498", next=":2487")),
 ("c07", "case/r3-rev-one", ["TODO.md"], dict(result="found", rung="3", plan="docs/plan/07-alpha/_TODO.md", kind="revision-master", next=":8")),
 ("c08", "case/r3-rev-two", ["TODO.md"], dict(result="ask", cand=["07-alpha", "08-beta"])),
 ("c09", "case/r3-rev-none", ["TODO.md"], dict(result="found", rung="4", plan="docs/plan/feat-other/TODO.md", next=":9")),
 ("c10", "case/r4-one", ["TODO.md"], dict(result="found", rung="4", plan="docs/plan/a/TODO.md", next=":9")),
 ("c11", "case/r4-several", ["TODO.md"], dict(result="ask", cand=["docs/plan/a/TODO.md", "docs/plan/b/TODO.md"], notcand=["docs/plan/c/TODO.md"])),
 ("c12", "case/r4-merged-only", ["TODO.md"], dict(result="ask", cand=["docs/plan/b/TODO.md", "docs/plan/c/TODO.md"])),
 ("c13", "case/r5-root", ["TODO.md"], dict(result="found", rung="5", plan="TODO.md", kind="root-file", next=":3", warn=["git mv TODO.md docs/plan/TODO.md"])),
 ("c14", "case/none", ["TODO.md"], dict(result="none")),
 ("c15", "case/do-model", ["DO.md"], dict(result="found", rung="2", plan="docs/plan/case-do-model/DO.md", next=":10")),
 ("c16", "case/blocked", ["TODO.md"], dict(result="found", rung="2", next=":12", blocked=":10")),
 ("c17", "case/closed", ["TODO.md"], dict(result="found", rung="2", next="—")),
 ("c18", "case/cmd-hitl", ["TODO.md"], dict(result="found", plan="docs/plan/case-cmd-hitl/TODO.md", next=":10")),
 ("c19", "case/cmd-hitl-master", ["TODO.md"], dict(result="found", plan=MASTER, next=":2487")),
 ("c20", "case/cmd-step", ["DO.md"], dict(result="found", plan="docs/plan/case-cmd-step/DO.md", next=":8")),
]

# fail-loudly cases (goal 11): permissions cannot live in git, so each case sets them up
# and tears them down around every run; shims put a failing awk first on PATH
SHIM, SHIM_LAYOUT, SHIM_GIT = (f"{P}/bin/{h(x)}" for x in ("awk-127", "awk-layout", "git-symref"))
X11 = [
 ("x09", "case/r2-flat", ["TODO.md"], dict(exit=1, result="error", rung="2", prob=["docs/plan/case-r2-flat/TODO.md cannot be read"], fix=["chmod u+r docs/plan/case-r2-flat/TODO.md"],
        setup="chmod 000 docs/plan/case-r2-flat/TODO.md", teardown="chmod 644 docs/plan/case-r2-flat/TODO.md")),
 ("x10", "case/r4-several", ["TODO.md"], dict(exit=1, result="error", rung="4", prob=["docs/plan/c/TODO.md cannot be read"],
        setup="chmod 000 docs/plan/c/TODO.md", teardown="chmod 644 docs/plan/c/TODO.md")),
 ("x11", "case/r1-valid", ["TODO.md", "docs/plan/some-plan"], dict(exit=1, result="error", rung="1", prob=["docs/plan/some-plan/ cannot be entered or listed"], fix=["chmod u+rx docs/plan/some-plan"],
        setup="chmod 000 docs/plan/some-plan", teardown="chmod 755 docs/plan/some-plan")),
 ("x12", "case/r2-moved", ["TODO.md"], dict(exit=1, result="error", rung="—", prob=["docs/plan/group/ cannot be entered or listed"],
        setup="chmod 000 docs/plan/group", teardown="chmod 755 docs/plan/group")),
 ("x13", "case/r2-flat", ["TODO.md"], dict(raw=True, exit=3, err="awk failed reading the **Layout** header of docs/plan/case-r2-flat/TODO.md", path=SHIM_LAYOUT)),
 ("x14", "case/r2-flat", ["TODO.md"], dict(raw=True, exit=3, err="locate-plan.sh: awk failed", path=SHIM)),
 ("x15", "case/r2-flat", ["TODO.md"], dict(raw=True, exit=3, err="git symbolic-ref failed with status 128", path=SHIM_GIT)),
]

# --- running and grading ---------------------------------------------------------------------

def parse(out):
    rep, order, key = {}, [], None
    for ln in out.splitlines():
        if ln.startswith("  ") and key: rep[key].append(ln[2:]); continue
        m = re.match(r"^([a-z-]+): (.*)$", ln)
        if not m: return None, order, f"unparseable line {ln!r}"
        key = m.group(1); order.append(key); rep[key] = [m.group(2)]
    return rep, order, None

def run(repo, br, args, exp, shell):
    cwd = exp.get("cwd") or repo
    if br:
        if exp.get("detach"):
            git("checkout", "-q", br, cwd=repo); git("checkout", "-q", "--detach", cwd=repo)
        else:
            git("checkout", "-q", br, cwd=repo)
        if exp.get("cwd_sub"): cwd = repo + "/" + exp["cwd_sub"]
    env = dict(os.environ, **exp.get("env", {}))
    if exp.get("path"): env["PATH"] = exp["path"] + ":" + env["PATH"]
    if exp.get("setup"): sh(["bash", "-c", exp["setup"]], cwd)
    try:
        r = sh([shell, SCRIPT, *args], cwd, env)
    finally:
        if exp.get("teardown"): sh(["bash", "-c", exp["teardown"]], cwd)
    return r.returncode, r.stdout, r.stderr

def grade(cid, exp, code, out, err):
    probs = []
    want_exit = exp.get("exit", 0)
    if code != want_exit: probs.append(f"exit {code}, want {want_exit} (stderr: {err.strip()[:120]!r})")
    if exp.get("raw"):
        if out: probs.append("usage error printed a report")
        if not err.strip(): probs.append("printed nothing on stderr")
        if exp.get("err") and exp["err"] not in err: probs.append(f"stderr lacks {exp['err']!r}: {err.strip()[:160]!r}")
        return probs
    if err.strip(): probs.append(f"stderr not empty: {err.strip()[:160]!r}")
    rep, order, perr = parse(out)
    if perr: return probs + [perr]
    if order != KEYS: probs.append(f"keys {order}")
    for k, v in rep.items():
        if any(x.startswith("/") for x in v): probs.append(f"{k}: an absolute path")
    one = lambda k: rep.get(k, ["—"])[0]
    allv = lambda k: "\n".join(rep.get(k, []))
    for k, want in exp.items():
        if k in ("exit", "raw", "env", "cwd", "detach", "cwd_sub", "setup", "teardown", "path", "err"): continue
        if k == "warn":
            for w in want:
                if w not in allv("warnings"): probs.append(f"warnings lack {w!r}: {allv('warnings')!r}")
        elif k == "nowarn":
            if one("warnings") != "—": probs.append(f"unexpected warnings {allv('warnings')!r}")
        elif k in ("prob", "fix"):
            key = "problem" if k == "prob" else "fix"
            for w in want:
                if w not in allv(key): probs.append(f"{key} lacks {w!r}: {allv(key)!r}")
        elif k == "nprob":
            if len(rep.get("problem", [])) != want: probs.append(f"{len(rep.get('problem', []))} problems, want {want}")
        elif k == "cand":
            for w in want:
                if w not in allv("candidates"): probs.append(f"candidates lack {w!r}")
        elif k == "notcand":
            for w in want:
                if w in allv("candidates"): probs.append(f"merged plan offered: {w}")
        elif k == "subgoals" and isinstance(want, list):
            if rep.get("subgoals") != want: probs.append(f"subgoals {rep.get('subgoals')} want {want}")
        elif k in ("next", "subgoals", "blocked") and want.startswith(":"):
            if want not in one(k): probs.append(f"{k}: want {want} in {one(k)!r}")
        elif one(k) != want: probs.append(f"{k}: want {want!r} got {one(k)!r}")
    if exp.get("result") == "error" and one("problem") == "—": probs.append("error without a problem")
    if exp.get("result") != "error" and one("problem") != "—": probs.append("problem on a non-error")
    return probs

def static_checks():
    src = open(SCRIPT).read()
    probs = []
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    if "<<" in code: probs.append("a heredoc or here-string (a temporary file on Bash 3.2)")
    if "mktemp" in code: probs.append("mktemp")
    # a redirect is `>`/`>>` after whitespace, optionally fd-prefixed, not `>=`; only
    # /dev/null and fd duplication are allowed. `goal > 0` is awk, not shell.
    for m in re.finditer(r"(?:^|\s)[0-9]?>>?(?!=)\s*([^\s)\"';|]+)", code.replace("goal > 0", "")):
        if m.group(1) not in ("/dev/null",) and not m.group(1).startswith("&"): probs.append(f"a redirect to {m.group(1)}")
    for bad in ("globstar", "mapfile", "readarray", "declare -A", ",,}", "^^}"):
        if bad in code: probs.append(f"Bash 4 feature {bad}")
    if re.search(r"grep[^|\n]*\\\|", code): probs.append("grep with \\| alternation")
    return probs

def mutants():
    """Every patch must apply cleanly to today's script and make the suite fail, except the
    known equivalent mutants, which must still pass it (if one starts failing, the script
    changed under it and the entry should be reviewed)."""
    d = HERE + "/mutants"; tmp = P + "/mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; out = f"{tmp}/{name}.sh"
        ap = sh(["patch", "-s", "-F0", "-o", out, SCRIPT, f"{d}/{fn}"], tmp)
        if ap.returncode:
            bad += 1; print(f"STALE  {name}: the patch no longer applies ({(ap.stdout + ap.stderr).strip()[:120]})"); continue
        os.chmod(out, 0o755)
        r = sh([sys.executable, "-I", os.path.abspath(__file__), "--once", "--script", out], HERE)
        killed = r.returncode != 0
        why = next((l for l in r.stdout.splitlines() if l.startswith("FAIL") or (l.startswith("static:") and l != "static: ok")), "")
        if name in EQUIVALENT:
            ok = not killed; print(f"{'EQUIV ' if ok else 'CHANGED'} {name}" + ("" if ok else f": now caught ({why[:100]})"))
        else:
            ok = killed; print(f"{'KILLED' if ok else 'SURVIVED'} {name}" + (f"  ({why[:90]})" if ok else ""))
        bad += not ok
    shutil.rmtree(tmp)
    print(f"\n{bad} failing"); sys.exit(1 if bad else 0)

def main():
    if "--mutants" in sys.argv: mutants()
    want = [a for a in sys.argv[1:] if re.match(r"^[cewxu]\d", a)]
    if not os.path.isdir(FX):
        r = subprocess.run([HERE + "/build-fixtures.sh"], env=dict(os.environ, LOCATE_PLAN_WORK=P))
        if r.returncode: sys.exit("build-fixtures.sh failed")
    if not os.path.isdir(FD): build_diag()
    if SKIPPED: print("shells not found, skipped:", ", ".join(SKIPPED))
    fails = 0
    st = static_checks()
    print("static:", "; ".join(st) or "ok"); fails += bool(st)
    cases = [(cid, FX, br, args, exp) for cid, br, args, exp in FXC] + \
            [(cid, FD, br, args, exp) for cid, br, _f, args, exp in D] + \
            [(cid, FX, br, args, exp) for cid, br, args, exp in X11]
    for cid, repo, br, args, exp in cases:
        if want and cid not in want: continue
        outs = []
        for shell in SHELLS:
            for _ in range(1 if "--once" in sys.argv else 2):  # twice per shell: determinism
                outs.append(run(repo, br, args, exp, shell))
        code, out, err = outs[0]
        probs = grade(cid, exp, code, out, err)
        if any(o != outs[0] for o in outs[1:]): probs.append("output differs between runs or shells")
        fails += bool(probs)
        print(f"{'PASS' if not probs else 'FAIL'} {cid:<5} {(br or '(no repo)'):<22} " + "; ".join(probs))
        if "-v" in sys.argv: print("      " + out.replace("\n", "\n      ") + err)
    for repo in (FX, FD):
        git("checkout", "-q", "main", cwd=repo)
        dirty = sh(["git", "status", "--porcelain", "--ignored"], repo).stdout.strip()
        if dirty: fails += 1; print(f"FAIL read-only: {repo} changed:\n{dirty}")
    if os.listdir(NOGIT): fails += 1; print(f"FAIL read-only: {NOGIT} not empty")
    print(f"\n{fails} failing")
    sys.exit(1 if fails else 0)

main()
