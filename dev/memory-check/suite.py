"""memory-check.sh suite: runs the script on fixture repositories built here, one per kind of
root plan, and grades every report against sizes computed here from the files themselves.
Writes only under $LOCATE_PLAN_WORK, which must lie outside the repository (the rule
dev/locate-plan/ uses, for the same reasons: each fixture is a git repository, and the name
must not decode to this one).

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--script PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

Every case runs twice under each shell found and must print the same thing each time.
Every report is checked for key order, exit code, no absolute paths, one fix per problem,
no problem unless the result is an error, and that its fixture is left untouched: no file
changed, added or removed, and HEAD where it was. A measured report is checked line for
line: each file's bytes, words, lines and ≈ tokens, their order, each branch's layout and
totals, the total, every warning and the message. --mutants applies each patch in mutants/
to a copy of the script and its library, scripts/lib/plan-rules.sh, and runs the suite on it
once: each must fail it, and a patch that no longer applies is reported stale. A patch
names its file relative to scripts/."""
import hashlib, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCRIPT = REPO + "/plugins/workflow-coding/scripts/memory-check.sh"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
LIB = os.path.dirname(SCRIPT) + "/lib/plan-rules.sh"
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
FX = W + "/mc"
REV, LEG, TWO, ZERO, NOROOT, BROKEN, DOM, NOGIT = (f"{FX}/{n}" for n in ("rev", "leg", "two", "zero", "noroot", "broken", "do", "nogit"))
SHELLS = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if os.access(s, os.X_OK)]
if "--once" in sys.argv: SHELLS = SHELLS[:1]
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
AWK127 = f"{W}/bin/{h('mc-awk-127')}"
KEYS = ["result", "root", "layout", "revision", "threshold", "files", "branches", "total", "candidates",
        "warnings", "problem", "fix", "message"]
EQUIVALENT = set()

LINE = b"lorem ipsum dolor sit amet\n"
def pad(head, n):  # head, then filler lines, to exactly n bytes, ending in a newline
    b = head.encode()
    while len(b) + len(LINE) <= n: b += LINE
    if n - len(b): b += b"x" * (n - len(b) - 1) + b"\n"
    assert len(b) == n, (head, n, len(b))
    return b
def idx(title, *items, layout="per-goal", status="active"):
    return (f"# {title}\n\n**Status**: {status}\n" + (f"**Layout**: {layout}\n" if layout else "")
            + "\n## Goals\n\n" + "".join(i + "\n" for i in items)).encode()
def gfile(nn, title, n): return pad(f"# {nn} — {title}\n\n**Goal**: [ ]\n\n- [ ] a\n\n", n)
def index(*lines): return ("# Plan\n\n**Layout**: revisions\n\n## Revisions\n\n" + "".join(l + "\n" for l in lines)).encode()

