"""check-plan-index.sh suite: runs the script directly on a fixture repository built here, one
plan directory per case, and grades every report. Writes only under $LOCATE_PLAN_WORK,
which must lie outside the repository (the rule dev/locate-plan/ uses, for the same
reasons: the fixture is a git repository, and the name must not decode to this one).

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--script PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

Every case runs twice under each shell found and must print the same thing each time.
Every report is checked for key order, exit code, problem and fix text, one fix per
problem, no absolute paths, and that the fixture is left untouched. --mutants applies each
patch in mutants/ to a copy of the script and its library, scripts/lib/plan-rules.sh, and
runs the suite on it once: each must fail it, and a patch that no longer applies is
reported stale. A patch names its file relative to scripts/."""
import hashlib, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCRIPT = REPO + "/plugins/workflow-claude/scripts/check-plan-index.sh"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
LIB = os.path.dirname(SCRIPT) + "/lib/plan-rules.sh"
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
FX, NOGIT = W + "/cpi", W + "/cpi-nogit"
SHELLS = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if os.access(s, os.X_OK)]
if "--once" in sys.argv: SHELLS = SHELLS[:1]
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
AWK127 = f"{W}/bin/{h('cpi-awk-127')}"
KEYS = ["result", "plan", "goals", "open", "warnings", "problem", "fix", "message"]
EQUIVALENT = set()

def idx(*lines, layout="per-goal", title="p"):
    head = f"# {title}\n\n**Status**: active\n" + (f"**Layout**: {layout}\n" if layout else "") + "\n## Goals\n\n"
    return head + "".join(l + "\n" for l in lines)        # first item on line 8 (7 with no layout)
def gf(nn, title, marker, *items):
    return f"# {nn} — {title}\n\n**Goal**: [{marker}]\n\n" + "".join(l + "\n" for l in items)   # items from line 5

