"""Grade a grant-lifetime run: did each case's `touch probe-<n>` run, or was it denied?

  LOCATE_PLAN_WORK=<dir> RUN=<tag> python3 -I check.py

g0 is the control: with no grant the write must be denied, or the run measures nothing. g1
and g3 invoke the command and must run. g2, the next message with no command, is the
measurement. Read-only: it reads the stream-json and checks for the probe files."""
import json, os, sys

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

CASES = [("g0", 0, "denied", "control, no grant"), ("g1", 1, "ran", "the turn that invokes the command"),
         ("g2", 2, None, "the next message, no command"), ("g3", 3, "ran", "the command invoked again")]
bad, cost = 0, 0.0
for cid, n, want, what in CASES:
    got, res = case(cid, n)
    cost += (res or {}).get("total_cost_usd") or 0
    ok = got == want if want else got in ("ran", "denied")
    print(f"{'PASS' if ok else 'FAIL'}  {cid}  {what}: {got}" + ("" if ok or not want else f", want {want}"))
    bad += not ok
g2 = case("g2", 2)[0]
if bad: print(f"\nresult: void, {bad} case(s) failed; cost ${cost:.2f}"); sys.exit(1)
print(f"\nresult: {'the grant clears with the next message' if g2 == 'denied' else 'the grant outlasts its turn'}; cost ${cost:.2f}")
