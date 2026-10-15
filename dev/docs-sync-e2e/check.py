"""Grade a docs-sync-e2e run: what each case's session left in its fixture, and what it ran.

  LOCATE_PLAN_WORK=<dir> RUN=<tag> [CASES="f1 g1 ..."] python3 -I check.py

A case passes when its fixture ends as run.sh's header says it must: the files the agent was to
change changed, and staged; those it was to leave alone byte for byte as they were; HEAD where
it was unless the case commits. Files under .claude/agent-memory/ are the agent's memory and
are allowed in any case. A case whose session did not load the plugins it needs, by the init
record's plugin list, is reported as that. A subagent's tool calls carry a parent_tool_use_id
in the stream-json; if the stream holds none, they are read from the session's subagent
transcripts under ~/.claude/projects. Read-only: it reads the stream-json, those transcripts,
the fixtures and the copies run.sh kept of f3's files."""
import glob, json, os, subprocess, sys

W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK")
RUN = os.environ.get("RUN") or sys.exit("set RUN=<tag>")
S = os.path.realpath(W) + "/docsync"; OUT = f"{S}/out-{RUN}"; FX = f"{S}/fx-{RUN}"; BEFORE = f"{S}/before-{RUN}"
BLOCKED = "Blocked: AGENTS.override.md is generated from docs/agents/codex-review/AGENTS.md"
GATE = "dp-compile: [commands].test failed — commit blocked."
KERNEL = "src/probe_python.py"
MEM = ".claude/agent-memory/"
OVERRIDE, HIST = "AGENTS.override.md", "docs/agents/_history/tooling.md"

def text(content):  # a tool_result's content, flattened to one string
    if isinstance(content, str): return content
    return "\n".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in content or [])

def blocks(d):  # a record's message content, or nothing: some records carry message as a string
    m = d.get("message")
    content = m.get("content") if isinstance(m, dict) else None
    return [c for c in content if isinstance(c, dict)] if isinstance(content, list) else []

