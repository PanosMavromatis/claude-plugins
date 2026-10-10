"""Grade the per-goal end-to-end run: each scenario's fixture repository as the sessions left
it, and each session's tool calls from its stream-json.

  LOCATE_PLAN_WORK=<dir> RUN=<tag> python3 -I check.py [scenario...]   (default: all)

Read-only: it runs git reads and the plugin copy's own read-only scripts in the fixtures.
Prints PASS or FAIL per check, a line per finding worth reading (a denial, a Grep), and
exits non-zero if any check failed."""
import hashlib, json, os, re, subprocess, sys

W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK")
W = os.path.realpath(W); RUN = os.environ.get("RUN") or sys.exit("set RUN=<tag>")
E = W + "/e2e"; OUT = f"{E}/out-{RUN}"
PLUGIN = f"{E}/p/{hashlib.sha1(b'e2e/plugin').hexdigest()[:8]}/workflow-claude"
SCRIPTS = PLUGIN + "/scripts"
fails = 0
WANT = [a for a in sys.argv[1:] if re.match(r"^e\d$", a)] or ["e1", "e3", "e4", "e5"]

def sh(args, cwd):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True); return r.returncode, r.stdout, r.stderr
def git(repo, *a): return sh(["git", *a], f"{E}/{repo}")[1]
def report(out):
    rep, key = {}, None
    for line in out.splitlines():
        if line.startswith("  ") and key: rep[key].append(line[2:]); continue
        m = re.match(r"^([a-z-]+): (.*)$", line)
        if m: key = m.group(1); rep[key] = [m.group(2)]
    return rep
def check(name, ok, why=""):
    global fails
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {why}")); fails += not ok

def session(sid):
    """Tool calls in order, as (name, input), and the result record."""
    calls, result = [], None
    p = f"{OUT}/{sid}.jsonl"
    if not os.path.exists(p): return None, None
    for line in open(p):
        try: d = json.loads(line)
        except ValueError: continue
        if d.get("type") == "assistant":
            for c in d.get("message", {}).get("content", []):
                if c.get("type") == "tool_use": calls.append((c.get("name"), c.get("input") or {}))
        elif d.get("type") == "result": result = d
    return calls, result

def bash(calls): return [c[1].get("command", "") for c in calls if c[0] == "Bash"]
def edits(calls): return [(c[0], c[1].get("file_path", ""), c[1]) for c in calls if c[0] in ("Edit", "Write", "MultiEdit")]

def common(sid, gates=()):
    """Every session: it ran, it ran the copy, nothing was denied but a documented gate (a
    command matching one of `gates`, reported, not failed); Grep, Glob and shell searches
    are reported, since a session may lack Grep and Glob."""
    calls, res = session(sid)
    if res is None: check(f"{sid}: session ran", False, f"no result in {OUT}/{sid}.jsonl"); return []
    check(f"{sid}: session ended without error", not res.get("is_error"), str(res.get("result", ""))[:200])
    den = res.get("permission_denials") or []
    gated = [d for d in den if any(re.match(g, (d.get("tool_input") or {}).get("command", "")) for g in gates)]
    den = [d for d in den if d not in gated]
    for d in gated: print(f"      {sid}: a documented gate held: {(d.get('tool_input') or {}).get('command', '')[:120]}")
    check(f"{sid}: no permission denials" + (" beyond its documented gates" if gates else ""), not den,
          "; ".join(f"{d.get('tool_name')} {json.dumps(d.get('tool_input'))[:120]}" for d in den))
    cmds = bash(calls)
    plug = [c for c in cmds if "/scripts/" in c and ".sh" in c]
    check(f"{sid}: plugin scripts ran from the copy", all(c.split()[0].startswith(SCRIPTS) for c in plug) and bool(plug),
          f"{plug[:3]}")
    check(f"{sid}: no installed plugin touched", not any("/.claude/plugins/cache/" in c for c in cmds))
    g = [c[0] for c in calls if c[0] in ("Grep", "Glob")]
    shg = [c for c in cmds if re.match(r"^\s*(grep|rg|find)\b", c)]
    print(f"      {sid}: {len(calls)} tool calls; Grep/Glob {len(g)}; shell grep/rg/find {len(shg)}; turns {res.get('num_turns')}; ${res.get('total_cost_usd') or 0:.2f}")
    for c in shg[:5]: print(f"        shell search: {c[:140]}")
    return calls

