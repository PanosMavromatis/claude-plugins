"""Grade the per-goal end-to-end run: each scenario's fixture repository as the sessions left
it, and each session's tool calls from its stream-json.

  LOCATE_PLAN_WORK=<dir> RUN=<tag> python3 -I check.py [scenario...]   (default: all)

Read-only: it runs git reads and the plugin copy's own read-only scripts in the fixtures.
Prints PASS or FAIL per check, a line per finding worth reading (a denial, a Grep), and
exits non-zero if any check failed."""
import hashlib, itertools, json, os, re, shutil, subprocess, sys

W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK")
W = os.path.realpath(W); RUN = os.environ.get("RUN") or sys.exit("set RUN=<tag>")
E = W + "/e2e"; OUT = f"{E}/out-{RUN}"
PLUGIN = f"{E}/p/{hashlib.sha1(b'e2e/plugin').hexdigest()[:8]}/workflow-claude"
SCRIPTS = PLUGIN + "/scripts"
fails = 0
WANT = [a for a in sys.argv[1:] if re.match(r"^[emc]\d$", a)] or ["e1", "e3", "e4", "e5", "m1", "m2", "m3", "c1", "c2", "c3"]

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
    """The session's own tool calls in order, as (name, input), and the result record. A
    subagent's calls (parent_tool_use_id set) are its own, not the session's."""
    calls, result = [], None
    p = f"{OUT}/{sid}.jsonl"
    if not os.path.exists(p): return None, None
    for line in open(p):
        try: d = json.loads(line)
        except ValueError: continue
        if d.get("type") == "assistant" and not d.get("parent_tool_use_id"):
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

def alone(sid, cmds):
    """One Bash call per command. A script's own arguments, and a commit message, may hold
    the characters a chain is made of."""
    chained = [c for c in cmds if re.search(r";|&&|\|\||(^|[^|])\|([^|]|$)|2>&1", c)
               and not c.lstrip().startswith((SCRIPTS, "git commit", "gh pr create"))]
    check(f"{sid}: every command ran alone", not chained, "; ".join(c[:100] for c in chained[:3]))

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
        alone(sid, cmds)
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

# The revision sessions: /master-plan opening a revision (m1, m2 through /open-revision, m3 a
# dry run past a refusal) and /close-revision closing one (c1 a stamp, c2 a legacy cut with
# moves, c3 a refusal). What a session should have written comes from the copy's own
# scripts, run on the fixture as it was on main, so the rules live in one place.
ROOT = "docs/plan/TODO.md"
SPEC_UNITS = ("CHANGELOG.md", "CLAUDE.md", "check-changelog.sh")   # build.py's SPEC names one file per unit, in order

def at(calls, pred): return [i for i, (n, inp) in enumerate(calls) if pred(n, inp)]
def ran(sub): return lambda n, inp: n == "Bash" and sub in inp.get("command", "")
def wrote(path, tools=("Write", "Edit", "MultiEdit")): return lambda n, inp: n in tools and inp.get("file_path", "").endswith(path)

def outputs(sid):
    """Each Bash command in order, with its output from the tool results."""
    uses, outs = [], {}
    for line in open(f"{OUT}/{sid}.jsonl"):
        try: d = json.loads(line)
        except ValueError: continue
        if d.get("parent_tool_use_id"): continue
        content = (d.get("message") or {}).get("content")
        for c in content if isinstance(content, list) else []:
            if c.get("type") == "tool_use" and c.get("name") == "Bash": uses.append((c.get("id"), (c.get("input") or {}).get("command", "")))
            elif c.get("type") == "tool_result":
                t = c.get("content")
                outs[c.get("tool_use_id")] = t if isinstance(t, str) else "".join(x.get("text", "") for x in t or [] if isinstance(x, dict))
    return [(cmd, outs.get(i, "")) for i, cmd in uses]

def said(sid): return str((session(sid)[1] or {}).get("result", ""))

def main_copy(repo):
    """The fixture as it was on main: the scripts read the working tree, which the session changed."""
    d = f"{E}/_main/{repo}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(f"{E}/_main", exist_ok=True)
    sh(["git", "clone", "-q", "-b", "main", f"{E}/{repo}", d], E); return d

