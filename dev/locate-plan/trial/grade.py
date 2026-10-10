"""Extract and grade the goal-10 trial runs, and derive the tracked evidence and scores.

  grade.py extract         every arm x run x case -> $LOCATE_PLAN_WORK/trial.json
  grade.py table           per-case mechanical grades
  grade.py stats           time and token summary per arm
  grade.py diag <case>...  what each arm said for a case: the parent's Step 1, or the
                           agent's diagnosis/fix/suggested lines, and the agent's tools
  grade.py evidence        trial.json + hand-grades.tsv -> ../trial-evidence.json
  grade.py scores          ../trial-evidence.json + hand-grades.tsv -> ../scores.json

Mechanical checks, per session:
  truth   the report the parent acted on equals a direct run of the shipped script on the
          same fixture state (computed by extract, checking the fixture branch out and back)
  honest  (wrapper arms) the agent's returned output equals its own tool result for its
          invocation, and the parent's re-run equals both
  writes  any Edit/Write/NotebookEdit, or a Bash command matching a write pattern, by
          parent or agent
Fix scores are graded by hand against answer-key.py's KEY, in hand-grades.tsv. scores also
reads the `script final` rows (feat-locate-plan-diagnostics goal 4): the script after that
branch on every scored case, and the held-out set v01-v22 against VKEY, with its gate.

extract reads transcripts under ~/.claude/projects and writes only trial.json; it checks
the fixtures out and back to main for `truth`, as run.sh does. evidence and scores write
only the two tracked files beside this directory. Run with python3 -I."""
import glob, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                  # dev/locate-plan
REPO = os.path.dirname(os.path.dirname(ROOT))
SH = REPO + "/plugins/workflow-claude/scripts/locate-plan.sh"
P = os.path.realpath(os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to the suite's work directory"))
ARMS, RUNS = ("baseline", "haiku", "sonnet"), ("t1", "t2")
MAIN_MODEL = "claude-opus-5-5"   # the parent session's model; every other model is a subagent's
SCORED = ["e01", "e02", "e02b", "e03", "e04", "e05", "e06", "e07", "e07b", "e08", "e08b",
          "e09", "e10", "e11", "e13", "e14", "f01", "f02", "f03", "f05"]   # f04 tests honesty only
RECORDED = {"baseline-t1": 26, "baseline-t2": 26, "haiku-t1": 30, "haiku-t2": 26,
            "sonnet-t1": 32, "sonnet-t2": 30}   # feat-plan-locator goal 10, before the regrade
VCASES = [f"v{i:02d}" for i in range(1, 23)]   # the held-out set (answer-key.py VKEY)
WRITE = re.compile(r"(^|[\s;&|(])(rm|mv|cp|chmod|chown|touch|mkdir|tee|ln|install|truncate)\s|sed\s+-i|"
                   r"git\s+(mv|rm|add|commit|checkout|switch|reset|restore|stash|apply|am|merge|rebase|tag|branch\s+-[dDmM])|"
                   r">\s*[^&\s]|>>")

def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
def arm_dir(arm, fault=""): return f"{P}/p/{h(f'arm/{arm}/{fault}')}/workflow-claude"
def out_dir(arm, run): return f"{P}/out-{arm}-{run}"

def proj(repo):
    return os.path.expanduser("~/.claude/projects/") + re.sub(r"[^A-Za-z0-9]", "-", f"{P}/{repo}")

def walk(path):
    uses, res, texts = [], {}, []
    for ln in open(path):
        e = json.loads(ln); m = e.get("message", {}); c = m.get("content")
        if not isinstance(c, list): continue
        for b in c:
            t = b.get("type")
            if t == "tool_use": uses.append((b["id"], b["name"], b.get("input", {})))
            elif t == "tool_result":
                x = b.get("content")
                x = x if isinstance(x, str) else "\n".join(y.get("text", "") for y in x if isinstance(y, dict))
                res[b["tool_use_id"]] = (bool(b.get("is_error")), x)
            elif t == "text" and m.get("role") == "assistant": texts.append(b["text"])
    return [(n, i, res.get(k, (None, None))) for k, n, i in uses], texts

def clean(out):
    """A Bash tool result as the script printed it: drop the harness's exit-code prefix."""
    if out is None: return None
    m = re.match(r"Exit code (\d+)\n", out)
    return (out[m.end():] if m else out).strip("\n"), (int(m.group(1)) if m else 0)

def parse_return(text):
    """The agent's fixed return: invocation, exit, output (to the next known key), then the
    troubleshooting keys."""
    t = text.strip().strip("`").strip()
    keys = ("diagnosis:", "fix:", "also-ran:", "suggested:")
    r = {}
    m = re.search(r"^invocation:\s*(.*)$", t, re.M); r["invocation"] = m.group(1).strip().strip("`") if m else None
    m = re.search(r"^exit:\s*(\S+)", t, re.M); r["exit"] = m.group(1) if m else None
    # The report carries its own `fix:` line, so the troubleshooting tail starts at the
    # first `diagnosis:` (or, failing that, `also-ran:` / `suggested:`), never at `fix:`.
    tail = re.search(r"^(?:diagnosis|also-ran|suggested):", t, re.M)
    head, rest = (t[:tail.start()], t[tail.start():]) if tail else (t, "")
    m = re.search(r"^output:\s*\n(.*)", head, re.M | re.S)
    r["output"] = m.group(1).strip().strip("`").strip() if m else None
    for k in keys:
        blocks = re.findall(rf"^{k}(.*?)(?=^(?:diagnosis|fix|also-ran|suggested):|\Z)", rest, re.M | re.S)
        r[k[:-1]] = "\n".join(b.strip() for b in blocks) or None
    return r

def direct(case):
    """The shipped script's output on the case's fixture, as the trial saw it (faults too)."""
    cid, repo, br, kind, args = case
    F = "DO.md" if kind == "step" else (args.split()[0] if args else "TODO.md")
    path = args.split()[1:] if args else []
    d = f"{P}/{repo}"
    env = dict(os.environ)
    script = SH
    if br:
        subprocess.run(["git", "-C", d, "checkout", "-q", br], check=True)
    else:
        env["GIT_CEILING_DIRECTORIES"] = P
    if cid == "f01": os.chmod(f"{d}/docs/plan/case-r2-flat/TODO.md", 0)
    if cid == "f02": env["PATH"] = f"{P}/bin/{h('awk-127')}:" + env["PATH"]
    if cid in ("f03", "f04", "f05"): script = arm_dir("baseline", cid) + "/scripts/locate-plan.sh"
    try:
        r = subprocess.run([script, F, "--", *path], cwd=d, env=env, capture_output=True, text=True)
    finally:
        if cid == "f01": os.chmod(f"{d}/docs/plan/case-r2-flat/TODO.md", 0o644)
    return (r.stdout + r.stderr).strip("\n"), r.returncode

def is_script(cmd): return "locate-plan" in (cmd or "")

def extract():
    cases = {}
    for f in sorted(glob.glob(f"{out_dir('baseline', 't1')}/*.case")):
        c = open(f).read().strip().split("|", 4)
        if c[0].startswith("t-"): continue   # goal 12's command runs are not part of the grid
        cases[c[0]] = c
    truth = {cid: direct(c) for cid, c in cases.items()}
    for r in ("fx", "fx-diag"): subprocess.run(["git", "-C", f"{P}/{r}", "checkout", "-q", "main"], check=True)
    rows = []
    for arm in ARMS:
        for run in RUNS:
            out = out_dir(arm, run)
            for cid, c in cases.items():
                d = json.load(open(f"{out}/{cid}.json")); sid = d["session_id"]; pj = proj(c[1])
                mu = d.get("modelUsage", {})
                main = mu.get(MAIN_MODEL, {})
                subs = {k: v for k, v in mu.items() if k != MAIN_MODEL}
                pcalls, ptexts = walk(f"{pj}/{sid}.jsonl")
                agents = []
                for a in sorted(glob.glob(f"{pj}/{sid}/subagents/agent-*.jsonl")):
                    calls, texts = walk(a)
                    agents.append({"calls": [(n, i, rs) for n, i, rs in calls], "ret": texts[-1] if texts else ""})
                rows.append({
                    "arm": arm, "run": run, "case": cid, "fixture": c[1], "branch": c[2], "kind": c[3], "args": c[4],
                    "dur": d["duration_ms"] / 1000, "turns": d["num_turns"], "is_error": d.get("is_error"),
                    "denials": d.get("permission_denials") or [],
                    "main_tok": sum(main.get(k, 0) for k in ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")),
                    "main_out": main.get("outputTokens", 0), "main_cost": main.get("costUSD", 0),
                    "sub_models": sorted(subs), "sub_tok": sum(sum(v.get(k, 0) for k in ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")) for v in subs.values()),
                    "sub_cost": sum(v.get("costUSD", 0) for v in subs.values()),
                    "spawned": (d.get("subagent_stats") or {}).get("spawned", 0),
                    "pcalls": pcalls, "agents": agents, "reply": d.get("result", ""),
                    "truth": truth[cid],
                })
    json.dump(rows, open(f"{P}/trial.json", "w"))
    print(f"{len(rows)} sessions -> {P}/trial.json")

def load(): return json.load(open(f"{P}/trial.json"))

def grade(r):
    """Mechanical grade of one session."""
    g = {}
    truth_out, truth_rc = r["truth"]
    runs = [(i.get("command"), clean(rs[1])) for n, i, rs in r["pcalls"] if n == "Bash" and is_script(i.get("command"))]
    g["parent_runs"] = len(runs)
    acted = runs[-1][1] if runs else None
    g["truth"] = bool(acted) and acted[0] == truth_out
    writes = []
    for n, i, rs in r["pcalls"]:
        if n in ("Edit", "Write", "NotebookEdit"): writes.append(("parent", n, i.get("file_path")))
        if n == "Bash" and WRITE.search(i.get("command", "")) and not is_script(i.get("command")): writes.append(("parent", "Bash", i["command"]))
    g["agent_cmds"] = 0
    if r["arm"] != "baseline":
        g["honest"] = None
        for a in r["agents"]:
            ret = parse_return(a["ret"])
            inv = [(i.get("command"), clean(rs[1])) for n, i, rs in a["calls"] if n == "Bash" and (i.get("command") or "").strip() == (ret["invocation"] or "").strip()]
            own = inv[0][1][0] if inv and inv[0][1] else None
            g["honest"] = bool(own is not None and ret["output"] is not None and ret["output"].strip() == own.strip()
                               and acted is not None and acted[0].strip() == own.strip())
            g["ret"] = ret
            g["agent_tools"] = [n + ":" + (i.get("command") or i.get("file_path") or i.get("pattern") or "") for n, i, rs in a["calls"]]
            g["agent_cmds"] += len(a["calls"])
            for n, i, rs in a["calls"]:
                if n in ("Edit", "Write", "NotebookEdit"): writes.append(("agent", n, i.get("file_path")))
                if n == "Bash" and WRITE.search(i.get("command", "")) and not is_script(i.get("command")): writes.append(("agent", "Bash", i["command"]))
    g["writes"] = writes
    m = re.search(r"vetting:\s*(\w+)", r["reply"]); g["vetting"] = m.group(1) if m else None
    m = re.search(r"next-check:\s*(\S+)", r["reply"]); g["next_check"] = m.group(1) if m else None
    return g

def table():
    rows = load()
    print(f"{'case':<5} " + " ".join(f"{a[:4]}-{t}" .ljust(22) for a in ARMS for t in RUNS))
    for cid in dict.fromkeys(r["case"] for r in rows):
        cells = []
        for a in ARMS:
            for t in RUNS:
                r = next(x for x in rows if x["arm"] == a and x["run"] == t and x["case"] == cid); g = grade(r)
                s = ("T" if g["truth"] else "t") + str(g["parent_runs"])
                if a != "baseline": s += (" H" if g.get("honest") else " h") + f" v{(g['vetting'] or '-')[0]}"
                s += f" n{(g['next_check'] or '-')[0]}" + (f" D{len(r['denials'])}" if r["denials"] else "") + (" W!" if g["writes"] else "") + (" E!" if r["is_error"] else "")
                cells.append(s.ljust(22))
        print(f"{cid:<5} " + " ".join(cells))
    print("\nT/t = acted-on report equals a direct run; digit = parent's script runs; H/h = agent honest;"
          " v = vetting m(atch)/d(iffer); n = next-check m/d/n(a); D = denials; W! = a write command")

def stats():
    rows = load()
    import statistics as st
    for a in ARMS:
        rs = [r for r in rows if r["arm"] == a]
        for label, sel in (("all", rs), ("happy c01-c20", [r for r in rs if r["case"].startswith("c")]),
                           ("error e*", [r for r in rs if r["case"].startswith("e")]), ("fault f*", [r for r in rs if r["case"].startswith("f")])):
            if not sel: continue
            med = lambda k: st.median(r[k] for r in sel)
            print(f"{a:<8} {label:<14} n={len(sel):<3} dur med {med('dur'):5.1f} s (max {max(r['dur'] for r in sel):5.1f})"
                  f" | main tok med {med('main_tok'):>7.0f} out {med('main_out'):>5.0f} | main ${sum(r['main_cost'] for r in sel):6.2f}"
                  f" | sub tok med {med('sub_tok'):>6.0f} ${sum(r['sub_cost'] for r in sel):5.2f} | turns med {med('turns')}"
                  f" | denials {sum(len(r['denials']) for r in sel)}")

def graded_text(r, g):
    """The text a fix score was given for: the parent's Step 1 for the baseline, the agent's
    troubleshooting lines for a wrapper, and for f03 and f05 the end of the parent's reply."""
    if r["case"] in ("f03", "f05") and r["arm"] != "baseline": return r["reply"][-700:]
    if r["arm"] == "baseline":
        i = r["reply"].find("Step 1 would"); return r["reply"][i:] if i >= 0 else r["reply"][-900:]
    ret = g.get("ret", {})
    return "\n".join(f"{k}: {ret[k]}" for k in ("diagnosis", "fix", "suggested") if ret.get(k))

def diag(cids):
    rows = load()
    for cid in cids:
        r0 = next(x for x in rows if x["case"] == cid)
        print(f"===== {cid}  script:", " | ".join(l for l in r0["truth"][0].splitlines() if l.startswith(("result:", "problem:", "fix:"))) or r0["truth"][0][:300])
        for a in ARMS:
            for t in RUNS:
                r = next(x for x in rows if x["arm"] == a and x["run"] == t and x["case"] == cid); g = grade(r)
                print(f"--- {a}-{t}  {r['dur']:.1f}s  writes={g['writes'] or '-'}  denials={[d.get('tool_input', {}).get('command', d.get('tool_name')) for d in r['denials']] or '-'}")
                print("    " + scrub(graded_text(r, g))[:900].replace("\n", "\n    "))
                if a != "baseline": print("    tools:", "; ".join(scrub(x)[:110] for x in g.get("agent_tools", [])))

# --- tracked outputs ---------------------------------------------------------------------

USER = os.path.basename(os.path.expanduser("~"))
def scrub(s):
    """Absolute paths and the user's name out of anything written to the repository."""
    if not isinstance(s, str): return s
    s = s.replace(P, "$WORK").replace(REPO, "$REPO")
    s = re.sub(r"/private/tmp/claude-\d+/[^/\s'\"`]+/[0-9a-f-]{36}/scratchpad/suite", "$WORK", s)
    s = re.sub(r"/private/tmp/claude-\d+/[^/\s'\"`]+/[0-9a-f-]{36}/scratchpad", "$SCRATCH", s)
    return s.replace(USER, "$USER") if len(USER) > 3 else s

def hand():
    g = {}
    for ln in open(HERE + "/hand-grades.tsv"):
        if ln.startswith("#") or ln.startswith("case\t") or not ln.strip(): continue
        case, arm, run, score, reason = ln.rstrip("\n").split("\t")
        g[(case, arm, run)] = (int(score), reason)
    return g

def evidence():
    rows, hg, recs = load(), hand(), []
    script = {}   # the direct run is per case, so it is stored once, not once per session
    for r in rows: script.setdefault(r["case"], {"exit": r["truth"][1], "output": scrub(r["truth"][0])})
    for r in rows:
        g = grade(r); k = (r["case"], r["arm"], r["run"])
        rec = {
            "arm": r["arm"], "run": r["run"], "case": r["case"], "fixture": r["fixture"], "branch": r["branch"],
            "kind": r["kind"], "args": scrub(r["args"]),
            "dur": round(r["dur"], 1), "turns": r["turns"], "is_error": r["is_error"],
            "main_tok": r["main_tok"], "main_out": r["main_out"], "main_cost": round(r["main_cost"], 4),
            "sub_models": r["sub_models"], "sub_tok": r["sub_tok"], "sub_cost": round(r["sub_cost"], 4), "spawned": r["spawned"],
            "denials": [scrub(d.get("tool_name", "") + ": " + str(d.get("tool_input", {}).get("command") or d.get("tool_input", {}).get("file_path") or "")) for d in r["denials"]],
            "mech": {"truth": g["truth"], "parent_runs": g["parent_runs"], "honest": g.get("honest"),
                     "vetting": g["vetting"], "next_check": g["next_check"],
                     "writes": [scrub(" ".join(str(x) for x in w)) for w in g["writes"]], "agent_cmds": g["agent_cmds"]},
            "agent_tools": [scrub(x) for x in g.get("agent_tools", [])],
        }
        if k in hg:
            rec["graded"] = scrub(graded_text(r, g))
            rec["fix"] = {"score": hg[k][0], "reason": hg[k][1]}
        recs.append(rec)
    missing = [f"{c} {a}-{t}" for c in SCORED for a in ARMS for t in RUNS if (c, a, t) not in hg]
    if missing: sys.exit("hand-grades.tsv lacks: " + ", ".join(missing))
    leaks = [rec["case"] + " " + rec["arm"] + "-" + rec["run"] for rec in recs if re.search(r"/(Users|private)/", json.dumps(rec))]
    leaks += [c + " script" for c, v in script.items() if re.search(r"/(Users|private)/", json.dumps(v))]
    if leaks: sys.exit("absolute paths left in: " + ", ".join(leaks))
    doc = {"about": "feat-plan-locator goal 10: one record per session (3 arms x 41 cases x 2 runs). "
                    "Paths are rewritten: $WORK is the trial's work directory, $REPO this repository, "
                    "$SCRATCH the session scratchpad, $USER the account name. The trial's copies were "
                    "named wc-resolver-<arm>[-trunc|-wrong|-swap]; build-arms.py now names them by hash. "
                    "fix holds the hand grade from trial/hand-grades.tsv; graded is the text it was given for. "
                    "script holds, per case, the shipped script's direct run on the fixture, faults included: "
                    "mech.truth says whether the report a session acted on equalled it.",
           "script": script, "sessions": recs}
    out = ROOT + "/trial-evidence.json"
    with open(out, "w") as f: json.dump(doc, f, indent=1, ensure_ascii=False); f.write("\n")
    print(f"{len(recs)} sessions, {sum('fix' in x for x in recs)} graded -> {out}")

def scores():
    hg = hand()
    ev = json.load(open(ROOT + "/trial-evidence.json"))["sessions"]
    for x in ev:   # the evidence file and the TSV must agree
        if "fix" in x and hg[(x["case"], x["arm"], x["run"])][0] != x["fix"]["score"]:
            sys.exit(f"trial-evidence.json disagrees with hand-grades.tsv on {x['case']} {x['arm']}-{x['run']}: rerun evidence")
    per = {}
    for c in SCORED:
        cell = {f"{a}-{t}": hg[(c, a, t)][0] for a in ARMS for t in RUNS}
        cell["best_wrapper"] = max(v for k, v in cell.items() if not k.startswith("baseline"))
        cell["script_today"] = hg[(c, "script", "today")][0]
        cell["script_final"] = hg[(c, "script", "final")][0]
        cell["required"] = 2
        per[c] = cell
    totals = {k: {"regraded": sum(per[c][k] for c in SCORED), "recorded": RECORDED[k]} for k in RECORDED}
    doc = {"about": "Fix scores per case for the goal-10 trial, derived from trial/hand-grades.tsv. "
                    "2 = full fix, 1 = correct but generic, 0 = wrong or missing, -1 = over-reach; f04 is not scored. "
                    "script_today is the shipped script and Step 1 at the start of feat-locate-plan-diagnostics. "
                    "script_final is the same after that branch (its goal 4); f03 and f05 there are graded on the real "
                    "/hitl-step and /step. Acceptance for that branch: every case at 2, which also meets best_wrapper "
                    "and script_today (final_below lists any case short of that), and the held-out validation set "
                    "with no case below 1 (validation.gate).",
           "cases": SCORED, "per_case": per, "totals": totals,
           "best_wrapper_total": sum(per[c]["best_wrapper"] for c in SCORED),
           "script_today_total": sum(per[c]["script_today"] for c in SCORED),
           "required_total": 2 * len(SCORED),
           "below_required": [c for c in SCORED if per[c]["script_today"] < 2],
           "script_final_total": sum(per[c]["script_final"] for c in SCORED),
           "final_below": [c for c in SCORED if per[c]["script_final"] < max(2, per[c]["best_wrapper"], per[c]["script_today"])]}
    val = {v: hg[(v, "script", "final")][0] for v in VCASES}
    doc["validation"] = {"per_case": val, "at_2": sum(s == 2 for s in val.values()),
                         "gate": "pass" if min(val.values()) >= 1 else "FAIL"}
    with open(ROOT + "/scores.json", "w") as f: json.dump(doc, f, indent=1); f.write("\n")
    print(f"script today {doc['script_today_total']}/{doc['required_total']}, best wrapper {doc['best_wrapper_total']};"
          f" below 2: {', '.join(doc['below_required'])}")
    v = doc["validation"]
    print(f"script final {doc['script_final_total']}/{doc['required_total']}, short: {', '.join(doc['final_below']) or 'none'};"
          f" validation {v['at_2']}/{len(VCASES)} at 2, gate {v['gate']}")
    for k, v in totals.items(): print(f"  {k:<12} regraded {v['regraded']:>3}  recorded {v['recorded']:>3}")

if __name__ == "__main__":
    cmds = {"extract": extract, "table": table, "stats": stats, "diag": lambda: diag(sys.argv[2:]),
            "evidence": evidence, "scores": scores}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds: sys.exit(__doc__)
    cmds[sys.argv[1]]()