def master_plan_change(repo, master, branch, item, after):
    """The subgoal starts on line `item` and its block ends on line `after`, where the backlink
    goes. A TODO.md master plan also has the subgoal flipped [ ] -> [~]; a DO.md one has no [~]
    and keeps its marker. Compared whole against the branch's copy, so nothing else may change."""
    lines = git(repo, "show", f"main:{master}").split("\n")
    flip = master.endswith("TODO.md")
    ok = lines[item - 1].startswith("- [ ] ")
    if flip: lines[item - 1] = lines[item - 1].replace("- [ ] ", "- [~] ", 1)
    lines.insert(after, f"  > **Branch:** {branch}")
    what = f"the subgoal on line {item} flipped to [~] and" if flip else "only"
    check(f"{repo}: {master} changed by {what} the backlink after line {after}",
          ok and git(repo, "show", f"{branch}:{master}") == "\n".join(lines),
          git(repo, "diff", "-U0", f"main..{branch}", "--", master).strip()[:300])

def goal_file_order(sid, calls, index):
    """Every index edit that changes goal NN's marker follows an edit to NN's goal file."""
    goal_n, bad = {}, []
    for name, path, inp in edits(calls):
        m = re.search(r"/(?:TODO|DO)/(\d+[a-z]?)-[^/]*\.md$", path)
        if m: goal_n[m.group(1)] = goal_n.get(m.group(1), 0) + 1; continue
        if path.endswith(index):
            for nn in re.findall(r"^- \[.\] (\d+[a-z]?) ", inp.get("old_string", "") or "", re.M):
                if not goal_n.get(nn): bad.append(nn)
    check(f"{sid}: goal file edited before its index line", not bad, f"index edited first for goal(s) {bad}")

def indents(repo, gdir):
    """A goal's own blockquotes sit at indent 0; an indented one before the first item is
    a legacy indent carried into a goal file."""
    bad = []
    if not os.path.isdir(f"{E}/{repo}/{gdir}"):
        check(f"{repo}: goal-level blockquotes at indent 0 in {gdir}", False, "no such directory"); return
    for f in sorted(os.listdir(f"{E}/{repo}/{gdir}")):
        seen_item = False
        for i, line in enumerate(open(f"{E}/{repo}/{gdir}/{f}"), 1):
            if re.match(r"^\s*- \[.\]", line): seen_item = True
            elif re.match(r"^\s+>", line) and not seen_item: bad.append(f"{f}:{i}")
    check(f"{repo}: goal-level blockquotes at indent 0 in {gdir}", not bad, ", ".join(bad))

def commits(repo, branch): return [l for l in git(repo, "log", "--format=%h %s", f"main..{branch}").splitlines()]