# The fixture repositories: files under each, relative to its root.
R = "docs/plan/07-rev"
FILES = {
  # A revisions root: 07-rev open, 05-old closed. 01-alpha is 1716 tokens, for the threshold's
  # boundary; chore-bad and 02-beta are the same size, for the order of a tie; fix-one is over
  # the default threshold; the spec, TODO/README.md and the stray DO.md are not plan files.
  REV: {"docs/plan/TODO.md": index("- [x] 05-old — the old one — closed. See `docs/plan/05-old/_TODO.md`.",
                                   "- [~] 07-rev — the open one"),
        f"{R}/_TODO.md": pad("# Revision 07-rev\n\n**Status**: open\n\n## Subgoals\n\n- [~] 1. Big\n  > **Branch:** feat/big\n\n", 40000),
        f"{R}/feat-big/TODO.md": idx("feat/big", "- [~] 01 — Alpha", "- [ ] 02 — Beta"),
        f"{R}/feat-big/TODO/01-alpha.md": gfile("01", "Alpha", 4004),
        f"{R}/feat-big/TODO/02-beta.md": gfile("02", "Beta", 300),
        f"{R}/feat-big/TODO/README.md": b"notes about the goals\n",
        f"{R}/feat-big/spec.md": pad("# A spec\n\n", 9000),
        f"{R}/fix-one/TODO.md": pad("# fix/one\n\n**Status**: active\n\n## Goals\n\n- [ ] One\n\n", 20000),
        f"{R}/fix-one/DO.md": b"stray\n",
        f"{R}/chore-bad/TODO.md": pad("# chore/bad\n\n**Status**: active\n**Layout**: revisions\n\n## Goals\n\n- [ ] One\n\n", 300),
        f"{R}/feat-empty/TODO.md": idx("feat/empty", "- [ ] 01 — Later"),
        "docs/plan/05-old/_TODO.md": pad("# Revision 05-old\n\n**Status**: closed — 2026-01-01\n\n", 6000),
        "docs/plan/05-old/feat-old/TODO.md": pad("# feat/old\n\n**Status**: merged — PR #1 — 2026-01-01\n\n", 18000),
        "docs/plan/05-old/feat-old/notes.md": b"notes\n"},
  # A legacy root: the root plan is the master; branch plans flat, grouped, and filed into a
  # closed revision's directory, whose _TODO.md is that revision's, not this tree's.
  LEG: {"docs/plan/TODO.md": b"# Plan\n\n## Subgoals \xe2\x80\x94 revision 01-x\n\n- [~] Do a\n  > **Branch:** feat/a\n",
        "docs/plan/feat-a/TODO.md": pad("# feat/a\n\n**Status**: active\n\n## Goals\n\n- [ ] One\n\n", 24000),
        "docs/plan/feat-c/TODO.md": idx("feat/c", "- [ ] One", layout=""),
        "docs/plan/02-arch/_TODO.md": pad("# Revision 02-arch\n\n", 5000),
        "docs/plan/02-arch/feat-z/TODO.md": pad("# feat/z\n\n**Status**: merged — PR #2 — 2026-01-02\n\n", 3000),
        "docs/plan/group/03-x/feat-y/TODO.md": idx("feat/y", "- [x] One", layout="legacy")},
  TWO: {"docs/plan/TODO.md": index("- [~] 03-a — a", "- [~] 04-b — b"),
        "docs/plan/03-a/_TODO.md": pad("# Revision 03-a\n\n", 800),
        "docs/plan/04-b/_TODO.md": pad("# Revision 04-b\n\n", 900),
        "docs/plan/04-b/feat-q/TODO.md": idx("feat/q", "- [ ] One", layout="single-file")},
  ZERO: {"docs/plan/TODO.md": index("- [x] 01-done — d — closed. See `docs/plan/01-done/_TODO.md`.")},
  NOROOT: {"docs/plan/05-old/_TODO.md": pad("# Revision 05-old\n\n", 1000),
           "docs/plan/05-old/feat-old/TODO.md": pad("# feat/old\n\n", 2000)},
  BROKEN: {"docs/plan/TODO.md": index("- [~] 09-gone — g")},
  # The DO model: _DO.md, DO.md and DO/; the TODO-model files beside them are not its.
  DOM: {"docs/plan/DO.md": index("- [~] 01-r — r"),
        "docs/plan/01-r/_DO.md": pad("# Revision 01-r\n\n**Status**: open\n\n", 2000),
        "docs/plan/01-r/feat-x/DO.md": idx("feat/x", "- [ ] 01 — A"),
        "docs/plan/01-r/feat-x/DO/01-a.md": gfile("01", "A", 1200),
        "docs/plan/01-r/feat-x/TODO.md": b"stray\n",
        "docs/plan/01-r/feat-x/TODO/01-a.md": b"stray\n"},
}

# What a measured report must list: (path, access, branch directory, its layout).
def bp(path, layout): return (path, "whole", os.path.dirname(path), layout)
def gp(path): return (path, "whole", os.path.dirname(os.path.dirname(path)), "per-goal")
def ln(path): return (path, "by line", "", "")
REV_OPEN = [ln("docs/plan/TODO.md"), ln(f"{R}/_TODO.md"), bp(f"{R}/feat-big/TODO.md", "per-goal"),
            gp(f"{R}/feat-big/TODO/01-alpha.md"), gp(f"{R}/feat-big/TODO/02-beta.md"),
            bp(f"{R}/fix-one/TODO.md", "single-file"), bp(f"{R}/chore-bad/TODO.md", "single-file"),
            bp(f"{R}/feat-empty/TODO.md", "per-goal")]
BAD = (f"{R}/chore-bad/TODO.md has a **Layout** header that is not valid there, so it was measured as one file; "
       "check-plan-index.sh says why")