def one_commit(repo, br, want):
    """Exactly one commit on br, touching exactly `want` (renames as a delete and an add)."""
    shas = git(repo, "log", "--format=%H", f"main..{br}").split()
    got = sorted(git(repo, "diff", "--no-renames", "--name-only", f"main..{br}").split())
    check(f"{repo}: one commit on {br}, of exactly {len(want)} paths", len(shas) == 1 and got == sorted(want),
          f"{len(shas)} commits; {got}")
    check(f"{repo}: the tree is clean after", not git(repo, "status", "--porcelain").strip(), git(repo, "status", "--porcelain")[:200])

def draft_form(where, text, label):
    """The form references/subdividing.md gives, which /master-plan checks the draft against."""
    L, bad = text.split("\n"), []
    if L[0] != f"# Revision {label}": bad.append(f"line 1 is {L[0]!r}")
    for k in ("Status", "Version", "Opened", "Spec"):
        if not any(l.startswith(f"**{k}**: ") for l in L[:8]): bad.append(f"no **{k}** header")
    if "**Status**: open" not in L[:8]: bad.append("Status is not open")
    if not re.search(r"^\*\*Opened\*\*: \d{4}-\d\d-\d\d$", text, re.M): bad.append("Opened is not a date")
    hs = [l for l in L if l.startswith("## ")]
    if hs != ["## Preamble", "## Settled decisions", "## Subgoals"]: bad.append(f"headings {hs}")
    sub = L[L.index("## Subgoals") + 1:] if "## Subgoals" in L else []
    items = [i for i, l in enumerate(sub) if l.startswith("- [")]
    for n, i in enumerate(items, 1):
        if not sub[i].startswith(f"- [ ] {n}. "): bad.append(f"subgoal {n} reads {sub[i][:40]!r}")
        cont = " ".join(l.strip() for l in itertools.takewhile(lambda l: l.startswith("  "), sub[i + 1:]))
        if not re.search(r"(^| )Scope: .*Acceptance: ", cont): bad.append(f"subgoal {n} has no Scope/Acceptance line")
    if re.search(r"^\s*> \*\*(Branch|Done)\*\*", text, re.M): bad.append("a backlink or a Done line")
    check(f"{where}: the draft has subdividing.md's form ({len(items)} subgoals)", not bad and 1 <= len(items) <= 8, "; ".join(bad[:4]))
    st = text.split("## Settled decisions", 1)[-1].split("## Subgoals", 1)[0]
    check(f"{where}: the spec's settled decision is under Settled decisions", "Keep a Changelog" in st, st.strip()[:200])
    # The form says nothing about content, and the fixture's CLAUDE.md approves the review that
    # would. A tripwire, not a judgement: each of the spec's three units names one file, so each
    # file must reach a subgoal, first in the spec's order. That proves nothing was dropped and
    # the order holds; it cannot prove nothing was invented, since in this spec nearly any extra
    # subgoal names CHANGELOG.md. A subgoal naming none of the files fails, the one invention it
    # sees; a subgoal count that differs from the spec's is reported. The drafts are read too.
    texts = [" ".join([sub[i]] + list(itertools.takewhile(lambda l: l.startswith("  "), sub[i + 1:]))) for i in items]
    firsts = [next((n for n, t in enumerate(texts, 1) if a in t), None) for a in SPEC_UNITS]
    bare = [n for n, t in enumerate(texts, 1) if not any(a in t for a in SPEC_UNITS)]
    check(f"{where}: nothing dropped (each spec unit reaches a subgoal, in order), no subgoal names none of its files",
          None not in firsts and firsts == sorted(firsts) and not bare, f"first subgoal per unit {dict(zip(SPEC_UNITS, firsts))}; naming none {bare}")
    if len(items) != len(SPEC_UNITS): print(f"      {where}: {len(items)} subgoals for the spec's {len(SPEC_UNITS)} units")

