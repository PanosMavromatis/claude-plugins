"""propose-merge-record.sh suite: runs the script directly on a fixture repository built here,
one orphan branch per case (each case needs its own plans), and grades every report.
Writes only under $LOCATE_PLAN_WORK, which must lie outside the repository (the rule
dev/locate-plan/ uses, for the same reasons).

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--script PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

Every case runs twice under each shell found and must print the same thing each time.
Every report is checked for key order, exit code, the listed values, no absolute paths,
and that the fixture is left untouched. m29 then plays a branch's whole life through the
scripts: propose-branch-plan.sh places the backlink, as /new-branch will; this script finds
it; the merge is recorded as /smart-merge will; and locate-plan.sh, this script and
propose-branch-plan.sh all read the result back. --mutants applies each patch in mutants/
to a copy of the script and its library and runs the suite on it once; each must fail it.
A patch names its file relative to scripts/."""
import hashlib, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SD = REPO + "/plugins/workflow-claude/scripts"
SCRIPT = SD + "/propose-merge-record.sh"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
LIB = os.path.dirname(SCRIPT) + "/lib/plan-rules.sh"
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
FX, NOGIT, INT = W + "/pmr", W + "/pmr-nogit", W + "/pmr-int"
SHELLS = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if os.access(s, os.X_OK)]
if "--once" in sys.argv: SHELLS = SHELLS[:1]
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
AWK127 = f"{W}/bin/{h('pmr-awk-127')}"
KEYS = ["result", "layout", "masters", "stamp", "item", "after", "subgoal", "candidates",
        "warnings", "problem", "fix", "message"]

# Line numbers matter: the cases name them.
LEGACY = """# Master plan

## Subgoals — revision 03-lifecycle

- [x] Done already
  > **Branch:** feat/old
  > **Done:** it landed — PR #1
- [~] Open, for feat/x
  Scope: a continuation line.
  > **Branch:** feat/x
  > **Q:** a question?
  > **A:** an answer.
- [ ] Open, for a longer name
  > **Branch:** feat/x-y
- [ ] Two branches
  > **Branch:** feat/a
  > **Branch:** feat/b
- [-] Descoped
  > **Branch:** feat/gone

A paragraph that quotes a backlink:
> **Branch:** feat/z

```
- [ ] fenced, not an item
  > **Branch:** feat/z
```
"""
DUP = "# M\n\n- [ ] First\twith a tab\n  > **Branch:** feat/x\n- [ ] Second\n  Scope.\n  > **Branch:** feat/x\n- [ ] Other\n  > **Branch:** feat/y\n"
INDEX = lambda *revs: "# Plans\n\n**Layout**: revisions\n\n## Revisions\n\n" + "".join(r + "\n" for r in revs)
REV = lambda label, branch: f"""# Revision {label}

**Status**: open

## Subgoals

- [x] 1. First, merged
  > **Branch:** feat/first
- [~] 2. Plan directory structure
  Scope: everything.
  > **Branch:** {branch}
- [ ] 3. Another one
"""

def plan(sub="One", status="**Status**: active", tail=""):
    """A branch plan: the status line is line 3 when there is one."""
    head = "# b\n\n" + (status + "\n" if status else "") + (f"**Subgoal**: {sub}\n" if sub is not None else "")
    return head + "\n## Tasks\n\n- [x] t\n" + tail

P = "docs/plan/feat-x/TODO.md"
STAMP = P + ":3 **Status**: active"
PG = "docs/plan/07-rev/feat-plan-dirs/TODO.md"
PGPLAN = "# feat/plan-dirs\n\n**Status**: active\n**Revision**: 07-rev\n**Subgoal**: 2. Plan directory structure\n**Layout**: per-goal\n\n## Goals\n\n- [x] 01 — a\n"
INT_MASTER = "# Master plan\n\n## Subgoals — revision 03-lifecycle\n\n- [ ] Open and free\n  Scope: a line.\n- [ ] Another\n"

