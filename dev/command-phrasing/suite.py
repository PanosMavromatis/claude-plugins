"""check.py suite: runs the phrasing check on fixture command files and on the plugin's own
commands, each with one statement removed, and grades its output exactly. No model, and
nothing written outside a temporary directory.

  python3 -I suite.py [--script PATH] [ids...]
  python3 -I suite.py --mutants

The fixture cases come first, each aimed at one rule. Then the plugin's commands as they
are, which must pass, and for each command granting git, each phrase removed in turn,
which must fail naming that command and that phrase. --mutants applies each patch in
mutants/ to a copy of check.py, placed where its default reaches the plugin's commands,
and runs the suite on it: each must fail it, and a patch that no longer applies is
reported stale. A patch names its file relative to dev/command-phrasing/."""
import glob, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
COMMANDS = REPO + "/plugins/workflow-coding/commands"
SCRIPT = HERE + "/check.py"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
C_, ALONE = "never `git -C <path>`", "every command alone"

def cmd(tools, body, desc="A command."):
    return f"---\nallowed-tools: {tools}\ndescription: {desc}\n---\n\n# A command\n\n{body}\n"
BOTH = f"Run `git` as `git <subcommand>`, {C_}.\n\n**Run {ALONE}**: one call each."
GIT = "Bash(git status:*), Bash(git log:*), Read"

# id, files (name: text), arguments (None: the directory), exit, stdout, stderr's start.
F = [
    ("f01", {"a.md": cmd(GIT, BOTH)}, None, 0, "ok    a.md\n\n0 failing\n", ""),
    ("f02", {"a.md": cmd("Read, Write", "No rule here.")}, None, 0,   # grants no git: not checked
     "skip  a.md (grants no git)\n\n0 failing\n", ""),
    ("f03", {"a.md": cmd("Read", "It never grants `Bash(git status:*)` itself.")}, None, 0,   # git named only in the body
     "skip  a.md (grants no git)\n\n0 failing\n", ""),
    ("f04", {"a.md": cmd(GIT, f"Run `git` as `git <subcommand>`, never `git -C\n<path>`.\n\n**Run {ALONE}**.")},
     None, 1, f"FAIL  a.md lacks: {C_}\n\n1 failing\n", ""),                 # a phrase split across lines
    ("f05", {"a.md": cmd(GIT, f"Never chain. {C_}."), "b.md": cmd(GIT, f"Run {ALONE}."),
             "c.md": cmd(GIT, BOTH)}, None, 1,                              # every failing command named
     f"FAIL  a.md lacks: {ALONE}\nFAIL  b.md lacks: {C_}\nok    c.md\n\n2 failing\n", ""),
    ("f06", {"a.md": "# No frontmatter\n\nRun `git status`.\n"}, None, 0,   # no frontmatter grants nothing
     "skip  a.md (grants no git)\n\n0 failing\n", ""),
    ("f07", {"a.md": cmd(GIT, "Nothing in the body.", desc=f"{C_}; {ALONE}")}, None, 1,   # the phrases only in the frontmatter
     f"FAIL  a.md lacks: {C_}; {ALONE}\n\n1 failing\n", ""),
    ("f08", {"a.md": "---\nallowed-tools:\n  - Read\n  - Bash(git status:*)\ndescription: A list.\n---\n\nNo rule.\n"},
     None, 1, f"FAIL  a.md lacks: {C_}; {ALONE}\n\n1 failing\n", ""),       # allowed-tools as a list
    ("f09", {}, None, 2, "", "check.py: no command files to check"),     # an empty directory
    ("f10", {}, ["missing"], 2, "", "check.py: no such file or directory: missing"),
    ("f11", {"a.md": cmd(GIT, "No rule."), "b.md": cmd(GIT, BOTH)}, ["b.md"], 0,   # a file: only it
     "ok    b.md\n\n0 failing\n", ""),
]