def drafter(sid, calls, label, previous):
    ag = [inp for n, inp in calls if n in ("Agent", "Task")]
    dr = [inp for inp in ag if inp.get("subagent_type") == "workflow-claude:plan-drafter"]
    check(f"{sid}: spawned workflow-claude:plan-drafter", bool(dr), f"agent calls: {[i.get('subagent_type') for i in ag]}")
    pr = dr[0].get("prompt", "") if dr else ""
    for what, v in (("the spec", f"docs/spec/{label}.md"), ("the previous revision", previous)):
        if v != "—": check(f"{sid}: the drafter's prompt names {what}, {v}", v in pr, pr[:200])
    check(f"{sid}: the session left the spec to the drafter", not any(wrote(f"docs/spec/{label}.md", ("Read",))(n, i) for n, i in calls))

def opened(sid, repo, label, alias=False):
    """A real /master-plan: proposed, drafted, the root plan from --render, the revision from
    the draft, both checks after the writes and before one commit, on chore/open-<label>."""
    print(f"\n== {sid}: {'/open-revision' if alias else '/master-plan'} {label}  ({E}/{repo})")
    rev, br = f"docs/plan/{label}/_TODO.md", f"chore/open-{label}"
    m = main_copy(repo); prop = report(sh([f"{SCRIPTS}/propose-revision.sh", label], m)[1])
    change = prop.get("change", ["?"])[0]
    calls = common(sid)
    if calls:
        alone(sid, bash(calls))
        if alias: check(f"{sid}: the alias ran /master-plan through Skill",
                        any(n == "Skill" and inp.get("skill", "").endswith("master-plan") for n, inp in calls))
        p, co, cm = at(calls, ran("propose-revision.sh")), at(calls, ran("git checkout -b")), at(calls, ran("git commit"))
        check(f"{sid}: proposed before git checkout -b", bool(p) and bool(co) and p[0] < co[0], f"propose {p[:1]}, checkout {co[:1]}")
        drafter(sid, calls, label, prop.get("previous", ["—"])[0])
        rw, vw, rd = at(calls, wrote(ROOT)), at(calls, wrote(rev)), at(calls, ran("--render"))
        check(f"{sid}: the root plan was written whole from --render, never edited",
              bool(rw) and all(calls[i][0] == "Write" for i in rw) and bool(rd) and rd[0] < rw[0], f"render {rd[:2]}, root writes {[calls[i][0] for i in rw]}")
        last = max(rw + vw) if rw and vw else None
        lp, rp = at(calls, ran("locate-plan.sh")), [i for i in p if "--render" not in calls[i][1]["command"]]
        check(f"{sid}: locate-plan.sh and propose-revision.sh re-ran after the writes, before the commit",
              last is not None and bool(cm) and any(last < i < cm[0] for i in lp) and any(last < i < cm[0] for i in rp),
              f"last write {last}, locate {lp}, propose {p}, commit {cm[:1]}")
        check(f"{sid}: no push", not any(c.lstrip().startswith("git push") for c in bash(calls)))
    check(f"{repo}: on {br}", git(repo, "branch", "--show-current").strip() == br, git(repo, "branch", "--show-current").strip())
    one_commit(repo, br, [ROOT, rev])
    new = git(repo, "show", f"{br}:{ROOT}")
    line = next((l for l in new.split("\n") if l.startswith(f"- [~] {label} — ")), "")
    check(f"{repo}: the root plan lists `- [~] {label} — <note>`", bool(line), new[:300])
    if line:
        want = sh([f"{SCRIPTS}/propose-revision.sh", label, "--render", line[len(f"- [~] {label} — "):]], m)[1]
        check(f"{repo}: the root plan is exactly --render's for that note ({change})", new == want,
              git(repo, "diff", "-U0", f"main..{br}", "--", ROOT).strip()[:400])
    draft_form(repo, git(repo, "show", f"{br}:{rev}"), label)
    r = report(sh([f"{SCRIPTS}/locate-plan.sh", "TODO.md", "--", rev], f"{E}/{repo}")[1])
    nx = (r.get("next") or [""])[0]
    check(f"{repo}: locate-plan.sh finds the revision with next: on subgoal 1", r.get("result") == ["found"] and nx.startswith(f"{rev}:") and " - [ ] 1. " in nx, f"{r.get('result')} {nx}")