REV_OLD = [ln("docs/plan/05-old/_TODO.md"), bp("docs/plan/05-old/feat-old/TODO.md", "single-file")]
LEG_ALL = [ln("docs/plan/TODO.md"), bp("docs/plan/feat-a/TODO.md", "single-file"), bp("docs/plan/feat-c/TODO.md", "single-file"),
           bp("docs/plan/02-arch/feat-z/TODO.md", "single-file"), bp("docs/plan/group/03-x/feat-y/TODO.md", "single-file")]
LEG_ARCH = [ln("docs/plan/02-arch/_TODO.md"), bp("docs/plan/02-arch/feat-z/TODO.md", "single-file")]
TWO_B = [ln("docs/plan/04-b/_TODO.md"), bp("docs/plan/04-b/feat-q/TODO.md", "single-file")]
DO_OPEN = [ln("docs/plan/DO.md"), ln("docs/plan/01-r/_DO.md"), bp("docs/plan/01-r/feat-x/DO.md", "per-goal"),
           gp("docs/plan/01-r/feat-x/DO/01-a.md")]

def M(entries, revision, where, root="docs/plan/TODO.md", layout="revisions", th=2000, extra=()):
    return dict(exit=0, result="measured", root=root, layout=layout, revision=revision, threshold=f"≈{th} tokens",
                measure=(entries, where, th, list(extra)))

# id, fixture, arguments (or a special run), expectations
C = [
 ("m01", REV, ["TODO.md"], M(REV_OPEN, "07-rev", "revision 07-rev", extra=[BAD])),
 ("m02", REV, ["TODO.md", "--threshold", "1715"], M(REV_OPEN, "07-rev", "revision 07-rev", th=1715, extra=[BAD])),
 ("m03", REV, ["TODO.md", "--threshold", "1716"], M(REV_OPEN, "07-rev", "revision 07-rev", th=1716, extra=[BAD])),
 ("m04", REV, ["TODO.md", "--threshold", "100000"], M(REV_OPEN, "07-rev", "revision 07-rev", th=100000, extra=[BAD])),
 ("m05", REV, ["TODO.md", "--threshold", "0400"], M(REV_OPEN, "07-rev", "revision 07-rev", th=400, extra=[BAD])),
 ("m06", REV, ["TODO.md", "--", "05-old"], M(REV_OLD, "05-old", "revision 05-old")),
 ("m07", REV, ["TODO.md", "05-old", "--threshold", "10"], M(REV_OLD, "05-old", "revision 05-old", th=10)),
 ("m08", REV, ["DO.md"], dict(exit=0, result="none", root="—", layout="none", revision="—",
                              msg="There is no root plan, docs/plan/DO.md, so no revision is open")),
 ("m09", LEG, ["TODO.md"], M(LEG_ALL, "—", "docs/plan/, under a legacy root plan", layout="legacy")),
 ("m10", LEG, ["TODO.md", "--", "02-arch"], M(LEG_ARCH, "02-arch", "revision 02-arch", layout="legacy")),
 ("m11", TWO, ["TODO.md"], dict(exit=0, result="ask", layout="revisions", revision="—", cand=["03-a", "04-b"],
                                msg="2 revisions are open; pass the one to measure as the label, after --.")),
 ("m12", TWO, ["TODO.md", "--", "04-b"], M(TWO_B, "04-b", "revision 04-b")),
 ("m13", ZERO, ["TODO.md"], dict(exit=0, result="none", root="docs/plan/TODO.md", layout="revisions",
                                 msg="No revision is open in docs/plan/TODO.md")),
 ("m14", NOROOT, ["TODO.md"], dict(exit=0, result="none", root="—", layout="none")),
 ("m15", NOROOT, ["TODO.md", "--", "05-old"], M([ln("docs/plan/05-old/_TODO.md"), bp("docs/plan/05-old/feat-old/TODO.md", "single-file")],
                                                "05-old", "revision 05-old", root="—", layout="none")),
 ("m16", DOM, ["DO.md"], M(DO_OPEN, "01-r", "revision 01-r", root="docs/plan/DO.md")),
 ("m17", BROKEN, ["TODO.md"], dict(exit=1, result="error", prob=["revision 09-gone is open at docs/plan/TODO.md:7"],
                                   fix=["docs/plan/09-gone/_TODO.md was never committed"])),
 ("m18", REV, ["TODO.md", "--", "a/b"], dict(exit=1, result="error", prob=["'a/b' is not a label"])),
 ("m19", REV, ["TODO.md", "--", "nope"], dict(exit=1, result="error", revision="—", prob=["docs/plan/nope/ does not exist"])),
 ("m20", REV, "chmod", dict(exit=1, result="error", prob=[f"{R}/feat-big/TODO/01-alpha.md cannot be read"],
                           fix=[f"chmod u+r {R}/feat-big/TODO/01-alpha.md"])),
 ("m21", NOGIT, "nogit", dict(exit=1, result="error", prob=["not inside a git repository"])),
 ("m22", REV, "awk127", dict(raw=True, exit=3, err=["memory-check.sh: awk failed", "hint: awk exited 127"])),
 ("m23", REV, [], dict(raw=True, exit=2, err=["no model given"])),
 ("m24", REV, ["X.md"], dict(raw=True, exit=2, err=["the model must be TODO.md or DO.md"])),
 ("m25", REV, ["TODO.md", "--threshold", "abc"], dict(raw=True, exit=2, err=["a whole number of tokens"])),
 ("m26", REV, ["TODO.md", "--threshold", "0"], dict(raw=True, exit=2, err=["at least 1 token"])),
 ("m27", REV, ["TODO.md", "--threshold"], dict(raw=True, exit=2, err=["--threshold needs a number"])),
 ("m28", REV, ["TODO.md", "--", "05-old", "07-rev"], dict(raw=True, exit=2, err=["more than one label"])),
 ("m29", REV, ["TODO.md", "--bogus"], dict(raw=True, exit=2, err=["unknown option '--bogus'"])),
]