def per_goal(scen, repo, branch, model, files):
    flat = branch.replace("/", "-"); gd = model[:-3]
    idx = f"docs/plan/07-rev/{flat}/{model}"; master = f"docs/plan/07-rev/_{model}"
    s1 = common(scen)
    if s1:
        cmds = bash(s1)
        pi = next((i for i, c in enumerate(cmds) if "propose-branch-plan.sh" in c), None)
        ci = next((i for i, c in enumerate(cmds) if c.strip().startswith("git checkout -b")), None)
        check(f"{scen}: proposed before git checkout -b", pi is not None and ci is not None and pi < ci, f"propose {pi}, checkout {ci}")
        check(f"{scen}: the master plan was edited, not rewritten",
              not any(n == "Write" and p.endswith(master) for n, p, _ in edits(s1)), "a Write of the master plan")
    check(f"{repo}: on {branch}", git(repo, "branch", "--show-current").strip() == branch, git(repo, "branch", "--show-current"))
    first = git(repo, "log", "--reverse", "--format=%H", f"main..{branch}").split()
    got = set(git(repo, "show", "--name-only", "--format=", first[0]).split()) if first else set()
    gfs = sorted(f"docs/plan/07-rev/{flat}/{gd}/{f}" for f in os.listdir(f"{E}/{repo}/docs/plan/07-rev/{flat}/{gd}")) if os.path.isdir(f"{E}/{repo}/docs/plan/07-rev/{flat}/{gd}") else []
    want = {f"docs/git/{branch}.md", idx, master, *gfs}   # as /new-branch says: the branch name, unflattened
    check(f"{repo}: /new-branch committed the doc, index, {len(gfs)} goal files and the backlink", got == want and len(gfs) == 2,
          f"committed {sorted(got)}; want {sorted(want)}")
    master_plan_change(repo, master, branch, 9, 10)
    head = open(f"{E}/{repo}/{idx}").read() if os.path.exists(f"{E}/{repo}/{idx}") else ""
    for line in ("**Status**: active", "**Revision**: 07-rev", "**Layout**: per-goal", "**Subgoal**: 2. Plan directory structure"):
        check(f"{repo}: the index has `{line}`", line in head)
    s2 = common(f"{scen}-step")
    if s2:
        cmds = bash(s2)
        check(f"{scen}-step: re-ran locate-plan.sh between goals", sum("locate-plan.sh" in c for c in cmds) >= 2,
              f"{sum('locate-plan.sh' in c for c in cmds)} runs")
        check(f"{scen}-step: ran check-plan-index.sh", any("check-plan-index.sh" in c for c in cmds))
        goal_file_order(f"{scen}-step", s2, idx)
    rc, out, _ = sh([f"{SCRIPTS}/check-plan-index.sh", model, "--", idx], f"{E}/{repo}")
    r = report(out)
    check(f"{repo}: check-plan-index.sh: clean, nothing open", r.get("result") == ["clean"] and r.get("open") == ["—"], out[:400])
    for f, word in files:
        p = f"{E}/{repo}/{f}"
        check(f"{repo}: {f} holds `{word}`", os.path.exists(p) and word in open(p).read())
    indents(repo, f"docs/plan/07-rev/{flat}/{gd}")
    extra = commits(repo, branch)[:-1]
    print(f"      {repo}: commits after /new-branch's: {len(extra)} {extra}")

if "e1" in WANT:
  print(f"== e1: /new-branch inside a revision, then /hitl-step 2  ({E}/r1)")
  per_goal("e1", "r1", "feat/plan-dirs", "TODO.md", [("notes/structure.txt", "structure"), ("notes/layout.txt", "layout")])
if "e3" in WANT:
  print(f"\n== e3: the DO model: /new-branch, then /step 2  ({E}/r3)")
  per_goal("e3", "r3", "fix/do-tasks", "DO.md", [("a.txt", "a"), ("b.txt", "b")])

def e4():
    print(f"\n== e4: a legacy master plan: /new-branch, then /hitl-step 1  ({E}/r4)")
    s = common("e4")
    if s:
        check("e4: the master plan was edited, not rewritten", not any(n == "Write" and p.endswith("docs/plan/TODO.md") for n, p, _ in edits(s)))
    plan = "docs/plan/feat-legacy-notes/TODO.md"
    check("r4: on feat/legacy-notes", git("r4", "branch", "--show-current").strip() == "feat/legacy-notes")
    txt = open(f"{E}/r4/{plan}").read() if os.path.exists(f"{E}/r4/{plan}") else ""
    check("r4: a flat single-file plan, as before", bool(txt) and "**Layout**" not in txt and not os.path.exists(f"{E}/r4/docs/plan/feat-legacy-notes/TODO"), txt[:200])
    check("r4: the plan has `**Status**: active`", "**Status**: active" in txt)
    master_plan_change("r4", "docs/plan/TODO.md", "feat/legacy-notes", 9, 10)
    s2 = common("e4-step")
    if s2:
        cmds = bash(s2)
        check("e4-step: Step 6 ran check-plan-index.sh, and no awk", any("check-plan-index.sh" in c for c in cmds)
              and not any(c.strip().startswith("awk") for c in cmds), "; ".join(c[:80] for c in cmds if "awk" in c))
    rc, out, _ = sh([f"{SCRIPTS}/check-plan-index.sh", "TODO.md", "--", plan], f"{E}/r4")
    r = report(out)
    check("r4: check-plan-index.sh: clean, nothing open", r.get("result") == ["clean"] and r.get("open") == ["—"], out[:400])
    check("r4: the first goal is [x]", bool(re.search(r"^- \[x\] ", txt, re.M)), txt[:300])
    p = f"{E}/r4/notes/legacy.txt"; check("r4: notes/legacy.txt holds `legacy`", os.path.exists(p) and "legacy" in open(p).read())