# id, files on the case's branch, arguments after the script (or a special), expectations
C = [
 ("m01", {"docs/plan/TODO.md": LEGACY, P: plan("Open, for feat/x")}, ["TODO.md", "feat/x", "--", P],
  dict(exit=0, result="propose", layout="legacy", masters=["docs/plan/TODO.md"], stamp=STAMP,
       item="docs/plan/TODO.md:8 - [~] Open, for feat/x", after="docs/plan/TODO.md:12", subgoal="Open, for feat/x",
       warnings=[], msg="close docs/plan/TODO.md:8, with the Done line after line 12")),
 ("m02", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x-"],
  dict(exit=0, result="none", stamp="—", item="—", warnings=[], msg="Nothing to record")),
 ("m03", {"docs/plan/TODO.md": LEGACY, "docs/plan/feat-z/TODO.md": plan("Zed")}, ["TODO.md", "feat/z", "--", "docs/plan/feat-z/TODO.md"],
  dict(exit=0, result="propose", item="—", after="—",
       warnings=["docs/plan/feat-z/TODO.md names the subgoal `Zed`, but no item in docs/plan/TODO.md backlinks feat/z: the backlink was lost or misspelled"])),
 ("m04", {"docs/plan/TODO.md": DUP, P: plan()}, ["TODO.md", "feat/x", "--", P],
  dict(exit=0, result="ask", stamp=STAMP, item="—", after="—",
       cand=["docs/plan/TODO.md:3 - [ ] First\twith a tab", "docs/plan/TODO.md:5 - [ ] Second"], msg="--item <file>:<line>")),
 ("m05", {"docs/plan/TODO.md": DUP, P: plan()}, ["TODO.md", "feat/x", "--item", "docs/plan/TODO.md:5", "--", P],
  dict(exit=0, result="propose", item="docs/plan/TODO.md:5 - [ ] Second", after="docs/plan/TODO.md:7", warnings=[])),
 ("m06", {"docs/plan/TODO.md": DUP, P: plan()}, ["TODO.md", "feat/x", "--item", "docs/plan/TODO.md:8", "--", P],
  dict(exit=1, result="error", prob=["--item names docs/plan/TODO.md:8, which is not an item that backlinks feat/x"],
       fix=["pass one of: docs/plan/TODO.md:3, docs/plan/TODO.md:5"])),
 ("m06b", {"docs/plan/TODO.md": DUP}, ["TODO.md", "feat/q", "--item", "docs/plan/TODO.md:3"],
  dict(exit=1, result="error", prob=["but no item backlinks feat/q"], fix=["run it again without --item"])),
 ("m07", {"docs/plan/TODO.md": LEGACY, "docs/plan/feat-s/TODO.md": plan("standalone")}, ["TODO.md", "feat/s", "--", "docs/plan/feat-s/TODO.md"],
  dict(exit=0, result="propose", item="—", subgoal="standalone", warnings=[], msg="feat/s is standalone, so no subgoal is closed")),
 ("m08", {"docs/plan/TODO.md": LEGACY, P: plan("standalone")}, ["TODO.md", "feat/x", "--", P],
  dict(exit=0, result="propose", item="docs/plan/TODO.md:8 - [~] Open, for feat/x",
       warnings=[f"{P} says the branch is standalone, but docs/plan/TODO.md:8 backlinks feat/x"])),
 ("m09", {"docs/plan/TODO.md": LEGACY, "docs/plan/feat-z/TODO.md": plan(None)}, ["TODO.md", "feat/z", "--", "docs/plan/feat-z/TODO.md"],
  dict(exit=0, result="propose", subgoal="—",
       warnings=["docs/plan/feat-z/TODO.md has no **Subgoal** line to say whether it is standalone, and no item in docs/plan/TODO.md backlinks feat/z"])),
 ("m10", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x"],
  dict(exit=0, result="propose", stamp="—", subgoal="—", item="docs/plan/TODO.md:8 - [~] Open, for feat/x",
       after="docs/plan/TODO.md:12", warnings=[], msg="Close docs/plan/TODO.md:8")),
 ("m11", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/q", "--"],
  dict(exit=0, result="none", stamp="—", item="—", warnings=[])),
 ("m12", {"docs/plan/TODO.md": LEGACY, P: plan(status=None)}, ["TODO.md", "feat/x", "--", P],
  dict(exit=1, result="error", stamp="—", item="—", prob=[f"{P} has no **Status** line"],
       fix=["add `**Status**: active` under its title, then run this again"])),
 ("m12b", {"docs/plan/TODO.md": LEGACY, P: plan(tail="\n```\n**Status**: merged — PR #9 — 2026-01-01\n```\n")}, ["TODO.md", "feat/x", "--", P],
  dict(exit=0, result="propose", stamp=STAMP, warnings=[])),
 ("m13", {"docs/plan/TODO.md": LEGACY, "docs/plan/feat-old/TODO.md": plan("Done already", "**Status**: merged — PR #1 — 2026-01-01")},
  ["TODO.md", "feat/old", "--", "docs/plan/feat-old/TODO.md"],
  dict(exit=0, result="propose", stamp="docs/plan/feat-old/TODO.md:3 **Status**: merged — PR #1 — 2026-01-01",
       item="docs/plan/TODO.md:5 - [x] Done already", after="docs/plan/TODO.md:7",
       warnings=["docs/plan/feat-old/TODO.md is already stamped `merged — PR #1 — 2026-01-01`: the merge may be recorded already",
                 "docs/plan/TODO.md:5 is already closed ([x]): the merge may be recorded already"])),
 ("m14", {"docs/plan/TODO.md": LEGACY, "docs/plan/feat-gone/TODO.md": plan("Descoped")}, ["TODO.md", "feat/gone", "--", "docs/plan/feat-gone/TODO.md"],
  dict(exit=0, result="propose", item="docs/plan/TODO.md:18 - [-] Descoped",
       warnings=["docs/plan/TODO.md:18 is already closed ([-]): the merge may be recorded already"])),
 ("m15", {"docs/plan/TODO.md": LEGACY, "docs/plan/feat-x/DO.md": plan()}, ["TODO.md", "feat/x", "--", "docs/plan/feat-x/DO.md"],
  dict(exit=1, result="error", prob=["docs/plan/feat-x/DO.md is not a TODO.md plan"], fix=["pass the model the plan was resolved with: DO.md"])),
 ("m16", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x", "--", P],
  dict(exit=1, result="error", prob=[f"{P} is not a file"])),
 ("m16b", {"docs/plan/TODO.md": LEGACY, P: plan()}, "absolute",
  dict(exit=1, result="error", prob=["the plan path is absolute"], fix=["pass it repository-relative"])),
 ("m17", {"docs/plan/TODO.md": INDEX("- [~] 07-rev — open", "- [x] 05-old — closed"),
          "docs/plan/07-rev/_TODO.md": REV("07-rev", "feat/plan-dirs"), "docs/plan/05-old/_TODO.md": REV("05-old", "feat/plan-dirs"),
          PG: PGPLAN, "docs/plan/07-rev/feat-plan-dirs/TODO/01-a.md": "# 01 — a\n\n**Goal**: [x]\n"},
  ["TODO.md", "feat/plan-dirs", "--", PG],
  dict(exit=0, result="propose", layout="revisions", masters=["docs/plan/07-rev/_TODO.md"], stamp=PG + ":3 **Status**: active",
       item="docs/plan/07-rev/_TODO.md:9 - [~] 2. Plan directory structure", after="docs/plan/07-rev/_TODO.md:11",
       subgoal="2. Plan directory structure", warnings=[])),
 ("m18", {"docs/plan/TODO.md": INDEX("- [~] 07-rev — a", "- [~] 08-two — b"),
          "docs/plan/07-rev/_TODO.md": REV("07-rev", "feat/other"), "docs/plan/08-two/_TODO.md": REV("08-two", "feat/plan-dirs")},
  ["TODO.md", "feat/plan-dirs"],
  dict(exit=0, result="propose", masters=["docs/plan/07-rev/_TODO.md", "docs/plan/08-two/_TODO.md"],
       item="docs/plan/08-two/_TODO.md:9 - [~] 2. Plan directory structure", after="docs/plan/08-two/_TODO.md:11", warnings=[])),
 ("m19", {"docs/plan/TODO.md": INDEX("- [x] 05-old — closed"), "docs/plan/05-old/_TODO.md": REV("05-old", "feat/x"), P: plan()},
  ["TODO.md", "feat/x", "--", P],
  dict(exit=0, result="propose", layout="revisions", masters=[], item="—",
       warnings=["no revision is open in docs/plan/TODO.md, so there is no subgoal to close"])),
 ("m20", {"docs/plan/DO.md": LEGACY, P: plan()}, ["TODO.md", "feat/x", "--", P],
  dict(exit=0, result="propose", layout="—", masters=[], item="—",
       warnings=["there is no docs/plan/TODO.md, but docs/plan/DO.md exists: the master plan uses the other model, so no subgoal is closed in it"])),
 ("m21", {P: plan()}, ["TODO.md", "feat/x", "--", P],
  dict(exit=0, result="propose", layout="—", masters=[], item="—",
       warnings=[f"{P} names the subgoal `One`, but there is no master plan to close it in"])),
 ("m22", {"docs/plan/TODO.md": "# P\n\n**Layout**: revisons\n\n## Revisions\n", P: plan()}, ["TODO.md", "feat/x", "--", P],
  dict(exit=1, result="error", prob=["docs/plan/TODO.md:3 has `**Layout**: revisons`, which is not valid there"],
       fix=["correct line 3 to `**Layout**: revisions`"])),
 ("m23", {"docs/plan/TODO.md": INDEX("- [~] 09-gone — open")}, ["TODO.md", "feat/x"],
  dict(exit=1, result="error", prob=["revision 09-gone is open at docs/plan/TODO.md:7, but docs/plan/09-gone/_TODO.md is missing"])),
 ("m24", {"docs/plan/DO.md": INDEX("- [~] 07-rev — open"), "docs/plan/07-rev/_DO.md": REV("07-rev", "fix/y"),
          "docs/plan/07-rev/fix-y/DO.md": plan("2. Plan directory structure")},
  ["DO.md", "fix/y", "--", "docs/plan/07-rev/fix-y/DO.md"],
  dict(exit=0, result="propose", layout="revisions", masters=["docs/plan/07-rev/_DO.md"],
       item="docs/plan/07-rev/_DO.md:9 - [~] 2. Plan directory structure", after="docs/plan/07-rev/_DO.md:11", warnings=[])),
 ("m25", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/b"],
  dict(exit=0, result="propose", item="docs/plan/TODO.md:15 - [ ] Two branches", after="docs/plan/TODO.md:17", warnings=[])),
 ("m26", {"README.md": "x\n"}, ["TODO.md"], dict(raw=True, exit=2, err=["no branch name given"])),
 ("m26b", {"README.md": "x\n"}, ["TODO.md", "feat x"], dict(raw=True, exit=2, err=["cannot hold whitespace"])),
 ("m26c", {"README.md": "x\n"}, ["TODO.md", "feat/x", "--item", "docs/plan/TODO.md"], dict(raw=True, exit=2, err=["--item takes <file>:<line>"])),
 ("m26d", {"README.md": "x\n"}, ["TODO.md", "feat/x", "--", "a", "b"], dict(raw=True, exit=2, err=["at most one plan path"])),
 ("m26e", {"README.md": "x\n"}, ["TODO.md", "-x"], dict(raw=True, exit=2, err=["unknown option"])),
 ("m26f", {"README.md": "x\n"}, ["PLAN.md", "feat/x"], dict(raw=True, exit=2, err=["the model must be TODO.md or DO.md"])),
 ("m27", {}, "nogit", dict(exit=1, result="error", prob=["not inside a git repository"])),
 ("m28", {"docs/plan/TODO.md": LEGACY}, "awk127", dict(raw=True, exit=3, err=["propose-merge-record.sh: awk failed", "hint: awk exited 127"])),
 ("m29", {"docs/plan/TODO.md": INT_MASTER}, "integration", dict()),
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
        git("checkout", "-q", "--orphan", f"case/{cid}"); git("rm", "-rq", "--cached", "."); shutil.rmtree(FX + "/docs", ignore_errors=True)
        for f in os.listdir(FX):
            if f != ".git": os.remove(FX + "/" + f) if os.path.isfile(FX + "/" + f) else shutil.rmtree(FX + "/" + f)
        for rel, text in (files or {"README.md": "x\n"}).items():
            p = f"{FX}/{rel}"; os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(text)
        git("add", "-A"); git("commit", "-q", "-m", cid)
    git("checkout", "-q", "main")
    os.makedirs(NOGIT, exist_ok=True); os.makedirs(AWK127, exist_ok=True)
    open(AWK127 + "/awk", "w").write("#!/bin/sh\nexit 127\n"); os.chmod(AWK127 + "/awk", 0o755)

def parse(out):
    rep, order, key = {}, [], None
    for line in out.splitlines():
        if line.startswith("  ") and key: rep[key].append(line[2:]); continue
        m = re.match(r"^([a-z-]+): (.*)$", line)
        if not m: return None, order
        key = m.group(1); order.append(key); rep[key] = [m.group(2)]
    return rep, order

def run(cid, args, shell, script=None):
    env = dict(os.environ); cwd = FX
    if args == "nogit": cwd = NOGIT; env["GIT_CEILING_DIRECTORIES"] = W; args = ["TODO.md", "feat/x"]
    elif args == "awk127": env["PATH"] = AWK127 + ":" + env["PATH"]; git("checkout", "-q", f"case/{cid}"); args = ["TODO.md", "feat/x"]
    elif args == "absolute": git("checkout", "-q", f"case/{cid}"); args = ["TODO.md", "feat/x", "--", f"{FX}/{P}"]
    else: git("checkout", "-q", f"case/{cid}")
    return sh([shell, script or SCRIPT, *args], cwd, env)

def grade(exp, r):
    probs = []
    if r.returncode != exp["exit"]: probs.append(f"exit {r.returncode}, want {exp['exit']} (stderr: {r.stderr.strip()[:80]!r})")
    for e in exp.get("err", []):
        if e not in r.stderr: probs.append(f"stderr lacks {e!r}: {r.stderr.strip()[:120]!r}")
    if exp.get("raw"):
        if r.stdout: probs.append("a report printed on a raw failure")
        return probs
    rep, order = parse(r.stdout)
    if rep is None: return probs + [f"unparseable report: {r.stdout[:120]!r}"]
    if order != KEYS: return probs + [f"keys {order}"]
    one = lambda k: "\n".join(rep[k]); allv = lambda k: [] if rep[k] == ["—"] else rep[k]
    for k in ("result", "layout", "stamp", "item", "after", "subgoal"):
        if k in exp and one(k) != exp[k]: probs.append(f"{k}: want {exp[k]!r} got {one(k)!r}")
    for k in ("masters", "warnings"):
        if k in exp and allv(k) != exp[k]: probs.append(f"{k} {allv(k)} want {exp[k]}")
    if "cand" in exp and allv("candidates") != exp["cand"]: probs.append(f"candidates {allv('candidates')} want {exp['cand']}")
    for k, key in (("prob", "problem"), ("fix", "fix")):
        for w in exp.get(k, []):
            if not any(w in v for v in allv(key)): probs.append(f"{key} lacks {w!r}: {allv(key)}")
    if len(allv("problem")) != len(allv("fix")): probs.append(f"{len(allv('problem'))} problems but {len(allv('fix'))} fixes")
    if exp.get("result") in ("propose", "ask", "none") and allv("problem"): probs.append("a problem on a " + exp["result"])
    if exp.get("result") == "error" and not allv("problem"): probs.append("an error without a problem")
    if exp.get("result") != "ask" and allv("candidates"): probs.append("candidates outside an ask")
    if "msg" in exp and exp["msg"] not in one("message"): probs.append(f"message lacks {exp['msg']!r}: {one('message')!r}")
    for k in KEYS:
        for v in rep[k]:
            if v.startswith("/") or W in v: probs.append(f"an absolute path in {k}: {v[:80]!r}")
    return probs

def rd(p): return open(p).read().split("\n")
def wr(p, lines): open(p, "w").write("\n".join(lines))

def integration(shell, script):
    """A branch's life through the scripts: placed, backlinked, merged, and read back."""
    probs = []
    shutil.rmtree(INT, ignore_errors=True)
    r = sh(["git", "clone", "-q", "-b", "case/m29", FX, INT], W)
    if r.returncode: return [f"clone failed: {r.stderr.strip()}"]
    sh(["git", "checkout", "-q", "-b", "feat/int"], INT)
    # /new-branch: propose, then write the plan, the backlink and the [~] marker.
    pb = sh([shell, SD + "/propose-branch-plan.sh", "TODO.md", "feat/int", "--subgoal", "docs/plan/TODO.md:5", "--", "A"], INT)
    brep, _ = parse(pb.stdout)
    if pb.returncode or not brep or brep["result"] != ["propose"]: return [f"no branch proposal: {pb.stdout[:200]!r}"]
    index = brep["index"][0]; bf, bl = brep["backlink"][0].rsplit(":", 1)
    os.makedirs(os.path.dirname(f"{INT}/{index}"), exist_ok=True)
    open(f"{INT}/{index}", "w").write("# feat/int\n\n**Status**: active\n**Created**: 2026-10-10\n**Subgoal**: Open and free\n\n## Tasks\n\n- [x] A\n")
    m = rd(f"{INT}/{bf}"); m.insert(int(bl), "  > **Branch:** feat/int"); m[4] = m[4].replace("- [ ]", "- [~]", 1); wr(f"{INT}/{bf}", m)
    # /smart-merge step 7: propose, then stamp and close exactly what the report names.
    r = sh([shell, script, "TODO.md", "feat/int", "--", index], INT); rep, _ = parse(r.stdout)
    want = {"result": "propose", "stamp": f"{index}:3 **Status**: active", "item": "docs/plan/TODO.md:5 - [~] Open and free",
            "after": "docs/plan/TODO.md:7", "warnings": "—"}
    for k, v in want.items():
        if not rep or rep.get(k, [""])[0] != v: probs.append(f"merge proposal {k}: want {v!r} got {(rep or {}).get(k)}")
    if probs: return probs
    sp, sl = rep["stamp"][0].split(" ", 1)[0].rsplit(":", 1)
    p = rd(f"{INT}/{sp}"); p[int(sl) - 1] = "**Status**: merged — PR #1 — 2026-10-10"; wr(f"{INT}/{sp}", p)
    ip, il = rep["item"][0].split(" ", 1)[0].rsplit(":", 1); al = int(rep["after"][0].rsplit(":", 1)[1])
    m = rd(f"{INT}/{ip}"); m[int(il) - 1] = m[int(il) - 1].replace("- [~]", "- [x]", 1)
    m.insert(al, "  > **Done:** it landed — PR #1"); wr(f"{INT}/{ip}", m)
    # Read it back.
    lp = sh([shell, SD + "/locate-plan.sh", "TODO.md"], INT); lrep, _ = parse(lp.stdout)
    if not lrep or lrep.get("plan") != [index] or not lrep.get("status", [""])[0].startswith("merged"):
        probs.append(f"locate-plan.sh does not see the merged plan: {lp.stdout[:300]!r}")
    again = sh([shell, script, "TODO.md", "feat/int", "--", index], INT); arep, _ = parse(again.stdout)
    ws = (arep or {}).get("warnings", [])
    if not any("is already stamped" in w for w in ws) or not any("is already closed ([x])" in w for w in ws):
        probs.append(f"a second merge proposal does not warn twice: {again.stdout[:400]!r}")
    if not arep or arep.get("after") != ["docs/plan/TODO.md:8"]:
        probs.append(f"the Done line is not inside the block: after {(arep or {}).get('after')}")
    nb = sh([shell, SD + "/propose-branch-plan.sh", "TODO.md", "feat/other"], INT); nrep, _ = parse(nb.stdout)
    if not nrep or any(c.startswith("docs/plan/TODO.md:5 ") for c in nrep.get("candidates", [])):
        probs.append(f"the closed subgoal is still offered to a new branch: {nb.stdout[:300]!r}")
    shutil.rmtree(INT, ignore_errors=True)
    return probs

def static_checks():
    src = open(SCRIPT).read() + "\n" + open(LIB).read()
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#")); probs = []
    if "<<" in code: probs.append("a heredoc or here-string (a temporary file on Bash 3.2)")
    if "mktemp" in code: probs.append("mktemp")
    for m in re.finditer(r"(?:^|\s)[0-9]?>>?(?!=)\s*([^\s)\"';|]+)", code.replace("goal > 0", "")):
        if m.group(1) != "/dev/null" and not m.group(1).startswith("&"): probs.append(f"a redirect to {m.group(1)}")
    for bad in ("globstar", "mapfile", "readarray", "declare -A", ",,}", "^^}"):
        if bad in code: probs.append(f"Bash 4 feature {bad}")
    if re.search(r"grep[^|\n]*\\\|", code): probs.append("grep with \\| alternation")
    return probs

def mutants():
    d = HERE + "/mutants"; tmp = W + "/pmr-mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; root = f"{tmp}/{name}"; out = root + "/propose-merge-record.sh"
        os.makedirs(root + "/lib"); shutil.copy2(SCRIPT, out); shutil.copy2(LIB, root + "/lib/plan-rules.sh")
        ap = sh(["patch", "-s", "-F0", "-p1", "-d", root, "-i", f"{d}/{fn}"], tmp)
        if ap.returncode:
            bad += 1; print(f"STALE  {name}: the patch no longer applies ({(ap.stdout + ap.stderr).strip()[:120]})"); continue
        r = sh([sys.executable, "-I", os.path.abspath(__file__), "--once", "--script", out], HERE)
        killed = r.returncode != 0
        why = next((l for l in r.stdout.splitlines() if l.startswith("FAIL") or (l.startswith("static:") and l != "static: ok")), "")
        print(f"{'KILLED' if killed else 'SURVIVED'} {name}" + (f"  ({why[:100]})" if killed else ""))
        bad += not killed
    shutil.rmtree(tmp); print(f"\n{bad} failing"); sys.exit(1 if bad else 0)

def main():
    if "--mutants" in sys.argv: mutants()
    want = [a for a in sys.argv[1:] if re.match(r"^m\d", a)]
    build()
    heads = git("for-each-ref", "--format=%(refname) %(objectname)")
    st = static_checks(); print("static: " + ("ok" if not st else "; ".join(st)))
    fails = len(st)
    for cid, _, args, exp in C:
        if want and cid not in want: continue
        outs, probs = set(), []
        for shell in SHELLS:
            for _ in range(1 if "--once" in sys.argv else 2):
                if args == "integration":
                    probs += [p for p in integration(shell, SCRIPT) if p not in probs]; continue
                r = run(cid, args, shell); outs.add((r.returncode, r.stdout, r.stderr))
                probs += [p for p in grade(exp, r) if p not in probs]
                if git("status", "--porcelain") or git("for-each-ref", "--format=%(refname) %(objectname)") != heads:
                    probs.append("the fixture changed")
        if len(outs) > 1: probs.append("output differs between runs or shells")
        print(f"{'PASS' if not probs else 'FAIL'} {cid:<5} " + "; ".join(probs))
        if "-v" in sys.argv: print("".join(o[1] + o[2] for o in sorted(outs)))
        fails += bool(probs)
    git("checkout", "-q", "main")
    print(f"\n{fails} failing"); sys.exit(1 if fails else 0)

main()