def sh(args, cwd, env=None): return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
def git(*a, cwd):
    r = sh(["git", *a], cwd)
    if r.returncode: sys.exit(f"git {' '.join(a)} failed in {cwd}: {r.stderr}")
    return r.stdout

def build():
    shutil.rmtree(FX, ignore_errors=True)
    for repo, files in FILES.items():
        os.makedirs(repo)
        git("init", "-q", "-b", "main", cwd=repo)
        for k, v in (("user.email", "suite@example.invalid"), ("user.name", "suite"), ("commit.gpgsign", "false")):
            git("config", k, v, cwd=repo)
        for rel, data in files.items():
            p = f"{repo}/{rel}"; os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "wb").write(data)
        git("add", "-A", cwd=repo); git("commit", "-q", "-m", "fixture", cwd=repo)
    os.makedirs(NOGIT)
    os.makedirs(AWK127, exist_ok=True)
    open(AWK127 + "/awk", "w").write("#!/bin/sh\nexit 127\n"); os.chmod(AWK127 + "/awk", 0o755)

def state(repo):  # what "untouched" means: the working tree's status, and HEAD
    if repo == NOGIT: return tuple(sorted(os.listdir(NOGIT)))
    return git("status", "--porcelain", "--untracked-files=all", cwd=repo), git("rev-parse", "HEAD", cwd=repo)

def parse(out):
    rep, order, key = {}, [], None
    for line in out.splitlines():
        if line.startswith("  ") and key: rep[key].append(line[2:]); continue
        m = re.match(r"^([a-z-]+): (.*)$", line)
        if not m: return None, order
        key = m.group(1); order.append(key); rep[key] = [m.group(2)]
    return rep, order

def run(repo, args, shell):
    env = dict(os.environ); cwd = repo; chmod = None
    if args == "nogit": env["GIT_CEILING_DIRECTORIES"] = W; args = ["TODO.md"]
    elif args == "chmod": chmod = f"{REV}/{R}/feat-big/TODO/01-alpha.md"; args = ["TODO.md"]
    elif args == "awk127": env["PATH"] = AWK127 + ":" + env["PATH"]; args = ["TODO.md"]
    if chmod: os.chmod(chmod, 0)
    try: r = sh([shell, SCRIPT, *args], cwd, env)
    finally:
        if chmod: os.chmod(chmod, 0o644)
    return r