def e5():
    print(f"\n== e5: an index left behind by an interrupted edit: /hitl-step 1  ({E}/r5)")
    s = common("e5")
    idx = "docs/plan/07-rev/feat-half-done/TODO.md"
    if s:
        said = " ".join(c[1].get("old_string", "") + c[1].get("new_string", "") for c in s if c[0] == "Edit" and c[1].get("file_path", "").endswith(idx))
        check("e5: the index line was rewritten from the goal file", "- [~] 01 —" in said or "- [x] 01 —" in said, said[:300])
        _, res = session("e5")
        check("e5: the session named the mismatch", bool(re.search(r"source of truth|differ|mismatch|\[~\]", (res or {}).get("result", ""))), (res or {}).get("result", "")[:300])
    rc, out, _ = sh([f"{SCRIPTS}/check-plan-index.sh", "TODO.md", "--", idx], f"{E}/r5")
    r = report(out)
    check("r5: index and goal files agree now", r.get("result") == ["clean"], out[:400])
    check("r5: goal 01 is done in both files, goal 02 untouched",
          "- [x] 01 —" in open(f"{E}/r5/{idx}").read() and "- [ ] 02 —" in open(f"{E}/r5/{idx}").read())
    p = f"{E}/r5/notes/half.txt"; check("r5: notes/half.txt holds `half`", os.path.exists(p) and "half" in open(p).read())


