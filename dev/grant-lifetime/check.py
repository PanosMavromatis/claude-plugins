"""Grade a grant-lifetime run.

  LOCATE_PLAN_WORK=<dir> RUN=<tag> [CASES="..."] python3 -I check.py

The g-cases: did each case's `touch probe-<n>` run, or was it denied? g0 is the control:
with no grant the write must be denied, or the run measures nothing. g1 and g3 invoke the
command and must run. g2, the next message with no command, is the measurement.

The a-cases: does a command's grant reach a subagent it spawns? Each write, the Edit of
AGENTS.md, `git add AGENTS.md` or `git commit`, is graded ran, denied, not tried, or tried
with no effect, for the actor the case names: a subagent's calls carry a parent_tool_use_id
in the stream-json, or, if the stream holds none, are read from the session's subagent
transcripts. a0 (no command) must be denied and a1 and a4 (the main session, under the
command) must run; a2 and a3 (a subagent, under the command) are the measurements.
Read-only: it reads the stream-json, those transcripts, the probe files and the fixtures."""
import glob, json, os, subprocess, sys

W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK")
RUN = os.environ.get("RUN") or sys.exit("set RUN=<tag>")
G = os.path.realpath(W) + "/grant"; OUT = f"{G}/out-{RUN}"; FX = f"{G}/fx-{RUN}"

def case(cid, n):
    """What became of case cid's `touch probe-<n>`: ran, denied, or why neither."""
    p, want = f"{OUT}/{cid}.jsonl", f"touch probe-{n}"
    if not os.path.exists(p): return "no session", None
    tried, res = False, None
    for line in open(p):
        try: d = json.loads(line)
        except ValueError: continue
        if d.get("type") == "result": res = d
        content = (d.get("message") or {}).get("content") if d.get("type") == "assistant" else None
        for c in content if isinstance(content, list) else []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and want in (c.get("input") or {}).get("command", ""):
                tried = True
    if res is None: return "no result", None
    if any(want in (x.get("tool_input") or {}).get("command", "") for x in res.get("permission_denials") or []):
        return "denied", res
    if os.path.exists(f"{FX}/probe-{n}"): return "ran", res
    return ("tried, no file" if tried else "not tried"), res

def text(content):  # a tool_result's content, flattened to one string
    if isinstance(content, str): return content
    return "\n".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in content or [])

def blocks(d):  # a record's message content, or nothing: some records carry message as a string
    m = d.get("message")
    content = m.get("content") if isinstance(m, dict) else None
    return [c for c in content if isinstance(c, dict)] if isinstance(content, list) else []

def stream(cid):
    """(session's result, [(by, kind, block)]): by is main or sub, kind tool_use or tool_result."""
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

def outcome(res, calls, by, picks, applied):
    """ran, denied, not tried, or tried with no effect, for by's tool calls that picks() matches."""
    tried = [c for b, k, c in calls if b == by and k == "tool_use" and picks(c)]
    if not tried: return "not tried"
    if applied(): return "ran"
    ids = {c.get("id") for c in tried}
    denied = {d.get("tool_use_id") for d in (res or {}).get("permission_denials") or []}
    if ids & denied or any(c.get("is_error") and "permission" in text(c.get("content")).lower()
                           for _, k, c in calls if k == "tool_result" and c.get("tool_use_id") in ids):
        return "denied"
    return "tried, no effect"

def mode(cid, calls):
    """How the subagent ran: background if its Agent call came back "Async agent launched",
    else foreground; and how many turns the session took, by its init records."""
    turns = 0
    for line in open(f"{OUT}/{cid}.jsonl"):
        try: d = json.loads(line)
        except ValueError: continue
        turns += d.get("type") == "system" and d.get("subtype") == "init"
    agents = {c.get("id") for b, k, c in calls if b == "main" and k == "tool_use" and c.get("name") in ("Agent", "Task")}
    if not agents: return "no subagent", turns
    bg = any("Async agent launched" in text(c.get("content")) for _, k, c in calls if k == "tool_result" and c.get("tool_use_id") in agents)
    return ("background" if bg else "foreground"), turns

def git(cid, *a): return subprocess.run(["git", *a], cwd=f"{FX}/{cid}", capture_output=True, text=True).stdout
def is_edit(c): return c.get("name") in ("Edit", "MultiEdit", "Write") and os.path.basename((c.get("input") or {}).get("file_path", "")) == "AGENTS.md"
def is_bash(word): return lambda c: c.get("name") == "Bash" and word in (c.get("input") or {}).get("command", "")

