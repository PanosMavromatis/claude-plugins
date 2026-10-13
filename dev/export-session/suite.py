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
import glob, json, os, shutil, subprocess, sys, tarfile, tempfile

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
def doc(title, *blocks, log=LOG):
    head = (f"# Session {title} — full transcript\n\nRendered from the Claude Code session log `{log}`. "
            "It contains the operator's messages, the assistant's visible replies, the operator's answers "
            "to multiple-choice questions, compaction summaries, and one-line entries for tool actions. "
            "It omits tool output, system reminders and hidden reasoning.\n")
    return "\n".join([head, *blocks])
def summary(op, cl, co, folder=False, subs=None):
    return (f"{op} operator messages, {cl} assistant replies, {co} compactions"
            + (f", {subs} subagents" if subs is not None else "")
            + ", raw log copied" + (", session folder archived" if folder else ", no session folder"))

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

# A project's log directory, for the cases that name a session: A was renamed from
# old-name to new-name, so its log holds both names; B is old-name now; C was never
# renamed, so it has no folder; D and E share a name.
UA, UB, UC, UD, UE = (f"{c * 8}-0000-4000-8000-00000000000{n}" for n, c in enumerate("abcde", 1))
def title(t, u): return json.dumps({"type": "custom-title", "customTitle": t, "sessionId": u})
def named(t): return json.dumps({"customTitle": t})
def said(who): return rec("user", f"from {who}", at("08:00"))
PROJ = {
    f"{UA}.jsonl": [title("old-name", UA), title("old-name", UA), said("A"), title("new-name", UA)],
    f"{UA}/custom-title.json": named("new-name"),
    f"{UB}.jsonl": [title("old-name", UB), said("B")], f"{UB}/custom-title.json": named("old-name"),
    f"{UC}.jsonl": [said("C")],
    f"{UD}.jsonl": [said("D")], f"{UD}/custom-title.json": named("twin"),
    f"{UE}.jsonl": [said("E")], f"{UE}/custom-title.json": named("twin"),
}
def by_name(n): return dict(proj=PROJ, arg=n)

# A session that spawned a subagent. Every record in a subagent's log is a sidechain record,
# and it hands its answer back as a SubagentHandback call, not as text.
FOLDER = LOG.removesuffix(".jsonl")
SPAWNS = [rec("assistant", [{"type": "tool_use", "id": "ag1", "name": "Agent", "input": {"description": "Draft it"}}], at("11:00")),
          rec("assistant", [{"type": "text", "text": "Drafting."}], at("11:01"))]
SUB = [rec("user", "Draft the plan.", at("11:00"), isSidechain=True),
       rec("assistant", [{"type": "tool_use", "id": "r1", "name": "Read", "input": {"file_path": "/p.md"}}], at("11:00"), isSidechain=True),
       rec("assistant", [{"type": "tool_use", "id": "h1", "name": "SubagentHandback", "input": {"message": "## Draft\n\nDone."}}],
           at("11:01"), isSidechain=True)]
def agent(tool_use_id): return {f"{FOLDER}/subagents/agent-a1.jsonl": SUB, f"{FOLDER}/subagents/agent-a1.meta.json":
                                json.dumps({"agentType": "plan-drafter", "description": "Draft it", "toolUseId": tool_use_id})}
SPAWN_ACT = "<details><summary>Actions (1)</summary>\n\n- `Agent`: Draft it\n\n</details>\n"
SUB_OUT = ("<details><summary>Subagent plan-drafter — Draft it (1 replies)</summary>\n\n"
           "### Prompt — 2026-10-12 11:00 UTC\n\nDraft the plan.\n\n"
           "<details><summary>Actions (1)</summary>\n\n- `Read`: /p.md\n\n</details>\n\n"
           "### Subagent — 2026-10-12 11:01 UTC\n\n## Draft\n\nDone.\n\n</details>\n")