# id, files under docs/plan/<id>/, extra arguments (default: TODO.md docs/plan/<id>), expectations
C = [
 ("k01", {"TODO.md": idx("- [x] 01 — One", "- [~] 02 — Two"),
          "TODO/01-one.md": gf("01", "One", "x", "- [x] a"),
          "TODO/02-two.md": gf("02", "Two", "~", "- [x] a", "- [ ] b")}, None,
  dict(exit=0, result="clean", goals="2", open=["docs/plan/k01/TODO.md:9", "docs/plan/k01/TODO/02-two.md:6"],
       msg="2 items are open")),
 ("k02", {"TODO.md": idx("- [x] 01 — One"), "TODO/01-one.md": gf("01", "One", "x", "- [x] a", "- [-] b")}, None,
  dict(exit=0, result="clean", goals="1", open=[], msg="0 items are open")),
 ("k02b", {"TODO.md": idx("- [~] 01 — One"), "TODO/01-one.md": gf("01", "One", "~", "- [x] a")}, None,
  dict(exit=0, result="clean", open=["docs/plan/k02b/TODO.md:8"], msg="1 item is open")),
 ("k03", {"TODO.md": idx("- [ ] 01 — One"), "TODO/01-one.md": gf("01", "One", "~", "- [ ] a")}, None,
  dict(exit=1, result="drift", nprob=1, prob=["docs/plan/k03/TODO.md:8 has [ ] but docs/plan/k03/TODO/01-one.md says **Goal**: [~]"],
       fix=["the goal file is the source of truth: write docs/plan/k03/TODO.md:8 as `- [~] 01 — One`"])),
 ("k04", {"TODO.md": idx("- [~] 02 — Two"), "TODO/2-two.md": gf("2", "Two", "~", "- [ ] a")}, None,
  dict(exit=1, result="drift", nprob=1, prob=["goal 02 has no file matching docs/plan/k04/TODO/02-*.md"],
       fix=["git mv docs/plan/k04/TODO/2-two.md docs/plan/k04/TODO/02-two.md"], nofix=["create"])),
 ("k05", {"TODO.md": idx("- [ ] 01 — Write the spec")}, None,
  dict(exit=1, result="drift", nprob=1,
       fix=["create docs/plan/k05/TODO/01-write-the-spec.md, or correct the number on docs/plan/k05/TODO.md:8"])),
 ("k06", {"TODO.md": idx("- [ ] 01 — One"), "TODO/01-one.md": gf("01", "One", " "), "TODO/01-uno.md": gf("01", "Uno", " ")}, None,
  dict(exit=1, result="drift", nprob=1, prob=["goal 01 matches several files in docs/plan/k06/TODO/: 01-one.md, 01-uno.md"],
       fix=["which copy is stale is your call"])),
 ("k07", {"TODO.md": idx("- [x] 01 — One"), "TODO/01-one.md": gf("01", "One", "x", "- [x] a"),
          "TODO/04-later-work.md": gf("04", "Later work", " ")}, None,
  dict(exit=1, result="drift", nprob=1, prob=["docs/plan/k07/TODO/04-later-work.md is a goal file no index line claims"],
       fix=["add `- [ ] 04 — Later work` to docs/plan/k07/TODO.md, from its heading and **Goal**, or git rm docs/plan/k07/TODO/04-later-work.md"])),
 ("k08", {"TODO.md": idx("- [x] 01 — One"), "TODO/01-one.md": gf("01", "One", "x"), "TODO/05-x.md": "- [ ] a\n"}, None,
  dict(exit=1, result="drift", nprob=1, fix=["add `- [ ] 05 — <its title>` to docs/plan/k08/TODO.md"])),
 ("k09", {"TODO.md": idx("- [x] 01 — One", "- [ ] Add tests"), "TODO/01-one.md": gf("01", "One", "x"),
          "TODO/02-add-tests.md": gf("02", "Add tests", " ")}, None,
  dict(exit=1, result="drift", nprob=1, prob=["docs/plan/k09/TODO.md:9 has no goal number: `- [ ] Add tests`"],
       fix=["number it 02 to match its goal file docs/plan/k09/TODO/02-add-tests.md"], nofix=["no index line claims"])),
 ("k10", {"TODO.md": idx("- [ ] 01 — One", "- [~] 01 — Uno"), "TODO/01-one.md": gf("01", "One", " ")}, None,
  dict(exit=1, result="drift", nprob=1, prob=["goal number 01 is on lines 8 and 9 of docs/plan/k10/TODO.md"],
       fix=["give each other one an unused number, from 02 on, and its goal file"])),
 ("k11", {"TODO.md": idx("- [~] 01 — One"), "TODO/01-one.md": "# 01 — One\n\n- [ ] a\n"}, None,
  dict(exit=1, result="drift", nprob=1, prob=["docs/plan/k11/TODO/01-one.md has no **Goal** line"],
       fix=["add `**Goal**: [~]` under its heading, the marker docs/plan/k11/TODO.md:8 has"])),
 ("k12", {"TODO.md": idx("- [x] 01 — One"), "TODO/01-one.md": gf("01", "One", "x", "- [ ] a", "- [!] b", "- [x] c")}, None,
  dict(exit=1, result="drift", nprob=1, prob=["docs/plan/k12/TODO/01-one.md says **Goal**: [x] but has open items, on lines 5, 6"],
       fix=["close each item, or reopen the goal (`**Goal**: [~]` in docs/plan/k12/TODO/01-one.md, then docs/plan/k12/TODO.md:8)"])),
 ("k12b", {"TODO.md": idx("- [x] 01 — One"), "TODO/01-one.md": gf("01", "One", "x", "- [x] a", "- [~] b")}, None,
  dict(exit=1, result="drift", nprob=1, prob=["has open items, on line 6"])),
 # A legacy (one-file) plan: nothing to drift, so only its open items, each with its heading.
 ("k13", {"TODO.md": idx("- [ ] One", layout="")}, None,
  dict(exit=0, result="clean", goals="1", openx=["docs/plan/k13/TODO.md:7 - [ ] One — under ## Goals"],
       msg="is a one-file plan, so nothing can drift; 1 item is open")),
 ("k13b", {"TODO.md": idx("- [x] One", "  - [ ] a", "  - [x] b", "- [-] Two", "- [~] Three", "  - [!] c", layout="")}, None,
  dict(exit=0, result="clean", goals="3", open=["docs/plan/k13b/TODO.md:8", "docs/plan/k13b/TODO.md:11", "docs/plan/k13b/TODO.md:12"],
       msg="3 items are open")),
 ("k13c", {"TODO.md": idx("- [x] One", "```", "- [ ] example", "```", layout="")}, None,
  dict(exit=0, result="clean", goals="1", open=[], msg="0 items are open")),
 ("k13d", {"TODO.md": "# p\n\n**Status**: active\n\n- [ ] Before\n\n## First\n\n- [x] Done\n\n## Second\n\n  - [ ] After\n"}, None,
  dict(exit=0, result="clean", goals="2", openx=["docs/plan/k13d/TODO.md:5 - [ ] Before",
                                                "docs/plan/k13d/TODO.md:13   - [ ] After — under ## Second"])),
 ("k13e", {"TODO.md": idx("- [ ] One", "- [y] Bad", layout="")}, None,
  dict(exit=0, result="clean", open=["docs/plan/k13e/TODO.md:7"],
       warn=["docs/plan/k13e/TODO.md:8 looks like an item but its marker is not one of"])),
 ("k13f", {"DO.md": idx("- [x] One", "- [ ] Two", layout="")}, ["DO.md", "docs/plan/k13f/DO.md"],
  dict(exit=0, result="clean", goals="2", open=["docs/plan/k13f/DO.md:8"])),
 ("k13g", {"../TODO.md": "# Master\n\n**Layout**: revisions\n\n## Revisions\n\n- [~] r1\n"}, ["TODO.md", "docs/plan/TODO.md"],
  dict(exit=1, result="error", goals="—", open=[], prob=["docs/plan/TODO.md is a revisions index: its items are revisions, not goals"],
       fix=["check the open revision's plan instead"])),
 ("k14", {"TODO.md": idx("- [ ] 01 — One", layout="pergoal")}, None,
  dict(exit=1, result="error", prob=["has `**Layout**: pergoal`, which is not valid there"])),
 ("k15", {}, ["TODO.md", "docs/plan/nope"],
  dict(exit=1, result="error", plan="docs/plan/nope", prob=["docs/plan/nope does not exist"])),
 ("k16", {}, ["TODO.md", "docs/plan/k01/TODO.md"], dict(exit=0, result="clean", plan="docs/plan/k01/TODO.md")),
 ("k16b", {}, ["TODO.md", "docs/plan/k01/"], dict(exit=0, result="clean", plan="docs/plan/k01/TODO.md")),
 ("k17", {"DO.md": idx("- [x] 01 — One", "- [ ] 02 — Two"), "DO/01-one.md": gf("01", "One", "x", "- [x] a"),
          "DO/02-two.md": gf("02", "Two", " ", "- [ ] a")}, ["DO.md", "docs/plan/k17"],
  dict(exit=0, result="clean", plan="docs/plan/k17/DO.md", open=["docs/plan/k17/DO.md:9", "docs/plan/k17/DO/02-two.md:5"])),
 ("k18", {}, "nogit", dict(exit=1, result="error", prob=["not inside a git repository"])),
 ("k19", {}, "chmod", dict(exit=1, result="error", prob=["docs/plan/k01/TODO/01-one.md cannot be read"],
                           fix=["chmod u+r docs/plan/k01/TODO/01-one.md"])),
 ("k20", {}, ["TODO.md"], dict(raw=True, exit=2, err=["no index given"])),
 ("k20b", {}, "abs", dict(exit=1, result="error", prob=["the index was given as an absolute path"])),
 ("k21", {}, "awk127", dict(raw=True, exit=3, err=["check-plan-index.sh: awk failed", "hint: awk exited 127"])),
 ("k22", {"TODO.md": idx("- [ ] 01 — One", "```", "- [ ] 99 — Fake", "```"),
          "TODO/01-one.md": gf("01", "One", " ", "- [ ] a", "```", "- [ ] fenced", "```")}, None,
  dict(exit=0, result="clean", goals="1", open=["docs/plan/k22/TODO.md:8", "docs/plan/k22/TODO/01-one.md:5"])),
 ("k23", {"TODO.md": idx("- [~] 01 — One"), "TODO/01-one.md": gf("01", "One", "~", "- [X] a")}, None,
  dict(exit=0, result="clean", warn=["docs/plan/k23/TODO/01-one.md:5 looks like an item but its marker is not one of"])),
 ("k24", {"TODO.md": idx("- [x] 03 — A", "- [ ] 03a — A, part two"), "TODO/03-a.md": gf("03", "A", "x"),
          "TODO/03a-a-part-two.md": gf("03a", "A, part two", " ")}, None, dict(exit=0, result="clean", goals="2")),
 ("k25", {"TODO.md": idx("- [ ] 2 — Two"), "TODO/2-two.md": gf("2", "Two", " ")}, None, dict(exit=0, result="clean")),
 ("k25b", {"TODO.md": idx("- [ ] 02 — Two", "- [ ] 2 — Deux"), "TODO/02-two.md": gf("02", "Two", " ")}, None,
  dict(exit=1, result="drift", nprob=1, prob=["goal number 02 is on lines 8 and 9 of docs/plan/k25b/TODO.md"])),
 ("k26", {"TODO.md": idx("- [-] 01 — One"), "TODO/01-one.md": gf("01", "One", "-", "- [ ] a")}, None,
  dict(exit=0, result="clean", open=["docs/plan/k26/TODO/01-one.md:5"])),
 ("k27", {"TODO.md": idx("- [x] 01 — One", "- [ ] 03 — Three", "- [ ] 03 — Again", "- [ ] Unnumbered thing"),
          "TODO/01-one.md": gf("01", "One", "x"), "TODO/03-three.md": gf("03", "Three", " "),
          "TODO/09-stray.md": gf("09", "Stray", " ")}, None,
  dict(exit=1, result="drift", nprob=3, fix=["number it 10, the next free number", "from 11 on"])),
 ("k28", {"TODO.md": idx("- [x] 01 — One"), "TODO/01-one.md": gf("01", "One", "x"), "TODO/README.md": "notes\n",
          "TODO/notes.txt": "x\n"}, None, dict(exit=0, result="clean")),
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
    for cid, files, _, _ in C:
        for rel, text in files.items():
            p = f"{FX}/docs/plan/{cid}/{rel}"; os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(text)
    git("add", "-A"); git("commit", "-q", "-m", "fixture")
    os.makedirs(NOGIT, exist_ok=True)
    os.makedirs(AWK127, exist_ok=True)
    open(AWK127 + "/awk", "w").write("#!/bin/sh\nexit 127\n"); os.chmod(AWK127 + "/awk", 0o755)

def parse(out):
    rep, order, key = {}, [], None
    for line in out.splitlines():
        if line.startswith("  ") and key: rep[key].append(line[2:]); continue
        m = re.match(r"^([a-z-]+): (.*)$", line)
        if not m: return None, order
        key = m.group(1); order.append(key); rep[key] = [m.group(2)]
    return rep, order

def run(cid, args, shell):
    env = dict(os.environ); cwd = FX; chmod = None
    if args is None: args = ["TODO.md", f"docs/plan/{cid}"]
    elif args == "nogit": cwd = NOGIT; env["GIT_CEILING_DIRECTORIES"] = W; args = ["TODO.md", "docs/plan/k01"]
    elif args == "chmod": chmod = f"{FX}/docs/plan/k01/TODO/01-one.md"; args = ["TODO.md", "docs/plan/k01"]
    elif args == "abs": args = ["TODO.md", f"{FX}/docs/plan/k01"]
    elif args == "awk127": env["PATH"] = AWK127 + ":" + env["PATH"]; args = ["TODO.md", "docs/plan/k01"]
    if chmod: os.chmod(chmod, 0)
    try: r = sh([shell, SCRIPT, *args], cwd, env)
    finally:
        if chmod: os.chmod(chmod, 0o644)
    return r

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
    one = lambda k: rep[k][0] if len(rep[k]) == 1 else "\n".join(rep[k])
    allv = lambda k: [] if rep[k] == ["—"] else rep[k]
    for k in ("result", "goals", "plan"):
        if k in exp and one(k) != exp[k]: probs.append(f"{k}: want {exp[k]!r} got {one(k)!r}")
    if "open" in exp:
        got = [l.split(" ", 1)[0] for l in allv("open")]
        if got != exp["open"]: probs.append(f"open {got} want {exp['open']}")
    if "openx" in exp and allv("open") != exp["openx"]: probs.append(f"open {allv('open')} want exactly {exp['openx']}")
    for k, key in (("prob", "problem"), ("fix", "fix"), ("warn", "warnings")):
        for w in exp.get(k, []):
            if not any(w in v for v in allv(key)): probs.append(f"{key} lacks {w!r}: {allv(key)}")
    for w in exp.get("nofix", []):
        if any(w in v for v in allv("fix")): probs.append(f"fix has {w!r}")
    if len(allv("problem")) != len(allv("fix")): probs.append(f"{len(allv('problem'))} problems but {len(allv('fix'))} fixes")
    if "nprob" in exp and len(allv("problem")) != exp["nprob"]: probs.append(f"{len(allv('problem'))} problems, want {exp['nprob']}")
    if exp.get("result") in ("clean",) and allv("problem"): probs.append("a problem on a clean result")
    if exp.get("result") in ("drift", "error") and not allv("problem"): probs.append(f"{exp['result']} without a problem")
    if "msg" in exp and exp["msg"] not in one("message"): probs.append(f"message lacks {exp['msg']!r}: {one('message')!r}")
    for k in KEYS:
        for v in rep[k]:
            if v.startswith("/") or W in v: probs.append(f"an absolute path in {k}: {v[:80]!r}")
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
    d = HERE + "/mutants"; tmp = W + "/cpi-mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; root = f"{tmp}/{name}"; out = root + "/check-plan-index.sh"
        os.makedirs(root + "/lib"); shutil.copy2(SCRIPT, out); shutil.copy2(LIB, root + "/lib/plan-rules.sh")
        ap = sh(["patch", "-s", "-F0", "-p1", "-d", root, "-i", f"{d}/{fn}"], tmp)
        if ap.returncode:
            bad += 1; print(f"STALE  {name}: the patch no longer applies ({(ap.stdout + ap.stderr).strip()[:120]})"); continue
        r = sh([sys.executable, "-I", os.path.abspath(__file__), "--once", "--script", out], HERE)
        killed = r.returncode != 0
        why = next((l for l in r.stdout.splitlines() if l.startswith("FAIL") or (l.startswith("static:") and l != "static: ok")), "")
        if name in EQUIVALENT:
            ok = not killed; print(f"{'EQUIV ' if ok else 'CHANGED'} {name}")
        else:
            ok = killed; print(f"{'KILLED' if ok else 'SURVIVED'} {name}" + (f"  ({why[:90]})" if ok else ""))
        bad += not ok
    shutil.rmtree(tmp); print(f"\n{bad} failing"); sys.exit(1 if bad else 0)

def main():
    if "--mutants" in sys.argv: mutants()
    want = [a for a in sys.argv[1:] if re.match(r"^k\d", a)]
    build()
    head = git("rev-parse", "HEAD")
    st = static_checks(); print("static: " + ("ok" if not st else "; ".join(st)))
    fails = len(st)
    for cid, _, args, exp in C:
        if want and cid not in want: continue
        outs, probs = set(), []
        for shell in SHELLS:
            for _ in range(1 if "--once" in sys.argv else 2):
                r = run(cid, args, shell); outs.add((r.returncode, r.stdout, r.stderr))
                probs += [p for p in grade(exp, r) if p not in probs]
                if git("status", "--porcelain") or git("rev-parse", "HEAD") != head: probs.append("the fixture changed")
        if len(outs) > 1: probs.append("output differs between runs or shells")
        print(f"{'PASS' if not probs else 'FAIL'} {cid:<5} " + "; ".join(probs))
        if "-v" in sys.argv: print("".join(o[1] + o[2] for o in sorted(outs)))
        fails += bool(probs)
    print(f"\n{fails} failing"); sys.exit(1 if fails else 0)

main()
