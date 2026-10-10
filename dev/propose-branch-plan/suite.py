"""propose-branch-plan.sh suite: runs the script directly on a fixture repository built here,
one orphan branch per case (each case needs its own root plan), and grades every report.
Writes only under $LOCATE_PLAN_WORK, which must lie outside the repository (the rule
dev/locate-plan/ uses, for the same reasons).

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--script PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

Every case runs twice under each shell found and must print the same thing each time.
Every report is checked for key order, exit code, the listed values, no absolute paths,
and that the fixture is left untouched. p24 then writes what a proposal lists, as
/new-branch will, and checks that locate-plan.sh resolves it and check-plan-index.sh
finds it clean: the writer and the reader agree. --mutants applies each patch in mutants/
to a copy of the script and its library and runs the suite on it once; each must fail it.
A patch names its file relative to scripts/."""
import hashlib, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SD = REPO + "/plugins/workflow-claude/scripts"
SCRIPT = SD + "/propose-branch-plan.sh"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
LIB = os.path.dirname(SCRIPT) + "/lib/plan-rules.sh"
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
FX, NOGIT, INT = W + "/pbp", W + "/pbp-nogit", W + "/pbp-int"
SHELLS = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if os.access(s, os.X_OK)]
if "--once" in sys.argv: SHELLS = SHELLS[:1]
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
AWK127 = f"{W}/bin/{h('pbp-awk-127')}"
KEYS = ["result", "layout", "revision", "subgoal", "dir", "index", "goals", "backlink", "candidates",
        "warnings", "problem", "fix", "message"]

LEGACY = """# Master plan

**Status**: active

## Subgoals — revision 03-lifecycle

- [x] Done already
  > **Branch:** feat/old
- [ ] Open, with a branch
  > **Branch:** feat/taken
- [ ] Open and free
  Scope: a continuation line.
  > **Q:** a question?
  > **A:** an answer.
- [~] In progress and free

  Not part of the block above.
- [!] Blocked

## Notes

```
- [ ] fenced, not an item
```
"""
INDEX = lambda *revs: "# Plans\n\n**Layout**: revisions\n\n## Revisions\n\n" + "".join(r + "\n" for r in revs)
REVMASTER = """# Revision {label}

**Status**: open

## Subgoals

- [x] 1. First, merged
  > **Branch:** feat/first
- [ ] 2. Plan directory structure
  Scope: everything. Acceptance: it works.
- [ ] 3. Another one
"""
ALL_TAKEN = "# Master plan\n\n## Subgoals — revision 03-x\n\n- [ ] Only one\n  > **Branch:** feat/one\n- [x] Done\n"
LONG = "Rewrite Step 1 of both step commands so they call the new script"