def grants(text):   # the suite's own reading, not check.py's
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return bool(m and re.search(r"^allowed-tools:.*Bash\(git ", m.group(1), re.M))

def plugin_cases():
    names = sorted(os.path.basename(p) for p in glob.glob(COMMANDS + "/*.md"))
    texts = {n: open(f"{COMMANDS}/{n}", encoding="utf-8").read() for n in names}
    git = [n for n in names if grants(texts[n])]
    if not git: sys.exit(f"no command in {COMMANDS} grants git, so there is nothing to remove")
    lines = "".join(f"ok    {n}\n" if n in git else f"skip  {n} (grants no git)\n" for n in names)
    yield "p00", {}, [], 0, lines + "\n0 failing\n", ""         # no argument: the plugin's commands/
    yield "p01", texts, None, 0, lines + "\n0 failing\n", ""
    for n in git:
        for half, phrase in (("C", C_), ("alone", ALONE)):
            if phrase not in texts[n]: sys.exit(f"{n} lacks {phrase!r} already; fix the plugin before the suite")
            cut = dict(texts, **{n: texts[n].replace(phrase, "")})
            want = lines.replace(f"ok    {n}\n", f"FAIL  {n} lacks: {phrase}\n")
            yield f"{n.removesuffix('.md')}/{half}", cut, None, 1, want + "\n1 failing\n", ""

def run_case(script, case, tmp):
    cid, files, args, exit_, out, err = case
    d = os.path.join(tmp, cid.replace("/", "-")); os.makedirs(d)
    for name, text in files.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f: f.write(text)
    argv = [sys.executable, "-I", script] + ([d] if args is None else [os.path.join(d, a) if a != "missing" else a for a in args])
    p = subprocess.run(argv, capture_output=True, text=True, cwd=d)
    bad = []
    if p.returncode != exit_: bad.append(f"exit {p.returncode}, want {exit_}")
    if p.stdout != out: bad.append(f"stdout {p.stdout!r}, want {out!r}")
    if not p.stderr.startswith(err) or (not err and p.stderr): bad.append(f"stderr {p.stderr.strip()[-200:]!r}, want {err!r}")
    return bad

def suite(script, ids):
    with tempfile.TemporaryDirectory() as tmp:
        for case in [*F, *plugin_cases()]:
            if ids and case[0] not in ids: continue
            yield case[0], run_case(script, case, tmp)

args = sys.argv[1:]
if "--script" in args: del args[args.index("--script"):args.index("--script") + 2]
ids = [a for a in args if not a.startswith("-")]

if "--mutants" in sys.argv:
    failing = 0
    for patch in sorted(glob.glob(HERE + "/mutants/*.patch")):
        name = os.path.basename(patch).removesuffix(".patch")
        with tempfile.TemporaryDirectory() as t:
            d = t + "/dev/command-phrasing"; os.makedirs(d)
            os.symlink(REPO + "/plugins", t + "/plugins")   # so the copy's default reaches the plugin
            shutil.copy(SCRIPT, d + "/check.py")
            ok = subprocess.run(["patch", "--dry-run", "-s", "-F0", "-p1", "-d", d, "-i", patch], capture_output=True)
            if ok.returncode:
                print(f"STALE {name}"); failing += 1; continue
            subprocess.run(["patch", "-s", "-F0", "-p1", "-d", d, "-i", patch], check=True, capture_output=True)
            first = next(((cid, bad) for cid, bad in suite(d + "/check.py", []) if bad), None)
        if first: print(f"KILLED {name}  (FAIL {first[0]}  {'; '.join(first[1])[:120]})")
        else: print(f"SURVIVED {name}"); failing += 1
    print(f"\n{failing} failing"); sys.exit(1 if failing else 0)

failing = 0
for cid, bad in suite(SCRIPT, ids):
    print(f"PASS {cid}" if not bad else f"FAIL {cid}  " + "; ".join(bad))
    failing += bool(bad)
print(f"\n{failing} failing"); sys.exit(1 if failing else 0)