def merged(scen, repo, branch, idx, master, item, after):
    """The merge session, in the clone run.sh made: steps 2 and 7 went through the scripts,
    the index is stamped, the subgoal closed with its Done line right after the block, in
    one commit of exactly those two files, and the PR body names the plan. MCP was off, and
    any mcp__ call fails the session, since one could reach a real repository."""
    sid = f"{scen}-merge"; rm = repo + "m"
    print(f"\n== {sid}: /smart-merge on the branch {scen} left, fake gh, no MCP  ({E}/{rm})")
    # /smart-merge leaves the rm of the gh fallback's body file to the harness prompt, and a
    # session cannot be granted it (measured, run r4: denied despite --allowedTools).
    calls = common(sid, gates=(r"^rm /tmp/pr-body-[^/ ]+\.md$",))
    if calls:
        cmds = bash(calls)
        chained = [c for c in cmds if re.search(r";|&&|\|\||(^|[^|])\|([^|]|$)|2>&1", c) 
                   and not c.lstrip().startswith((SCRIPTS, "git commit", "gh pr create"))]   # message text is not chaining
        check(f"{sid}: every command ran alone", not chained, "; ".join(c[:100] for c in chained[:3]))
        for sc in ("locate-plan.sh", "check-plan-index.sh", "propose-merge-record.sh"):
            check(f"{sid}: ran {sc}", any(sc in c for c in cmds))
        pm = [c for c in cmds if "propose-merge-record.sh" in c]
        check(f"{sid}: propose-merge-record.sh was given the plan step 2 resolved", any(c.rstrip().endswith(f"-- {idx}") for c in pm), f"{pm[:2]}")
        mcp = [c[0] for c in calls if c[0].startswith("mcp__")]
        check(f"{sid}: no MCP calls", not mcp, f"{mcp[:3]}")
        init = next((d for d in map(lambda l: json.loads(l) if l.startswith("{") else {}, open(f"{OUT}/{sid}.jsonl"))
                     if d.get("type") == "system" and d.get("subtype") == "init"), {})
        srv = [m.get("name") for m in init.get("mcp_servers") or []]
        check(f"{sid}: MCP was off (no servers at init)", bool(init) and not srv, f"init {'found' if init else 'missing'}; servers {srv}")
        check(f"{sid}: no Grep or Glob", not any(c[0] in ("Grep", "Glob") for c in calls))
        check(f"{sid}: the master file was edited, not rewritten",
              not any(n == "Write" and p.endswith(master) for n, p, _ in edits(calls)), "a Write of the master file")
    if not os.path.isdir(f"{E}/{rm}/.git"): check(f"{rm}: the clone exists", False, f"{E}/{rm}"); return
    pre = git(rm, "rev-parse", "-q", "--verify", "refs/e2e/pre").strip()   # run.sh: the branch tip, with the step session's work
    if not pre: check(f"{rm}: run.sh marked the pre-merge tip", False, "no refs/e2e/pre: a clone from before run.sh made one"); return
    st = git(rm, "show", f"{branch}:{idx}").split("\n")
    check(f"{rm}: the index is stamped merged, PR #42", len(st) > 2 and bool(re.match(r"^\*\*Status\*\*: merged — PR #42 — \d{4}-\d\d-\d\d$", st[2])),
          st[2] if len(st) > 2 else "")
    want = git(rm, "show", f"{pre}:{master}").split("\n")
    got = git(rm, "show", f"{branch}:{master}").split("\n")
    if want[item - 1].startswith("- [~] ") or want[item - 1].startswith("- [ ] "): want[item - 1] = "- [x] " + want[item - 1][6:]
    done = got[after] if len(got) > after else ""
    want.insert(after, done)
    check(f"{rm}: {master}: only the subgoal on line {item} closed, and a Done line naming PR #42 after line {after}",
          got == want and done.startswith("  > **Done:** ") and "PR #42" in done,
          git(rm, "diff", "-U0", f"{pre}..{branch}", "--", master).strip()[:400])
    shas = git(rm, "log", "--format=%H", f"{pre}..{branch}").split()
    files = [sorted(git(rm, "show", "--name-only", "--format=", c).split()) for c in shas]
    check(f"{rm}: one commit records the merge, touching exactly the index and the master file",
          sorted([idx, master]) in files, f"{len(shas)} commits: {files}")
    check(f"{rm}: one commit removes the branch doc", [f"docs/git/{branch}.md"] in files, f"{files}")
    gfd = idx[:-len(os.path.basename(idx))] + os.path.basename(idx)[:-3]
    if os.path.isdir(f"{E}/{repo}/{gfd}"):
        check(f"{rm}: goal files untouched by the merge", not git(rm, "diff", "--name-only", f"{pre}..{branch}", "--", gfd).strip())
    log = open(f"{OUT}/{sid}.gh").read() if os.path.exists(f"{OUT}/{sid}.gh") else ""
    check(f"{sid}: gh pr create ran", "ARGV pr create" in log, log[:200])
    name = os.path.basename(os.path.dirname(idx))
    check(f"{sid}: the PR body names the plan", f"Plan: `{name}` under `docs/plan/`" in log, log[-300:])

if "e4" in WANT: e4()
if "e5" in WANT: e5()
if "e1" in WANT: merged("e1", "r1", "feat/plan-dirs", "docs/plan/07-rev/feat-plan-dirs/TODO.md", "docs/plan/07-rev/_TODO.md", 9, 11)
if "e3" in WANT: merged("e3", "r3", "fix/do-tasks", "docs/plan/07-rev/fix-do-tasks/DO.md", "docs/plan/07-rev/_DO.md", 9, 11)
if "e4" in WANT: merged("e4", "r4", "feat/legacy-notes", "docs/plan/feat-legacy-notes/TODO.md", "docs/plan/TODO.md", 9, 11)

print(f"\n{fails} failing"); sys.exit(1 if fails else 0)
