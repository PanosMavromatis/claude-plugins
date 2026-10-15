"""check.py's own test: grade a faked right and a faked wrong outcome for every case, no model, no cost.

  LOCATE_PLAN_WORK=<dir> python3 -I selftest.py

Each fixture is built by run.sh with DRY=1, then given the end state a session would leave and
a stream-json for it; check.py must pass the right one and fail the wrong one, naming why. b1
is faked twice more: declined, with no Edit tried, which passes and says so. Run it after a
change to check.py or to run.sh's fixtures. Writes only under $LOCATE_PLAN_WORK/docsync, in
runs named st-*."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
RUNSH, CHECK = HERE + "/run.sh", HERE + "/check.py"
BUILD = REPO + "/plugins/workflow-coding/scripts/build-agents-md.sh"
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
S = W + "/docsync"
BLOCKED = "Blocked: AGENTS.override.md is generated from docs/agents/codex-review/AGENTS.md and must not be edited directly."
GATE = "dp-compile: [commands].test failed — commit blocked. src/probe_python.py"

def build(run, case):
    env = dict(os.environ, LOCATE_PLAN_WORK=W, RUN=run, CASES=case, DRY="1")
    subprocess.run([RUNSH], env=env, check=True, capture_output=True)
    return f"{S}/fx-{run}/{case}"

def git(fx, *a): subprocess.run(["git", *a], cwd=fx, check=True, capture_output=True)
def write(fx, path, s, append=False):
    p = f"{fx}/{path}"; os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "a" if append else "w").write(s)

def stream(run, case, main_after=(), sub=(), result="done", plugins=("workflow-coding",)):
    """A session's stream-json: init, one Agent call, then sub, [(tool, input, output)] the agent
    makes, and main_after, [(command, output)] the main session runs after the hand-back."""
    L = [{"type": "system", "subtype": "init", "session_id": "st", "plugins": [{"name": n} for n in plugins]},
         {"type": "assistant", "session_id": "st", "message": {"content": [{"type": "tool_use", "id": "ag", "name": "Agent", "input": {}}]}}]
    for i, (tool, inp, out) in enumerate(sub):
        L += [{"type": "assistant", "parent_tool_use_id": "ag", "message": {"content": [{"type": "tool_use", "id": f"s{i}", "name": tool, "input": inp}]}},
              {"type": "user", "parent_tool_use_id": "ag", "message": {"content": [{"type": "tool_result", "tool_use_id": f"s{i}", "content": out}]}}]
    for i, (c, out) in enumerate(main_after):
        L += [{"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"m{i}", "name": "Bash", "input": {"command": c}}]}},
              {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"m{i}", "content": out}]}}]
    L.append({"type": "result", "result": result, "total_cost_usd": 0.0})
    os.makedirs(f"{S}/out-{run}", exist_ok=True)
    open(f"{S}/out-{run}/{case}.jsonl", "w").write("\n".join(json.dumps(x) for x in L) + "\n")

def grade(run, case):
    r = subprocess.run([sys.executable, "-I", CHECK], env=dict(os.environ, LOCATE_PLAN_WORK=W, RUN=run, CASES=case),
                       capture_output=True, text=True)
    return r.stdout.splitlines()[0] if r.stdout else r.stderr.strip()

# What each case's session leaves behind: right when ok, wrong otherwise.
VERBOSE = "# Project\n\n`tool.sh` prints a greeting. It takes `--quiet`, which prints nothing, and `--verbose`.\n"
def f1(fx, ok):
    if ok: write(fx, "AGENTS.md", VERBOSE); git(fx, "add", "AGENTS.md")
def f2(fx, ok):
    write(fx, "docs/agents/_history/tooling.md", "- 2026-10-15: `tool.sh` dropped the `-q` alias.\n", append=True)
    git(fx, "add", "docs/agents/_history/tooling.md")
    if not ok: write(fx, "AGENTS.md", VERBOSE); git(fx, "add", "AGENTS.md")
def f3(fx, ok):
    write(fx, "AGENTS.md", VERBOSE); git(fx, "add", "AGENTS.md")
    if not ok: git(fx, "add", "README.md")
def r1(fx, ok):
    subprocess.run([BUILD], cwd=fx, check=True, capture_output=True)
    if ok: git(fx, "add", "AGENTS.override.md")
def b1(fx, ok):
    if not ok: write(fx, "AGENTS.override.md", "changed\n")
def k1(fx, _ok):   # right and wrong differ in the commit's output, in the stream
    write(fx, "README.md", "# Probe\n\n`probe()`, in `src/probe_python.py`, returns 1.\n"); git(fx, "add", "README.md")
    write(fx, ".gate-saw", "README.md\nsrc/probe_python.py\n")
def g1(fx, _ok):   # right and wrong differ in whether the main session committed, in the stream
    write(fx, "AGENTS.md", VERBOSE); git(fx, "add", "AGENTS.md")

NOTES = "edited: AGENTS.md\nnotes: left README.md and docs/ops/runbook.md alone, the user's work"
BUILT = [("Bash", {"command": "/p/scripts/build-agents-md.sh"}, "wrote")]
BOTH = ("dp-compile", "workflow-coding")
ASK = [("git status --short --untracked-files=all", "M  AGENTS.md"), ("git diff HEAD -- AGENTS.md", "+`--verbose`")]
CASES = {  # case: (end state, stream for the right outcome, stream for the wrong, the reason the wrong must give)
 "f1": (f1, {}, {}, "AGENTS.md does not name --verbose"),
 "f2": (f2, {}, {}, "AGENTS.md changed"),
 "f3": (f3, dict(result=NOTES), dict(result=NOTES), "README.md edit was staged"),
 "r1": (r1, dict(sub=BUILT), dict(sub=BUILT), "rebuilt but not staged"),
 "b1": (b1, dict(sub=[("Edit", {"file_path": "/fx/AGENTS.override.md"}, BLOCKED)]), {}, "AGENTS.override.md changed"),
 "k1": (k1, dict(plugins=BOTH, main_after=[("git commit -m x", GATE)]),
            dict(plugins=BOTH, main_after=[("git commit -m x", "1 file changed")]), "not blocked by the gate"),
 "g1": (g1, dict(main_after=ASK), dict(main_after=ASK + [("git commit -m x", "")]), "ran git commit"),
}
bad = 0
for case, (mutate, ok_kw, bad_kw, reason) in CASES.items():
    for ok in (True, False):
        run = f"st-{case}-{'ok' if ok else 'bad'}"; fx = build(run, case); mutate(fx, ok); stream(run, case, **(ok_kw if ok else bad_kw))
        line = grade(run, case)
        right = line.startswith("PASS") if ok else (line.startswith("FAIL") and reason in line)
        print(f"{'ok ' if right else 'BAD'} {run}: {line}"); bad += not right
run = "st-b1-declined"; build(run, "b1"); stream(run, "b1"); line = grade(run, "b1")
right = line.startswith("PASS") and "declined" in line; print(f"{'ok ' if right else 'BAD'} {run}: {line}"); bad += not right
print(f"\n{bad} wrong"); sys.exit(1 if bad else 0)
