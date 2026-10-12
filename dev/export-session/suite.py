"""export-session.py suite: writes fixture session logs, renders each with the script, and
grades every output byte for byte. No model, and nothing written outside a temporary
directory.

  python3 -I suite.py [-v] [--script PATH] [ids...]
  python3 -I suite.py --mutants

Each case writes a JSONL log the way Claude Code does, with raw UTF-8, runs the script
under a stated locale, and checks the exit code, stderr, the summary line and the output
file's bytes. --mutants applies each patch in mutants/ to a copy of the script and runs the
suite on it: each must fail it, and a patch that no longer applies is reported stale. A
patch names its file relative to scripts/."""
import glob, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCRIPT = REPO + "/plugins/workflow-coding/scripts/export-session.py"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
VERBOSE = "-v" in sys.argv
UTF8, LATIN1 = "en_US.UTF-8", "en_US.ISO8859-1"
LOG = "0f1e2d3c-session.jsonl"

def rec(kind, content, ts, **kw):   # raw UTF-8, as Claude Code writes its logs
    return json.dumps(dict(type=kind, timestamp=ts, message=dict(content=content), **kw), ensure_ascii=False)
def at(hm): return f"2026-10-12T{hm}:00.000Z"
def compact(args):                   # the shape of a real /compact record
    return ("<command-name>/compact</command-name>\n            <command-message>compact</command-message>\n"
            f"            <command-args>{args}</command-args>")
def doc(title, *blocks):
    head = (f"# Session {title} — full transcript\n\nRendered from the Claude Code session log `{LOG}`. "
            "It contains the operator's messages, the assistant's visible replies, the operator's answers "
            "to multiple-choice questions, compaction summaries, and one-line entries for tool actions. "
            "It omits tool output, system reminders and hidden reasoning.\n")
    return "\n".join([head, *blocks])
def summary(op, cl, co): return f"{op} operator messages, {cl} assistant replies, {co} compactions"

# Every kind of record the script renders or skips, in one log.
G = [
    rec("user", "Hello <system-reminder>noise</system-reminder>there", at("10:00")),
    rec("assistant", [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"description": "List files"}},
                      {"type": "tool_use", "id": "t2", "name": "Read", "input": {"file_path": "/x/y.md"}}], at("10:01")),
    rec("user", [{"type": "tool_result", "tool_use_id": "t1", "content": "a\nb"}], at("10:01")),
    rec("assistant", [{"type": "text", "text": "  Done.  "}], at("10:02")),
    rec("assistant", [{"type": "tool_use", "id": "q1", "name": "AskUserQuestion", "input": {"questions": [
        {"question": "Pick one?", "options": [{"label": "A"}, {"label": "B"}]}]}}], at("10:03")),
    rec("user", [{"type": "tool_result", "tool_use_id": "q1", "content": "A"}], at("10:04")),
    rec("user", compact("Keep the plan paths"), at("10:05")),
    rec("user", "<command-name>/clear</command-name>\n<command-message>clear</command-message>\n<command-args></command-args>", at("10:05")),
    rec("user", "This session is being continued.", at("10:06"), isCompactSummary=True),
    rec("user", "meta", at("10:06"), isMeta=True),
    rec("assistant", [{"type": "text", "text": "side"}], at("10:06"), isSidechain=True),
    "{not json",
    json.dumps({"type": "system", "timestamp": at("10:06"), "content": "x"}),
    rec("user", "<local-command-stdout>x</local-command-stdout>", at("10:06")),
    rec("user", "[Request interrupted by user]", at("10:07")),
    rec("assistant", [{"type": "text", "text": "Bye."}], at("10:08")),
]
GOUT = doc("g01",
    "## Operator — 2026-10-12 10:00 UTC\n\nHello there\n",
    "<details><summary>Actions (2)</summary>\n\n- `Bash`: List files\n- `Read`: /x/y.md\n\n</details>\n",
    "## Claude — 2026-10-12 10:02 UTC\n\nDone.\n",
    "## Claude asks — 2026-10-12 10:03 UTC\n\n- **Pick one?** Options: A; B\n",
    "## Operator answers — 2026-10-12 10:04 UTC\n\nA\n",
    "## Operator ran `/compact` — 2026-10-12 10:05 UTC\n\nKeep the plan paths\n",
    "## Operator ran `/clear` — 2026-10-12 10:05 UTC\n",
    "## Compaction summary — 2026-10-12 10:06 UTC\n\n<details><summary>Summary the session continued "
    "from</summary>\n\nThis session is being continued.\n\n</details>\n",
    "*[Request interrupted by user]*\n",
    "## Claude — 2026-10-12 10:08 UTC\n\nBye.\n")
HI = [rec("user", "hi", at("09:00"))]
HIOUT = "## Operator — 2026-10-12 09:00 UTC\n\nhi\n"