DRAFTING = "## Claude — 2026-10-12 11:01 UTC\n\nDrafting.\n"
def from_(who, u, t, folder=True): return dict(exit=0, out=doc(t, f"## Operator — 2026-10-12 08:00 UTC\n\nfrom {who}\n",
                                                               log=f"{u}.jsonl"), summary=summary(1, 0, 0, folder=folder))

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
    ("n01", [], "n01.md", UTF8, [], from_("A", UA, "n01"), by_name("new-name")),     # a renamed session's name
    ("n02", [], "n02.md", UTF8, [], from_("B", UB, "n02"), by_name("old-name")),     # A's old name is B's alone
    ("n03", [], "n03.md", UTF8, [], dict(exit=1, stderr="export-session.py: no session named 'no-such' in ",
                                         nofile=True), by_name("no-such")),
    ("n04", [], "n04.md", UTF8, [], dict(exit=1, stderr="export-session.py: 2 sessions named 'twin' in ",
                                         nofile=True), by_name("twin")),
    ("n05", [], "n05.md", UTF8, [], dict(exit=1, stderr="export-session.py: no such session log: missing.jsonl",
                                         nofile=True), dict(proj={}, arg="missing.jsonl")),
    ("s01", SPAWNS, "s01.md", UTF8, ["--subagents"],      # inline, after the call that spawned it
     dict(exit=0, out=doc("s01", SPAWN_ACT, SUB_OUT, DRAFTING), summary=summary(0, 1, 0, folder=True, subs=1)),
     dict(files=agent("ag1"))),
    ("s02", SPAWNS, "s02.md", UTF8, [],                   # only when asked for
     dict(exit=0, out=doc("s02", SPAWN_ACT, DRAFTING), summary=summary(0, 1, 0, folder=True)), dict(files=agent("ag1"))),
    ("s03", SPAWNS, "s03.md", UTF8, ["--subagents"],      # its call not in the log: an appendix, not lost
     dict(exit=0, out=doc("s03", SPAWN_ACT, DRAFTING, "## Subagents whose call is not in the log\n", SUB_OUT),
          summary=summary(0, 1, 0, folder=True, subs=1)), dict(files=agent("zz"))),
    ("r01", HI, "r01.md", UTF8, [],                       # the raw log, byte for byte, as <name>.jsonl
     dict(exit=0, out=doc("r01", HIOUT), summary=summary(1, 0, 0), jsonl=True, notar=True)),
    ("r02", HI, FOLDER + ".md", UTF8, [],                 # <name>.jsonl would be the log it reads
     dict(exit=1, stderr="export-session.py: ", stderr_has="is the session log itself", nofile=True, keep_log=True)),
    ("r03", HI, "r03.md", UTF8, [],                       # the session's folder, as <name>.tar.gz
     dict(exit=0, out=doc("r03", HIOUT), summary=summary(1, 0, 0, folder=True), jsonl=True,
          tar={"r03/custom-title.json": named("x"), "r03/tool-results/t1.txt": "a large output\n",
               "r03/subagents/agent-a1.jsonl": "".join(l + "\n" for l in SUB),
               "r03/subagents/agent-a1.meta.json": agent("ag1")[f"{FOLDER}/subagents/agent-a1.meta.json"]}),
     dict(files={f"{FOLDER}/custom-title.json": named("x"), f"{FOLDER}/tool-results/t1.txt": "a large output\n",
                 **agent("ag1")})),
    ("r04", HI, "deeper/still/r04.md", UTF8, [],          # the output directory is created
     dict(exit=0, out=doc("r04", HIOUT), summary=summary(1, 0, 0), jsonl=True, notar=True)),
    ("i01", [], "i01.md", UTF8, [], from_("A", UA, "i01"), dict(proj=PROJ, arg=UA)),   # a session by its id
    ("o01", [], "o01dir/new-name.md", UTF8, [], from_("A", UA, "new-name"),          # a directory: named for it
     dict(proj=PROJ, arg="new-name", out_arg="o01dir")),
    ("o02", [], "home/claude-exports/work/new-name.md", UTF8, [], from_("A", UA, "new-name"),   # no output given
     dict(proj=PROJ, arg="new-name", out_arg=None, home=True)),
    ("o03", [], f"o03dir/{UC}.md", UTF8, [], from_("C", UC, UC, folder=False),    # never renamed: its id
     dict(proj=PROJ, arg=UC, out_arg="o03dir")),
    ("o04", [], "work/exports/new-name.md", UTF8, [],                              # inside the repository
     dict(exit=1, stderr="export-session.py: ", stderr_has="is inside the repository", nofile=True),
     dict(proj=PROJ, arg="new-name", out_arg="work/exports", files={"work/.git/HEAD": "ref: refs/heads/main\n"})),
    ("g01", G, "g01-full.md", UTF8, [], dict(exit=0, out=GOUT, summary=summary(1, 2, 1))),
    ("g02", G, "g01-full.md", LATIN1, [], dict(exit=0, out=GOUT, summary=summary(1, 2, 1))),
    ("u01", HI, None, UTF8, [], dict(exit=2, stderr="usage: export-session.py <session> [<output.md> | <output dir>] [--subagents]")),
    ("u02", HI, "u02.md", UTF8, ["extra"], dict(exit=2, stderr="usage: export-session.py", nofile=True)),
]