# id, files on the case's branch, arguments after the script (or a special), expectations
C = [
 ("p01", {"README.md": "x\n"}, ["TODO.md", "feat/x"],
  dict(exit=0, result="propose", layout="legacy", revision="—", subgoal="standalone", dir="docs/plan/feat-x",
       index="docs/plan/feat-x/TODO.md", goals=[], backlink="—", warnings=[])),
 ("p02", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x"],
  dict(exit=0, result="ask", layout="legacy", dir="—", cand=["docs/plan/TODO.md:11 - [ ] Open and free",
       "docs/plan/TODO.md:15 - [~] In progress and free"], msg="--subgoal <file>:<line>, or pass --standalone")),
 ("p03", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x", "--subgoal", "docs/plan/TODO.md:11", "--", "A", "B"],
  dict(exit=0, result="propose", layout="legacy", revision="03-lifecycle", subgoal="docs/plan/TODO.md:11 - [ ] Open and free",
       dir="docs/plan/feat-x", goals=[], backlink="docs/plan/TODO.md:14", warnings=[])),
 ("p03b", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x", "--subgoal", "docs/plan/TODO.md:15"],
  dict(exit=0, result="propose", backlink="docs/plan/TODO.md:15")),
 ("p04", {"docs/plan/TODO.md": ALL_TAKEN}, ["TODO.md", "feat/x"],
  dict(exit=0, result="propose", subgoal="standalone", backlink="—",
       warn=["no open subgoal in docs/plan/TODO.md is without a branch, so the plan is standalone"])),
 ("p05", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x", "--standalone"],
  dict(exit=0, result="propose", subgoal="standalone", revision="—", backlink="—", warnings=[])),
 ("p06", {"docs/plan/TODO.md": INDEX("- [~] 07-rev — open", "- [x] 05-old — closed"),
          "docs/plan/07-rev/_TODO.md": REVMASTER.format(label="07-rev"), "docs/plan/05-old/_TODO.md": REVMASTER.format(label="05-old")},
  ["TODO.md", "feat/x", "--", "One"],
  dict(exit=0, result="ask", layout="per-goal", cand=["docs/plan/07-rev/_TODO.md:9 - [ ] 2. Plan directory structure",
       "docs/plan/07-rev/_TODO.md:11 - [ ] 3. Another one"])),
 ("p07", {"docs/plan/TODO.md": INDEX("- [~] 07-rev — open"), "docs/plan/07-rev/_TODO.md": REVMASTER.format(label="07-rev")},
  ["TODO.md", "feat/plan-dirs", "--subgoal", "docs/plan/07-rev/_TODO.md:9", "--", "Write the spec", "Build it", LONG],
  dict(exit=0, result="propose", layout="per-goal", revision="07-rev",
       subgoal="docs/plan/07-rev/_TODO.md:9 - [ ] 2. Plan directory structure",
       dir="docs/plan/07-rev/feat-plan-dirs", index="docs/plan/07-rev/feat-plan-dirs/TODO.md",
       goals=["docs/plan/07-rev/feat-plan-dirs/TODO/01-write-the-spec.md - [ ] 01 — Write the spec",
              "docs/plan/07-rev/feat-plan-dirs/TODO/02-build-it.md - [ ] 02 — Build it",
              f"docs/plan/07-rev/feat-plan-dirs/TODO/03-rewrite-step-1-of-both-step-commands-so.md - [ ] 03 — {LONG}"],
       backlink="docs/plan/07-rev/_TODO.md:10", warnings=[])),
 ("p08", {"docs/plan/TODO.md": INDEX("- [~] 07-rev — a", "- [~] 08-two — b"),
          "docs/plan/07-rev/_TODO.md": REVMASTER.format(label="07-rev"), "docs/plan/08-two/_TODO.md": REVMASTER.format(label="08-two")},
  ["TODO.md", "feat/x", "--", "One"],
  dict(exit=0, result="ask", cand=["docs/plan/07-rev/_TODO.md:9", "docs/plan/07-rev/_TODO.md:11",
       "docs/plan/08-two/_TODO.md:9", "docs/plan/08-two/_TODO.md:11"])),
 ("p09", {"docs/plan/TODO.md": INDEX("- [x] 05-old — closed"), "docs/plan/05-old/_TODO.md": REVMASTER.format(label="05-old")},
  ["TODO.md", "feat/x", "--", "One"],
  dict(exit=0, result="propose", layout="per-goal", subgoal="standalone", dir="docs/plan/feat-x", backlink="—",
       goals=["docs/plan/feat-x/TODO/01-one.md - [ ] 01 — One"], warn=["no revision is open in docs/plan/TODO.md"])),
 ("p10", {"docs/plan/TODO.md": INDEX("- [x] 05-old — closed")}, ["TODO.md", "feat/x"],
  dict(exit=1, result="error", prob=["no goal titles were given"], fix=["pass the Scope items as titles, after --"])),
 ("p11", {"docs/plan/TODO.md": INDEX("- [x] 05-old — closed")}, ["TODO.md", "feat/x", "--", "One", "  ", "Three"],
  dict(exit=1, result="error", prob=["title 2 is empty"])),
 ("p12", {"docs/plan/TODO.md": LEGACY, "docs/plan/grp/feat-x/TODO.md": "# old\n"}, ["TODO.md", "feat/x"],
  dict(exit=1, result="error", prob=["a plan named feat-x already exists: docs/plan/grp/feat-x/TODO.md"],
       fix=["branch feat/x has been planned before: resume that plan, or pick another branch name"])),
 ("p12b", {"docs/plan/feat-x/notes.txt": "x\n"}, ["TODO.md", "feat/x"],
  dict(exit=1, result="error", prob=["docs/plan/feat-x/ already exists, and holds no plan"])),
 ("p12c", {"docs/plan/feat-x/DO.md": "# old\n"}, ["TODO.md", "feat/x"],
  dict(exit=1, result="error", prob=["a plan named feat-x already exists: docs/plan/feat-x/DO.md"])),
 ("p13", {"docs/plan/TODO.md": LEGACY, "docs/plan/other.md": "- [ ] x\n"}, ["TODO.md", "feat/x", "--subgoal", "docs/plan/other.md:1"],
  dict(exit=1, result="error", prob=["--subgoal names docs/plan/other.md, which is not the master plan"])),
 ("p13b", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x", "--subgoal", "docs/plan/TODO.md:12"],
  dict(exit=1, result="error", prob=["docs/plan/TODO.md:12 is not a subgoal: no item line starts there"])),
 ("p13c", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x", "--subgoal", "docs/plan/TODO.md:7"],
  dict(exit=1, result="error", prob=["docs/plan/TODO.md:7 is not open: its marker is [x]"])),
 ("p13d", {"docs/plan/TODO.md": LEGACY}, ["TODO.md", "feat/x", "--subgoal", "docs/plan/TODO.md:9"],
  dict(exit=0, result="propose", backlink="docs/plan/TODO.md:10",
       warn=["docs/plan/TODO.md:9 already has a branch (feat/taken): the subgoal may have been branched before"])),
 ("p13e", {"README.md": "x\n"}, ["TODO.md", "feat/x", "--subgoal", "docs/plan/TODO.md:3"],
  dict(exit=1, result="error", prob=["there is no master plan to take a subgoal from"], fix=["pass --standalone"])),
 ("p14", {"docs/plan/TODO.md": INDEX("- [~] 09-gone — open")}, ["TODO.md", "feat/x", "--", "One"],
  dict(exit=1, result="error", prob=["revision 09-gone is open at docs/plan/TODO.md:7, but docs/plan/09-gone/_TODO.md is missing"])),
 ("p15", {"README.md": "x\n"}, ["TODO.md"], dict(raw=True, exit=2, err=["no branch name given"])),
 ("p15b", {"README.md": "x\n"}, ["TODO.md", "feat x"], dict(raw=True, exit=2, err=["cannot hold whitespace"])),
 ("p15c", {"README.md": "x\n"}, ["TODO.md", "feat/x", "--standalone", "--subgoal", "docs/plan/TODO.md:3"],
  dict(raw=True, exit=2, err=["exclude each other"])),
 ("p15d", {"README.md": "x\n"}, ["TODO.md", "feat/x", "--subgoal", "docs/plan/TODO.md"], dict(raw=True, exit=2, err=["--subgoal takes <file>:<line>"])),
 ("p15e", {"README.md": "x\n"}, ["TODO.md", "-x"], dict(raw=True, exit=2, err=["unknown option"])),
 ("p16", {}, "nogit", dict(exit=1, result="error", prob=["not inside a git repository"])),
 ("p17", {"docs/plan/TODO.md": INDEX("- [x] 05-old — closed")}, ["TODO.md", "feat/x", "--"] + [f"T{i}" for i in range(1, 101)],
  dict(exit=0, result="propose", goals_first="docs/plan/feat-x/TODO/001-t1.md - [ ] 001 — T1",
       goals_last="docs/plan/feat-x/TODO/100-t100.md - [ ] 100 — T100")),
 ("p19", {"docs/plan/DO.md": INDEX("- [~] 07-rev — open"), "docs/plan/07-rev/_DO.md": REVMASTER.format(label="07-rev")},
  ["DO.md", "fix/y", "--subgoal", "docs/plan/07-rev/_DO.md:11", "--", "Only"],
  dict(exit=0, result="propose", dir="docs/plan/07-rev/fix-y", index="docs/plan/07-rev/fix-y/DO.md",
       goals=["docs/plan/07-rev/fix-y/DO/01-only.md - [ ] 01 — Only"], backlink="docs/plan/07-rev/_DO.md:11")),
 ("p20", {"README.md": "x\n"}, "awk127", dict(raw=True, exit=3, err=["propose-branch-plan.sh: awk failed", "hint: awk exited 127"])),
 ("p21", {"docs/plan/DO.md": "# master\n\n- [ ] a\n"}, ["TODO.md", "feat/x"],
  dict(exit=0, result="propose", subgoal="standalone", warn=["there is no docs/plan/TODO.md, but docs/plan/DO.md exists"])),
 ("p24", {"docs/plan/TODO.md": INDEX("- [~] 07-rev — open"), "docs/plan/07-rev/_TODO.md": REVMASTER.format(label="07-rev")},
  "integration", dict()),
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
    elif args == "awk127": env["PATH"] = AWK127 + ":" + env["PATH"]; args = ["TODO.md", "feat/x"]
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
    for k in ("result", "layout", "revision", "subgoal", "dir", "index", "backlink"):
        if k in exp and one(k) != exp[k]: probs.append(f"{k}: want {exp[k]!r} got {one(k)!r}")
    if "goals" in exp and allv("goals") != exp["goals"]: probs.append(f"goals {allv('goals')} want {exp['goals']}")
    if "goals_first" in exp and (not allv("goals") or allv("goals")[0] != exp["goals_first"]): probs.append(f"first goal {allv('goals')[:1]}")
    if "goals_last" in exp and (not allv("goals") or allv("goals")[-1] != exp["goals_last"]): probs.append(f"last goal {allv('goals')[-1:]}")
    if "warnings" in exp and allv("warnings") != exp["warnings"]: probs.append(f"warnings {allv('warnings')}")
    if "cand" in exp:
        got = allv("candidates")
        if [c.split(" ", 1)[0] for c in got] != [c.split(" ", 1)[0] for c in exp["cand"]] or any(e not in got for e in exp["cand"] if " " in e):
            probs.append(f"candidates {got} want {exp['cand']}")
    for k, key in (("prob", "problem"), ("fix", "fix"), ("warn", "warnings")):
        for w in exp.get(k, []):
            if not any(w in v for v in allv(key)): probs.append(f"{key} lacks {w!r}: {allv(key)}")
    if len(allv("problem")) != len(allv("fix")): probs.append(f"{len(allv('problem'))} problems but {len(allv('fix'))} fixes")
    if exp.get("result") in ("propose", "ask") and allv("problem"): probs.append("a problem on a " + exp["result"])
    if exp.get("result") == "error" and not allv("problem"): probs.append("an error without a problem")
    if "msg" in exp and exp["msg"] not in one("message"): probs.append(f"message lacks {exp['msg']!r}")
    for k in KEYS:
        for v in rep[k]:
            if v.startswith("/") or W in v: probs.append(f"an absolute path in {k}: {v[:80]!r}")
    return probs

def integration(shell, script):
    """Write what a proposal lists, as /new-branch will, then read it back with the readers."""
    probs = []
    shutil.rmtree(INT, ignore_errors=True)
    r = sh(["git", "clone", "-q", "-b", "case/p24", FX, INT], W)
    if r.returncode: return [f"clone failed: {r.stderr.strip()}"]
    sh(["git", "checkout", "-q", "-b", "feat/plan-dirs"], INT)
    args = ["TODO.md", "feat/plan-dirs", "--subgoal", "docs/plan/07-rev/_TODO.md:9", "--", "Write the spec", "Build it", LONG]
    r = sh([shell, script, *args], INT); rep, _ = parse(r.stdout)
    if r.returncode or not rep or rep["result"] != ["propose"]: return [f"no proposal: {r.stdout[:200]!r}"]
    index, sub = rep["index"][0], rep["subgoal"][0]
    lines = []
    for g in rep["goals"]:
        path, line = g.split(" ", 1); lines.append(line)
        title = re.sub(r"^- \[ \] ", "", line)
        os.makedirs(os.path.dirname(f"{INT}/{path}"), exist_ok=True)
        open(f"{INT}/{path}", "w").write(f"# {title}\n\n**Goal**: [ ]\n")
    os.makedirs(os.path.dirname(f"{INT}/{index}"), exist_ok=True)
    open(f"{INT}/{index}", "w").write("# feat/plan-dirs\n\n**Status**: active\n**Created**: 2026-10-10\n**Revision**: 07-rev\n"
        f"**Subgoal**: {re.sub(r'^[^ ]+ - .. ', '', sub)}\n**Layout**: per-goal\n\n## Goals\n\n" + "".join(l + "\n" for l in lines))
    bf, bl = rep["backlink"][0].rsplit(":", 1)
    src = open(f"{INT}/{bf}").read().split("\n"); src.insert(int(bl), "  > **Branch:** feat/plan-dirs")
    open(f"{INT}/{bf}", "w").write("\n".join(src))
    lp = sh([shell, SD + "/locate-plan.sh", "TODO.md"], INT); lrep, _ = parse(lp.stdout)
    want = {"result": "found", "rung": "2", "plan": index, "layout": "per-goal",
            "goal-file": rep["goals"][0].split(" ", 1)[0], "next": f"{index}:11 {lines[0]}"}
    for k, v in want.items():
        if not lrep or lrep.get(k, [""])[0] != v: probs.append(f"locate-plan.sh {k}: want {v!r} got {(lrep or {}).get(k)}")
    ck = sh([shell, SD + "/check-plan-index.sh", "TODO.md", index], INT); crep, _ = parse(ck.stdout)
    if ck.returncode or not crep or crep["result"] != ["clean"]: probs.append(f"check-plan-index.sh: {ck.stdout[:300]!r}")
    pb = sh([shell, script, *args], INT); prep, _ = parse(pb.stdout)
    if not prep or not any("a plan named feat-plan-dirs already exists" in v for v in prep.get("problem", [])):
        probs.append(f"a second proposal is not refused: {pb.stdout[:200]!r}")
    sub2 = sh([shell, script, "TODO.md", "feat/other", "--", "x"], INT); s2, _ = parse(sub2.stdout)
    if not s2 or any(c.startswith("docs/plan/07-rev/_TODO.md:9 ") for c in s2.get("candidates", [])):
        probs.append(f"the backlinked subgoal is still a candidate: {sub2.stdout[:300]!r}")
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
    d = HERE + "/mutants"; tmp = W + "/pbp-mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; root = f"{tmp}/{name}"; out = root + "/propose-branch-plan.sh"
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
    want = [a for a in sys.argv[1:] if re.match(r"^p\d", a)]
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