# id, log lines, output name (None: no output path), locale, extra args, expectations.
# The defect cases come first, the title's before the rest, since every output has a title:
# so a mutant's first failure is the case aimed at it.
C = [
    ("e03", HI, "r1a-full.md", UTF8, [], dict(exit=0, out=doc("r1a", HIOUT), summary=summary(1, 0, 0))),   # title
    ("e04", HI, "notes.md", UTF8, [], dict(exit=0, out=doc("notes", HIOUT), summary=summary(1, 0, 0))),
    ("e01", [rec("user", "a — b", at("09:00"))], "e01.md", LATIN1, [],     # em dash, once
     dict(exit=0, out=doc("e01", "## Operator — 2026-10-12 09:00 UTC\n\na — b\n"), summary=summary(1, 0, 0))),
    ("e02", [rec("user", compact("Keep A.\nKeep B."), at("09:00"))], "e02.md", UTF8, [],   # /compact's instructions
     dict(exit=0, out=doc("e02", "## Operator ran `/compact` — 2026-10-12 09:00 UTC\n\nKeep A.\nKeep B.\n"),
          summary=summary(0, 0, 0))),
    ("g01", G, "g01-full.md", UTF8, [], dict(exit=0, out=GOUT, summary=summary(1, 2, 1))),
    ("g02", G, "g01-full.md", LATIN1, [], dict(exit=0, out=GOUT, summary=summary(1, 2, 1))),
    ("u01", HI, None, UTF8, [], dict(exit=2, stderr="usage: export-session.py <session.jsonl> <output.md>")),
    ("u02", HI, "u02.md", UTF8, ["extra"], dict(exit=2, stderr="usage: export-session.py", nofile=True)),
]

def run_case(script, case, tmp):
    cid, lines, name, loc, extra, want = case
    d = os.path.join(tmp, cid); os.makedirs(d)
    log, out = os.path.join(d, LOG), (os.path.join(d, name) if name else None)
    with open(log, "w", encoding="utf-8") as f: f.write("".join(l + "\n" for l in lines))
    argv = [sys.executable, "-I", script] + ([log, out] if out else []) + extra
    p = subprocess.run(argv, capture_output=True, env=dict(os.environ, LC_ALL=loc, LANG=loc))
    err, so, bad = p.stderr.decode("utf-8", "replace"), p.stdout.decode("utf-8", "replace"), []
    if p.returncode != want["exit"]: bad.append(f"exit {p.returncode}, want {want['exit']} (stderr: {err.strip()[-200:]!r})")
    if "stderr" in want:
        if not err.startswith(want["stderr"]): bad.append(f"stderr {err!r} lacks {want['stderr']!r}")
    elif err: bad.append(f"stderr not empty: {err.strip()[-200:]!r}")
    if want.get("nofile") and out and os.path.exists(out): bad.append("wrote an output file on a usage error")
    if "summary" in want and not so.rstrip("\n").endswith(" " + want["summary"]):
        bad.append(f"summary {so.strip()!r}, want it to end {want['summary']!r}")
    if "out" in want:
        got = open(out, "rb").read() if out and os.path.exists(out) else None
        exp = want["out"].encode("utf-8")
        if got is None: bad.append("no output file")
        elif got != exp:
            i = next((k for k in range(min(len(got), len(exp))) if got[k] != exp[k]), min(len(got), len(exp)))
            bad.append(f"output differs at byte {i}: got {got[max(0, i - 20):i + 30]!r}, want {exp[max(0, i - 20):i + 30]!r}")
    if VERBOSE and out and os.path.exists(out): print(open(out, encoding="utf-8", errors="replace").read())
    return bad

def suite(script, ids):
    with tempfile.TemporaryDirectory() as tmp:
        for case in C:
            if ids and case[0] not in ids: continue
            yield case[0], run_case(script, case, tmp)

def latin1_ready():   # without the locale, e01 and g02 would pass on a broken script
    p = subprocess.run([sys.executable, "-I", "-c", "import locale; print(locale.getpreferredencoding(False))"],
                       capture_output=True, text=True, env=dict(os.environ, LC_ALL=LATIN1, LANG=LATIN1))
    return p.stdout.strip().upper().replace("_", "-") in ("ISO8859-1", "ISO-8859-1", "LATIN-1")

if not latin1_ready():
    sys.exit(f"the {LATIN1} locale is not installed, so e01 and g02 cannot test the encoding")
args = sys.argv[1:]
if "--script" in args: del args[args.index("--script"):args.index("--script") + 2]
ids = [a for a in args if not a.startswith("-")]

if "--mutants" in sys.argv:
    failing = 0
    for patch in sorted(glob.glob(HERE + "/mutants/*.patch")):
        name = os.path.basename(patch).removesuffix(".patch")
        with tempfile.TemporaryDirectory() as d:
            shutil.copy(SCRIPT, d + "/export-session.py")
            ok = subprocess.run(["patch", "--dry-run", "-s", "-F0", "-p1", "-d", d, "-i", patch], capture_output=True)
            if ok.returncode:
                print(f"STALE {name}"); failing += 1; continue
            subprocess.run(["patch", "-s", "-F0", "-p1", "-d", d, "-i", patch], check=True, capture_output=True)
            first = next(((cid, bad) for cid, bad in suite(d + "/export-session.py", []) if bad), None)
        if first: print(f"KILLED {name}  (FAIL {first[0]}  {'; '.join(first[1])[:120]})")
        else: print(f"SURVIVED {name}"); failing += 1
    print(f"\n{failing} failing"); sys.exit(1 if failing else 0)

failing = 0
for cid, bad in suite(SCRIPT, ids):
    print(f"PASS {cid}" if not bad else f"FAIL {cid}  " + "; ".join(bad))
    failing += bool(bad)
print(f"\n{failing} failing"); sys.exit(1 if failing else 0)