def enc(path):   # how Claude Code names a project's log directory: each non-letter, non-digit is -
    return "".join(c if c.isascii() and c.isalnum() else "-" for c in path)

def run_case(script, case, tmp):
    cid, lines, name, loc, extra, want, *setup = case
    d = os.path.join(tmp, cid); os.makedirs(d)
    log, out = os.path.join(d, LOG), (os.path.join(d, name) if name else None)
    written = "".join(l + "\n" for l in lines).encode("utf-8")
    with open(log, "wb") as f: f.write(written)
    env, cwd, first = dict(os.environ, LC_ALL=loc, LANG=loc), None, log
    env.pop("CLAUDE_CONFIG_DIR", None)
    def put(root, files):
        for rel, body in files.items():
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
                f.write(body if isinstance(body, str) else "".join(l + "\n" for l in body))
    s = setup[0] if setup else {}
    if "proj" in s:   # a case that names a session: its own config directory, working directory and projects
        cwd, env["CLAUDE_CONFIG_DIR"] = os.path.join(d, "work"), os.path.join(d, "claude")
        os.makedirs(cwd)
        proj = os.path.join(env["CLAUDE_CONFIG_DIR"], "projects", enc(os.path.realpath(cwd)))
        os.makedirs(proj)
        put(proj, s["proj"])
    put(d, s.get("files", {}))   # files beside the log, such as its <uuid>/subagents/
    first = s.get("arg", log)
    if s.get("home"): env["HOME"] = os.path.join(d, "home")
    second = ([os.path.join(d, s["out_arg"])] if s["out_arg"] else []) if "out_arg" in s else ([out] if out else [])
    argv = [sys.executable, "-I", script] + ([first] + second if out else []) + extra
    p = subprocess.run(argv, capture_output=True, env=env, cwd=cwd)
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
    base = out.removesuffix(".md") if out else ""
    if want.get("stderr_has") and want["stderr_has"] not in err: bad.append(f"stderr {err!r} lacks {want['stderr_has']!r}")
    if want.get("keep_log") and open(log, "rb").read() != written: bad.append("the session log changed")
    if want.get("jsonl"):   # the raw log beside the Markdown, byte for byte
        got = open(base + ".jsonl", "rb").read() if os.path.exists(base + ".jsonl") else None
        if got is None: bad.append("no <name>.jsonl")
        elif got != written: bad.append("<name>.jsonl is not the log, byte for byte")
    if want.get("notar") and os.path.exists(base + ".tar.gz"): bad.append("wrote <name>.tar.gz for a session with no folder")
    if "tar" in want:       # the folder, as <name>.tar.gz: its files, by name and content
        if not os.path.exists(base + ".tar.gz"): bad.append("no <name>.tar.gz")
        else:
            with tarfile.open(base + ".tar.gz") as t:
                got = {m.name: t.extractfile(m).read().decode("utf-8") for m in t.getmembers() if m.isfile()}
            if sorted(got) != sorted(want["tar"]): bad.append(f"archive holds {sorted(got)}, want {sorted(want['tar'])}")
            elif got != want["tar"]: bad.append("an archived file's content differs")
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