def expected(repo, entries, where, th, extra):
    """The measured report's lines, computed from the fixture's own bytes."""
    s = lambda k: "" if k == 1 else "s"
    rows = []
    for p, acc, br, lay in entries:
        d = open(f"{repo}/{p}", "rb").read()
        rows.append((len(d), len(d.split()), d.count(b"\n") + (0 if not d or d.endswith(b"\n") else 1), acc, br, lay, p))
    rows.sort(key=lambda r: (-r[0], r[6]))
    tok = lambda b: b * 3 // 7   # the calibrated ratio, as the script's header records it
    files = [f"{p} — {b} bytes, {w} words, {l} lines, ≈{tok(b)} tokens, {acc}" for b, w, l, acc, _, _, p in rows]
    over = [f"{p}: ≈{tok(b)} tokens, over the threshold of ≈{th}" for b, _, _, acc, _, _, p in rows if acc == "whole" and tok(b) > th]
    bs = {}
    for b, _, _, _, d, lay, _ in rows:
        if d: x = bs.setdefault(d, [lay, 0, 0]); x[1] += 1; x[2] += b
    branches = [f"{d.rsplit('/', 1)[-1]} — {lay}, {n} file{s(n)}, {B} bytes, ≈{tok(B)} tokens"
                for d, (lay, n, B) in sorted(bs.items(), key=lambda kv: (-kv[1][2], kv[0]))]
    n = len(rows); tb = sum(r[0] for r in rows); wh = [r for r in rows if r[3] == "whole"]; wb = sum(r[0] for r in wh)
    total = f"{n} file{s(n)}, {tb} bytes, ≈{tok(tb)} tokens; read whole: {len(wh)} file{s(len(wh))}, ≈{tok(wb)} tokens"
    msg = f"Measured {n} plan file{s(n)} in {where}; ≈ tokens are bytes × 3 / 7, calibrated on claude-opus-5-5 as Read returns a file."
    if over: msg += f" {len(over)} read whole {'is' if len(over) == 1 else 'are'} over the threshold; see warnings."
    return files, branches, total, extra + over, msg

def grade(repo, exp, r):
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
    one = lambda k: "\n".join(rep[k])
    allv = lambda k: [] if rep[k] == ["—"] else rep[k]
    for k in ("result", "root", "layout", "revision", "threshold"):
        if k in exp and one(k) != exp[k]: probs.append(f"{k}: want {exp[k]!r} got {one(k)!r}")
    if "measure" in exp:
        files, branches, total, warns, msg = expected(repo, *exp["measure"])
        for k, want in (("files", files), ("branches", branches), ("warnings", warns)):
            if allv(k) != want:
                bad = next((f"{g!r} want {w!r}" for g, w in zip(allv(k), want) if g != w), f"{len(allv(k))} lines, want {len(want)}")
                probs.append(f"{k}: {bad}")
        if one("total") != total: probs.append(f"total: {one('total')!r} want {total!r}")
        if one("message") != msg: probs.append(f"message: {one('message')!r} want {msg!r}")
        if allv("candidates"): probs.append("candidates on a measured report")
    else:
        for k in ("files", "branches", "total"):
            if allv(k): probs.append(f"{k} on a {exp['result']} report")
    if "cand" in exp and allv("candidates") != exp["cand"]: probs.append(f"candidates {allv('candidates')} want {exp['cand']}")
    for k, key in (("prob", "problem"), ("fix", "fix")):
        for w in exp.get(k, []):
            if not any(w in v for v in allv(key)): probs.append(f"{key} lacks {w!r}: {allv(key)}")
    if len(allv("problem")) != len(allv("fix")): probs.append(f"{len(allv('problem'))} problems but {len(allv('fix'))} fixes")
    if exp["result"] != "error" and allv("problem"): probs.append(f"a problem on a {exp['result']} report: {allv('problem')}")
    if exp["result"] == "error" and not allv("problem"): probs.append("an error without a problem")
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
    d = HERE + "/mutants"; tmp = W + "/mc-mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; root = f"{tmp}/{name}"; out = root + "/memory-check.sh"
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
    want = [a for a in sys.argv[1:] if re.match(r"^m\d", a)]
    build()
    st = static_checks(); print("static: " + ("ok" if not st else "; ".join(st)))
    fails = len(st)
    for cid, repo, args, exp in C:
        if want and cid not in want: continue
        before = state(repo); outs, probs = set(), []
        for shell in SHELLS:
            for _ in range(1 if "--once" in sys.argv else 2):
                r = run(repo, args, shell); outs.add((r.returncode, r.stdout, r.stderr))
                probs += [p for p in grade(repo, exp, r) if p not in probs]
                if state(repo) != before and "the fixture changed" not in probs: probs.append("the fixture changed")
        if len(outs) > 1: probs.append("output differs between runs or shells")
        print(f"{'PASS' if not probs else 'FAIL'} {cid:<4} " + "; ".join(probs))
        if "-v" in sys.argv: print("".join(o[1] + o[2] for o in sorted(outs)))
        fails += bool(probs)
    print(f"\n{fails} failing"); sys.exit(1 if fails else 0)

main()
