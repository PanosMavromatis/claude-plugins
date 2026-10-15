"""Grade a subagent-hooks run: did each case's edit or commit land, and who tried it?

  LOCATE_PLAN_WORK=<dir> RUN=<tag> python3 -I check.py

h0 and h2 are the controls: the main session's edit of AGENTS.override.md must be blocked,
or the hook never loaded, and a subagent's edit of AGENTS.md must land, or a subagent cannot
edit at all. h1, a subagent's edit of AGENTS.override.md, is the measurement, and counts only
if the subagent itself attempted the Edit. d1 must end with the commit blocked by dp-compile's
gate, the kernel named, and AGENTS.md, staged by the subagent, in the set the gate saw.

A case whose session did not load the plugin it needs, by the init record's plugin list, is
reported as that, not as a result: a plugin whose dependency is missing is dropped silently.
A subagent's tool calls carry a parent_tool_use_id in the stream-json. If the stream holds
none, they are read from the session's subagent transcripts under ~/.claude/projects instead.
Read-only: it reads the stream-json, those transcripts and the fixtures."""
import glob, json, os, subprocess, sys

W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK")
RUN = os.environ.get("RUN") or sys.exit("set RUN=<tag>")
S = os.path.realpath(W) + "/subhooks"; OUT = f"{S}/out-{RUN}"; FX = f"{S}/fx-{RUN}"
BLOCKED = "Blocked: AGENTS.override.md is generated from docs/agents/codex-review/AGENTS.md"
GATE = "dp-compile: [commands].test failed — commit blocked."
KERNEL = "src/probe_python.py"

def text(content):  # a tool_result's content, flattened to one string
    if isinstance(content, str): return content
    return "\n".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in content or [])

def records(cid):
    """(session's result, [(by, kind, block)]): by is 'main' or 'sub', kind tool_use or tool_result."""
    p = f"{OUT}/{cid}.jsonl"
    if not os.path.exists(p): return None, []
    res, sid, calls = None, None, []
    for line in open(p):
        try: d = json.loads(line)
        except ValueError: continue
        sid = sid or d.get("session_id")
        if d.get("type") == "result": res = d
        by = "sub" if d.get("parent_tool_use_id") else "main"
        for c in ((d.get("message") or {}).get("content") or []) if isinstance((d.get("message") or {}).get("content"), list) else []:
            if isinstance(c, dict) and c.get("type") in ("tool_use", "tool_result"): calls.append((by, c["type"], c))
    if sid and not any(by == "sub" for by, _, _ in calls):   # the stream carried no subagent messages
        for t in glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}/subagents/*.jsonl")):
            for line in open(t):
                try: d = json.loads(line)
                except ValueError: continue
                content = (d.get("message") or {}).get("content")
                for c in content if isinstance(content, list) else []:
                    if isinstance(c, dict) and c.get("type") in ("tool_use", "tool_result"): calls.append(("sub", c["type"], c))
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

def edits(calls, by, name):  # Edit calls by main or sub on a file named name, and whether any result says blocked
    tried = [c for b, k, c in calls if b == by and k == "tool_use" and c.get("name") in ("Edit", "MultiEdit", "Write")
             and os.path.basename((c.get("input") or {}).get("file_path", "")) == name]
    ids = {c.get("id") for c in tried}
    blocked = any(BLOCKED in text(c.get("content")) for _, k, c in calls if k == "tool_result" and c.get("tool_use_id") in ids)
    return tried, blocked

def edit_case(cid, by, name):
    res, calls = records(cid)
    if res is None: return "no session", res
    if missing(cid, "workflow-coding"): return missing(cid, "workflow-coding"), res
    tried, blocked = edits(calls, by, name)
    if not tried: return f"no Edit of {name} by the {'subagent' if by == 'sub' else 'main session'}", res
    new = "PROBE-NEW" in open(f"{FX}/{cid}/{name}").read()
    if new and not blocked: return "edited", res
    if blocked and not new: return "blocked", res
    return f"unclear: blocked message {blocked}, file changed {new}", res

def gate_case(cid):
    res, calls = records(cid)
    if res is None: return "no session", res
    if missing(cid, "dp-compile", "workflow-coding"): return missing(cid, "dp-compile", "workflow-coding"), res
    staged = any(b == "sub" and k == "tool_use" and c.get("name") == "Bash" and "git add AGENTS.md" in (c.get("input") or {}).get("command", "")
                 for b, k, c in calls)
    commits = [c for b, k, c in calls if b == "main" and k == "tool_use" and c.get("name") == "Bash"
               and "git commit" in (c.get("input") or {}).get("command", "")]
    if not staged: return "the subagent did not stage AGENTS.md", res
    if not commits: return "the main session ran no git commit", res
    out = " ".join(text(c.get("content")) for _, k, c in calls if k == "tool_result" and c.get("tool_use_id") in {x.get("id") for x in commits})
    n = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=f"{FX}/{cid}", capture_output=True, text=True).stdout.strip()
    saw = open(f"{FX}/{cid}/.gate-saw").read().split() if os.path.exists(f"{FX}/{cid}/.gate-saw") else None
    if n != "1": return "the commit landed", res
    if saw is None: return "the gate never ran its test", res
    if GATE not in out or KERNEL not in out: return f"the commit was refused, but not by the gate naming the kernel: {out[:120]!r}", res
    if sorted(saw) != sorted([KERNEL, "AGENTS.md"]): return f"the gate saw {saw}", res
    return "blocked, naming the kernel, with AGENTS.md staged", res

CASES = [("h0", lambda: edit_case("h0", "main", "AGENTS.override.md"), "blocked", "control: the main session edits AGENTS.override.md"),
         ("h1", lambda: edit_case("h1", "sub", "AGENTS.override.md"), None, "a subagent edits AGENTS.override.md"),
         ("h2", lambda: edit_case("h2", "sub", "AGENTS.md"), "edited", "control: a subagent edits AGENTS.md"),
         ("d1", lambda: gate_case("d1"), "blocked, naming the kernel, with AGENTS.md staged", "the gate after a subagent stages a doc")]
bad, cost, got = 0, 0.0, {}
for cid, fn, want, what in CASES:
    g, res = fn(); got[cid] = g
    cost += (res or {}).get("total_cost_usd") or 0
    ok = g == want if want else g in ("blocked", "edited")
    print(f"{'PASS' if ok else 'FAIL'}  {cid}  {what}: {g}" + ("" if ok or not want else f", want {want}"))
    bad += not ok
if bad: print(f"\nresult: void or failing, {bad} case(s); cost ${cost:.2f}"); sys.exit(1)
print(f"\nresult: protect-agent-docs.py {'fires' if got['h1'] == 'blocked' else 'does not fire'} on a subagent's Edit;"
      f" dp-compile's gate sees the docs a subagent stages; cost ${cost:.2f}")
