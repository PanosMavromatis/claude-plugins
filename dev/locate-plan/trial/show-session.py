"""Show one trial session in full: parent and agent tool calls with their results, models,
permission denials, and the reply. Reads the transcripts under ~/.claude/projects, so it
works only on the machine that ran the session. Read-only.

  LOCATE_PLAN_WORK=<dir> python3 -I show-session.py <arm> <run> <case>..."""
import glob, json, os, re, sys

P = os.path.realpath(os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to the suite's work directory"))
def proj(repo):
    return os.path.expanduser("~/.claude/projects/") + re.sub(r"[^A-Za-z0-9]", "-", f"{P}/{repo}")
def walk(path):
    uses, res, models = [], {}, set()
    for ln in open(path):
        e = json.loads(ln); m = e.get("message", {})
        if m.get("model"): models.add(m["model"])
        c = m.get("content")
        if not isinstance(c, list): continue
        for b in c:
            if b.get("type") == "tool_use": uses.append((b["id"], b["name"], b.get("input", {})))
            if b.get("type") == "tool_result":
                t = b.get("content"); t = t if isinstance(t, str) else " ".join(x.get("text", "") for x in t if isinstance(x, dict))
                res[b["tool_use_id"]] = (b.get("is_error"), t)
    return uses, res, models
def show(label, path):
    uses, res, models = walk(path)
    print(f"  [{label}] models={sorted(models)}")
    for i, n, inp in uses:
        err, t = res.get(i, (None, "<no result>"))
        arg = inp.get("command") or inp.get("file_path") or inp.get("pattern") or inp.get("subagent_type") or ""
        print(f"    {n}: {arg}".replace(P, "$WORK"))
        print(f"       {'ERROR' if err else 'ok'}: {t[:150]!r}".replace(P, "$WORK"))
if len(sys.argv) < 4: sys.exit(__doc__)
out = f"{P}/out-{sys.argv[1]}-{sys.argv[2]}"
for cid in sys.argv[3:]:
    _, repo, br, kind, args = open(f"{out}/{cid}.case").read().strip().split("|", 4)
    d = json.load(open(f"{out}/{cid}.json")); sid = d["session_id"]; pj = proj(repo)
    print(f"===== {cid} ({repo} {br}) {d['duration_ms']/1000:.1f} s, {d['num_turns']} turns, ${d['total_cost_usd']:.3f}")
    for den in d.get("permission_denials") or []:
        print("  DENIED:", den.get("tool_name"), str(den.get("tool_input"))[:200].replace(P, "$WORK"))
    show("parent", f"{pj}/{sid}.jsonl")
    for a in sorted(glob.glob(f"{pj}/{sid}/subagents/agent-*.jsonl")):
        meta = json.load(open(a[:-6] + ".meta.json")) if os.path.exists(a[:-6] + ".meta.json") else {}
        show(f"agent {meta.get('agentType')}", a)
    print("  reply:", d.get("result", "").replace(P, "$WORK")[:1800])