def edit_case(cid, by):
    res, calls = stream(cid)
    if res is None: return "no session", None, res
    e = outcome(res, calls, by, is_edit, lambda: "PROBE-NEW" in open(f"{FX}/{cid}/AGENTS.md").read())
    a = outcome(res, calls, by, is_bash("git add AGENTS.md"), lambda: "AGENTS.md" in git(cid, "diff", "--cached", "--name-only").split())
    return f"edit {e}, git add {a}", mode(cid, calls), res

def commit_case(cid, by):
    res, calls = stream(cid)
    if res is None: return "no session", None, res
    c = outcome(res, calls, by, is_bash("git commit"), lambda: git(cid, "rev-list", "--count", "HEAD").strip() == "2")
    return f"git commit {c}", mode(cid, calls), res

def g_case(cid, n):  # the g-cases, in the a-cases' shape: no subagent, so no mode
    g, res = case(cid, n)
    return g, None, res

EDITS = ("edit ran, git add ran", "edit denied, git add denied", "edit ran, git add denied", "edit denied, git add ran")
COMMITS = ("git commit ran", "git commit denied")
# id, grade, the verdicts it may give, the mode it must run in (None: any), what it is
ALL = [("g0", lambda: g_case("g0", 0), ("denied",), None, "control, no grant"),
       ("g1", lambda: g_case("g1", 1), ("ran",), None, "the turn that invokes the command"),
       ("g2", lambda: g_case("g2", 2), ("ran", "denied"), None, "the next message, no command"),
       ("g3", lambda: g_case("g3", 3), ("ran",), None, "the command invoked again"),
       ("a0", lambda: edit_case("a0", "sub"), ("edit denied, git add denied", "edit denied, git add not tried",
                                               "edit denied, git add tried, no effect"), None, "control: a subagent's edit, no command"),
       ("a1", lambda: edit_case("a1", "main"), ("edit ran, git add ran",), None, "control: the main session's edit, under the command"),
       ("a2", lambda: edit_case("a2", "sub"), EDITS, "background", "a background subagent's edit, under the command"),
       ("a2f", lambda: edit_case("a2f", "sub"), EDITS, "foreground", "a foreground subagent's edit, under the command"),
       ("a3", lambda: commit_case("a3", "sub"), COMMITS, "background", "a background subagent's commit, under the command"),
       ("a3f", lambda: commit_case("a3f", "sub"), COMMITS, "foreground", "a foreground subagent's commit, under the command"),
       ("a4", lambda: commit_case("a4", "main"), ("git commit ran",), None, "control: the main session's commit, under the command"),
       ("a5", lambda: commit_case("a5", "main"), COMMITS, "background", "the main session's commit after a background subagent returns"),
       ("a5f", lambda: commit_case("a5f", "main"), COMMITS, "foreground", "the main session's commit after a foreground subagent returns")]
picked = (os.environ.get("CASES") or "g0 g1 g2 g3").split()
bad, cost, got = 0, 0.0, {}
for cid, fn, verdicts, need, what in [c for c in ALL if c[0] in picked]:
    g, m, res = fn(); got[cid] = g
    cost += (res or {}).get("total_cost_usd") or 0
    ok = g in verdicts and (need is None or (m and m[0] == need))
    shown = f"{g}" + (f" ({m[0]}, {m[1]} turn{'' if m[1] == 1 else 's'})" if m else "")
    print(f"{'PASS' if ok else 'FAIL'}  {cid}  {what}: {shown}" + ("" if ok or need is None or (m and m[0] == need) else f", want {need}"))
    bad += not ok
if bad: print(f"\nresult: void, {bad} case(s) failed; cost ${cost:.2f}"); sys.exit(1)
found = []
if "g2" in got: found.append("the grant clears with the next message" if got["g2"] == "denied" else "the grant outlasts its turn")
for b, f, what in (("a2", "a2f", "a subagent's"), ("a3", "a3f", "a subagent's"), ("a5", "a5f", "after a hand-back, the main session's")):
    if b in got or f in got:
        found.append(f"under a command's grant, {what} {got.get(b, '—')} in the background and {got.get(f, '—')} in the foreground")
print("\nresult: " + ";\n  ".join(found) + f"\ncost ${cost:.2f}")