def dry(sid, repo, label, path):
    """A dry run on a legacy root plan with a revision open: the refusal reported, the draft
    written to <path>, no root plan (a refused proposal renders none), no branch, no commit."""
    print(f"\n== {sid}: /master-plan {label} --dry-run {path}, past a refusal  ({E}/{repo})")
    calls = common(sid)
    if calls:
        alone(sid, bash(calls))
        drafter(sid, calls, label, "—")
        check(f"{sid}: no branch, no staging, no commit",
              not at(calls, lambda n, i: n == "Bash" and re.match(r"\s*git (checkout -b|add|commit)\b", i.get("command", ""))))
        check(f"{sid}: the report says a real run would refuse", bool(re.search(r"refus", said(sid), re.I)), said(sid)[:300])
    check(f"{repo}: still on main, at the fixture's one commit", git(repo, "branch", "--show-current").strip() == "main"
          and len(git(repo, "log", "--format=%H").split()) == 1 and git(repo, "branch", "--format=%(refname:short)").split() == ["main"])
    check(f"{repo}: only {path}/ is new", git(repo, "status", "--porcelain").strip() == f"?? {path}/", git(repo, "status", "--porcelain")[:200])
    f = f"{E}/{repo}/{path}/_TODO.md"
    check(f"{repo}: the draft is at {path}/_TODO.md", os.path.exists(f))
    if os.path.exists(f): draft_form(repo, open(f).read(), label)
    check(f"{repo}: no root plan rendered into {path}/", not os.path.exists(f"{E}/{repo}/{path}/TODO.md"))

def closing(sid, calls, repo, label, writes):
    """Both closes: proposed before the branch, the --check after the last write (and move)
    and before the commit, reporting verified."""
    alone(sid, bash(calls))
    p, co, cm = at(calls, ran("close-revision.sh")), at(calls, ran("git checkout -b")), at(calls, ran("git commit"))
    check(f"{sid}: proposed before git checkout -b", bool(p) and bool(co) and p[0] < co[0], f"propose {p[:1]}, checkout {co[:1]}")
    w = [i for x in writes for i in at(calls, x)]
    ck = [i for i in at(calls, ran("--check")) if w and max(w) < i and (not cm or i < cm[0])]
    out = dict((i, o) for i, (c, o) in zip(at(calls, lambda n, i: n == "Bash"), outputs(sid)))
    check(f"{sid}: --check ran after the writes, before the commit, and verified", bool(cm) and any("result: verified" in out.get(i, "") for i in ck),
          f"writes {w}, checks {at(calls, ran('--check'))}, commit {cm[:1]}")
    check(f"{sid}: no push", not any(c.lstrip().startswith("git push") for c in bash(calls)))

def stamped(sid, repo, label):
    print(f"\n== {sid}: /close-revision {label} on a revisions index  ({E}/{repo})")
    rev, br = f"docs/plan/{label}/_TODO.md", f"chore/close-{label}"
    calls = common(sid)
    if calls:
        closing(sid, calls, repo, label, (wrote(ROOT), wrote(rev)))
        check(f"{sid}: both files edited in place, never rewritten", not at(calls, lambda n, i: n == "Write" and i.get("file_path", "").endswith((ROOT, rev))))
    check(f"{repo}: on {br}", git(repo, "branch", "--show-current").strip() == br, git(repo, "branch", "--show-current").strip())
    one_commit(repo, br, [ROOT, rev])
    d = re.search(r"^\*\*Status\*\*: closed — (\d{4}-\d\d-\d\d)$", git(repo, "show", f"{br}:{rev}"), re.M)
    check(f"{repo}: {rev} is stamped closed with a date", bool(d))
    r = report(sh([f"{SCRIPTS}/close-revision.sh", label, "--date", d.group(1) if d else "2000-01-01"], main_copy(repo))[1])
    for e in r.get("edits", []):
        path, n, text = re.match(r"^(.*?):(\d+): (.*)$", e).groups()
        want = git(repo, "show", f"main:{path}").split("\n"); want[int(n) - 1] = text
        check(f"{repo}: {path} differs from main by line {n} alone, now `{text[:50]}`", git(repo, "show", f"{br}:{path}") == "\n".join(want),
              git(repo, "diff", "-U0", f"main..{br}", "--", path).strip()[:300])