def records(cid):
    """(session's result, [(by, kind, block)]) in stream order: by is 'main' or 'sub'."""
    p = f"{OUT}/{cid}.jsonl"
    if not os.path.exists(p): return None, []
    res, sid, calls = None, None, []
    for line in open(p):
        try: d = json.loads(line)
        except ValueError: continue
        sid = sid or d.get("session_id")
        if d.get("type") == "result": res = d
        by = "sub" if d.get("parent_tool_use_id") else "main"
        calls += [(by, c["type"], c) for c in blocks(d) if c.get("type") in ("tool_use", "tool_result")]
    if sid and not any(by == "sub" for by, _, _ in calls):   # the stream carried no subagent messages
        for t in glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}/subagents/*.jsonl")):
            for line in open(t):
                try: d = json.loads(line)
                except ValueError: continue
                calls += [("sub", c["type"], c) for c in blocks(d) if c.get("type") in ("tool_use", "tool_result")]
    return res, calls

def missing(cid, *names):  # the plugins a case needs that its session's init record does not list
    loaded = set()
    for line in open(f"{OUT}/{cid}.jsonl"):
        try: d = json.loads(line)
        except ValueError: continue
        if d.get("type") == "system" and d.get("subtype") == "init":
            loaded = {p.get("name") for p in d.get("plugins") or []}; break
    gone = [n for n in names if n not in loaded]
    return f"{' and '.join(gone)} did not load" if gone else None

BASE = {"k1": "3"}   # the commits each fixture starts with, where not one

def git(cid, *a): return subprocess.run(["git", *a], cwd=f"{FX}/{cid}", capture_output=True, text=True)
def landed(cid): return git(cid, "rev-list", "--count", "HEAD").stdout.strip() != BASE.get(cid, "1")
def blob(cid, spec):  # a file at HEAD (HEAD:path) or in the index (:path), or None
    r = git(cid, "show", spec); return r.stdout if r.returncode == 0 else None
def work(cid, path):
    p = f"{FX}/{cid}/{path}"; return open(p).read() if os.path.exists(p) else None
def changed(cid):  # every path git status lists, the agent's memory left out
    lines = git(cid, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
    return {l[3:] for l in lines if not l[3:].startswith(MEM)}
def staged(cid, path): return blob(cid, f":{path}") == work(cid, path) != blob(cid, f"HEAD:{path}")
def bash(calls, by="main"): return [c for b, k, c in calls if b == by and k == "tool_use" and c.get("name") == "Bash"]
def cmd(c): return (c.get("input") or {}).get("command", "")
def results(calls, ids): return " ".join(text(c.get("content")) for _, k, c in calls if k == "tool_result" and c.get("tool_use_id") in ids)
def spawned(calls):  # the index of the main session's first Agent call, or None
    return next((i for i, (b, k, c) in enumerate(calls) if b == "main" and k == "tool_use" and c.get("name") in ("Agent", "Task")), None)

def start(cid, *plugins):
    """(problems so far, result, calls): no session, or a plugin not loaded, ends the case there."""
    res, calls = records(cid)
    if res is None: return ["no session"], res, calls
    gone = missing(cid, *plugins)
    if gone: return [gone], res, calls
    if any(d.get("tool_name") == "Skill" for d in res.get("permission_denials") or []):
        return ["the Skill tool was denied, so the command never ran"], res, calls   # run e3
    if spawned(calls) is None: return ["docs-sync was never spawned"], res, calls
    return [], res, calls

def others(cid, allowed):  # problems for any path changed beyond those the case allows
    extra = sorted(changed(cid) - set(allowed))
    return [f"also changed: {', '.join(extra)}"] if extra else []

def f1(cid="f1"):
    probs, res, _ = start(cid, "workflow-coding")
    if probs: return probs, res
    a = work(cid, "AGENTS.md") or ""
    if "--verbose" not in a: probs.append("AGENTS.md does not name --verbose")
    elif not staged(cid, "AGENTS.md"): probs.append("AGENTS.md's edit is not staged")
    if landed(cid):probs.append("a commit landed")
    return probs + others(cid, ["AGENTS.md", "tool.sh"]), res

def f2(cid="f2"):
    probs, res, _ = start(cid, "workflow-coding")
    if probs: return probs, res
    old, new = blob(cid, f"HEAD:{HIST}") or "", work(cid, HIST) or ""
    added = [l for l in new.splitlines() if l not in old.splitlines()]
    if not added: probs.append(f"{HIST} gained nothing")
    elif not any("-q" in l for l in added): probs.append(f"{HIST}'s new lines do not name -q: {added}")
    elif not staged(cid, HIST): probs.append(f"{HIST}'s edit is not staged")
    if not work(cid, "AGENTS.md") == blob(cid, ":AGENTS.md") == blob(cid, "HEAD:AGENTS.md"): probs.append("AGENTS.md changed")
    if landed(cid):probs.append("a commit landed")
    return probs + others(cid, [HIST, "tool.sh"]), res

def f3(cid="f3"):
    probs, res, _ = start(cid, "workflow-coding")
    if probs: return probs, res
    for path in ("README.md", "docs/ops/runbook.md"):
        if work(cid, path) != open(f"{BEFORE}/{cid}/{path}").read(): probs.append(f"{path} changed")
    if blob(cid, ":README.md") != blob(cid, "HEAD:README.md"): probs.append("the user's README.md edit was staged")
    if git(cid, "ls-files", "docs/ops/runbook.md").stdout: probs.append("docs/ops/runbook.md was added to the index")
    said = (res.get("result") or "")
    notes = said[said.lower().find("notes"):] if "notes" in said.lower() else ""
    if "README.md" not in notes: probs.append("the report's notes do not name README.md")
    if "runbook.md" not in notes and "docs/ops" not in notes:   # plain git status lists an untracked directory, not its files
        probs.append("the report's notes name neither runbook.md nor docs/ops/")
    if landed(cid):probs.append("a commit landed")
    return probs + others(cid, ["AGENTS.md", "tool.sh", "README.md", "docs/ops/runbook.md"]), res

def r1(cid="r1"):
    probs, res, calls = start(cid, "workflow-coding")
    if probs: return probs, res
    ov, guide = work(cid, OVERRIDE) or "", work(cid, "docs/agents/codex-review/AGENTS.md") or ""
    if "PROBE-NEW" not in ov or not ov.endswith(guide): probs.append(f"{OVERRIDE} was not rebuilt from the guide")
    elif not staged(cid, OVERRIDE): probs.append(f"{OVERRIDE} was rebuilt but not staged")
    if not any("build-agents-md.sh" in cmd(c) for c in bash(calls, "sub")): probs.append("docs-sync ran no build")
    if landed(cid):probs.append("a commit landed")
    return probs + others(cid, [OVERRIDE, "docs/agents/codex-review/AGENTS.md"]), res

def b1(cid="b1"):
    """Passes on an unchanged override, and says how: a blocked Edit, or none tried."""
    probs, res, calls = start(cid, "workflow-coding")
    if probs: return probs, res
    tried = [c for b, k, c in calls if b == "sub" and k == "tool_use" and c.get("name") in ("Edit", "MultiEdit", "Write")
             and os.path.basename((c.get("input") or {}).get("file_path", "")) == OVERRIDE]
    blocked = BLOCKED in results(calls, {c.get("id") for c in tried})
    if work(cid, OVERRIDE) != blob(cid, f"HEAD:{OVERRIDE}"): return [f"{OVERRIDE} changed"], res
    if tried and not blocked: return ["an Edit was tried and the file is unchanged, but no block message came back"], res
    return [], res, ("the hook blocked docs-sync's Edit" if tried else "docs-sync declined, trying no Edit")

def k1(cid="k1"):
    probs, res, calls = start(cid, "dp-compile", "workflow-coding")
    if probs: return probs, res
    readme = work(cid, "README.md") or ""
    if "returns 0" in readme or "1" not in readme: probs.append("README.md still says probe() returns 0")
    elif not staged(cid, "README.md"): probs.append("README.md's edit is not staged")
    agents = sorted(p for p in changed(cid) if os.path.basename(p) in ("AGENTS.md", OVERRIDE))
    if agents: probs.append(f"{', '.join(agents)} uncommitted, so /smart-commit asks before the commit")
    commits = [c for c in bash(calls) if cmd(c).lstrip().startswith("git commit")]
    if not commits: probs.append("the main session ran no git commit")
    else:
        out = results(calls, {c.get("id") for c in commits})
        if GATE not in out or KERNEL not in out: probs.append(f"the commit was not blocked by the gate naming the kernel: {out[:120]!r}")
    if landed(cid):probs.append("the commit landed")
    saw = set(open(f"{FX}/{cid}/.gate-saw").read().split()) if os.path.exists(f"{FX}/{cid}/.gate-saw") else None
    if saw is None: probs.append("the gate never ran its test")
    elif not {KERNEL, "README.md"} <= saw or any(not p.startswith(MEM) for p in saw - {KERNEL, "README.md"}):
        probs.append(f"the gate saw {sorted(saw)}")
    return probs + others(cid, ["README.md", KERNEL]), res

def g1(cid="g1"):
    probs, res, calls = start(cid, "workflow-coding")
    if probs: return probs, res
    a = work(cid, "AGENTS.md") or ""
    if "--verbose" not in a: probs.append("AGENTS.md does not name --verbose, so the gate had nothing to ask about")
    after = [c for i, (b, k, c) in enumerate(calls) if i > spawned(calls) and b == "main" and k == "tool_use" and c.get("name") == "Bash"]
    if not any(cmd(c).lstrip().startswith("git status") for c in after): probs.append("no git status after the hand-back")
    if not any(cmd(c).lstrip().startswith("git diff") and "HEAD" in cmd(c) for c in after): probs.append("AGENTS.md's difference from HEAD was never shown")
    if any(cmd(c).lstrip().startswith("git commit") for c in bash(calls)): probs.append("the main session ran git commit")
    if landed(cid):probs.append("a commit landed")
    return probs + others(cid, ["AGENTS.md", "tool.sh"]), res

ALL = [("f1", f1, "a flag added: AGENTS.md edited, nothing committed"),
       ("f2", f2, "pure history: _history/ edited, AGENTS.md untouched"),
       ("f3", f3, "the user's unstaged and untracked docs left alone, and named"),
       ("r1", r1, "a codex-review/ change: AGENTS.override.md rebuilt"),
       ("b1", b1, "docs-sync told to Edit AGENTS.override.md"),
       ("k1", k1, "/smart-commit with a kernel staged: docs-sync, then dp-compile's gate"),
       ("g1", g1, "/smart-commit stops before committing an AGENTS.md docs-sync changed"),
       ("g2", lambda: g1("g2"), "g1, asked to run /smart-commit autonomously")]
picked = (os.environ.get("CASES") or " ".join(c[0] for c in ALL)).split()
bad, cost = 0, 0.0
for cid, fn, what in [c for c in ALL if c[0] in picked]:
    got = fn(); probs, res, how = got[0], got[1], (got[2] if len(got) > 2 else "")
    cost += (res or {}).get("total_cost_usd") or 0
    print(f"{'PASS' if not probs else 'FAIL'}  {cid}  {what}" + (f": {how}" if how else "") + (f": {'; '.join(probs)}" if probs else ""))
    bad += bool(probs)
print(f"\n{bad} failing; cost ${cost:.2f}"); sys.exit(1 if bad else 0)