def extracted(sid, repo, label):
    print(f"\n== {sid}: /close-revision {label} on a legacy root plan, with moves  ({E}/{repo})")
    arc, br = f"docs/plan/{label}/_TODO.md", f"chore/close-{label}"
    m = main_copy(repo); date = "2000-01-01"
    calls = common(sid)
    if calls:
        date = next((re.search(r"--date (\S+)", c).group(1) for c in bash(calls) if "--date " in c), date)
    r = report(sh([f"{SCRIPTS}/close-revision.sh", label, "--date", date], m)[1])
    moves = r.get("moves", [])
    pairs = [mv.split()[2:4] for mv in moves if mv.startswith("git mv ")]
    if calls:
        closing(sid, calls, repo, label, (wrote(ROOT), wrote(arc), ran("git mv ")))
        ra, rr, wa, wr = at(calls, ran("--render archive")), at(calls, ran("--render root")), at(calls, wrote(arc)), at(calls, wrote(ROOT))
        check(f"{sid}: both files rendered before either was written", bool(ra and rr and wa and wr) and max(ra[0], rr[0]) < min(wa[0], wr[0]),
              f"render archive {ra[:1]} root {rr[:1]}, write archive {wa[:1]} root {wr[:1]}")
        check(f"{sid}: each move ran exactly as printed, and nothing else was moved",
              sorted(c.strip() for c in bash(calls) if c.lstrip().startswith("git mv")) == sorted(moves), f"{[c for c in bash(calls) if 'git mv' in c]}")
        check(f"{sid}: the report names the plan left flat, feat-old-c", "feat-old-c" in said(sid), said(sid)[-300:])
    check(f"{repo}: on {br}", git(repo, "branch", "--show-current").strip() == br, git(repo, "branch", "--show-current").strip())
    check(f"{repo}: the proposal on main moved feat-old-a and feat-old-b", [os.path.basename(a) for a, _ in pairs] == ["feat-old-a", "feat-old-b"], f"{moves}")
    one_commit(repo, br, [ROOT, arc] + [f"{x}/TODO.md" for pr in pairs for x in pr])
    for which, path in (("archive", arc), ("root", ROOT)):
        want = sh([f"{SCRIPTS}/close-revision.sh", label, "--date", date, "--render", which], m)[1]
        check(f"{repo}: {path} is exactly --render {which}'s", bool(want) and git(repo, "show", f"{br}:{path}") == want,
              git(repo, "diff", "-U0", f"main..{br}", "--", path).strip()[:300])
    check(f"{repo}: feat-old-c, still active, stays flat", bool(git(repo, "show", f"{br}:docs/plan/feat-old-c/TODO.md")))

def refused(sid, repo, label):
    print(f"\n== {sid}: /close-revision {label} with items still open  ({E}/{repo})")
    calls = common(sid)
    if calls:
        check(f"{sid}: ran close-revision.sh, then wrote nothing",
              bool(at(calls, ran("close-revision.sh"))) and not at(calls, lambda n, i: n in ("Write", "Edit", "MultiEdit"))
              and not at(calls, lambda n, i: n == "Bash" and re.match(r"\s*git (checkout -b|add|commit)\b", i.get("command", ""))))
        check(f"{sid}: the report names the open items", "Plan directory structure" in said(sid) or "2." in said(sid), said(sid)[:300])
    check(f"{repo}: untouched: main, one commit, clean", git(repo, "branch", "--format=%(refname:short)").split() == ["main"]
          and len(git(repo, "log", "--format=%H").split()) == 1 and not git(repo, "status", "--porcelain").strip())

if "m1" in WANT: opened("m1", "m1", "08-next")
if "m2" in WANT: opened("m2", "m2", "04-next", alias=True)
if "m3" in WANT: dry("m3", "m3", "04-next", "dry-run")
if "c1" in WANT: stamped("c1", "c1", "07-rev")
if "c2" in WANT: extracted("c2", "c2", "03-old")
if "c3" in WANT: refused("c3", "c3", "07-rev")

print(f"\n{fails} failing"); sys.exit(1 if fails else 0)
