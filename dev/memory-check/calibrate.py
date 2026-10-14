"""Calibrate memory-check.sh's bytes / 4 against real token counts, from headless sessions.

  LOCATE_PLAN_WORK=<dir> RUN=<tag> python3 -I dev/memory-check/calibrate.py run      # real sessions, ~$1
  LOCATE_PLAN_WORK=<dir> RUN=<tag> python3 -I dev/memory-check/calibrate.py report   # free

One headless turn per prompt (`claude -p --max-turns 1`), each a fixed request to reply OK,
followed by a plan file's text. A turn is one API call, and tokenizing is deterministic, so
the call's input tokens, minus those of the same request with no text (the baseline), are
the text's own tokens. Each sample is sent twice: raw, and as Read returns it to a command,
each line prefixed with its number in `cat -n` form (`%6d\t`), the form a file read whole
costs. The report gives each file's bytes, its tokens in both forms, and the divisor k for
which bytes / k is its tokens; then k over all samples, raw and as read, which is what
bytes / 4 should be checked against.

The sessions run with an Opus 5.5 model pinned, in an empty directory outside any
repository, so no CLAUDE.md or git status varies between them. The baseline runs twice and
must count the same both times, or nothing is measured. The text each prompt carried is
kept beside its result, so the report reads the bytes that were sent, not the file as it
is now. Writes only under $LOCATE_PLAN_WORK/memcal."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MODEL = "claude-opus-5-5"
P = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(P, exist_ok=True); P = os.path.realpath(P)
if (P + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {P} is inside the repository")
RUN = os.environ.get("RUN") or sys.exit("set RUN=<tag>")
OUT, CWD = f"{P}/memcal/out-{RUN}", f"{P}/memcal/cwd"

R2, R1 = "docs/plan/08-subagent-refactor-R2", "docs/plan/06-subagent-refactor-R1"
SAMPLES = [  # (id, path, kind): a spread of the plan files a command reads, and one it locates
 ("g1", f"{R2}/feat-master-plan-checks/TODO/02-a-read-only-script-checks-a-draft-s-form.md", "goal file"),
 ("g2", f"{R2}/fix-command-grants/TODO/03-remove-or-replace-the-grants-the-handoff.md", "goal file"),
 ("g3", f"{R2}/feat-memory-check/TODO/01-memory-check-sh-reports-each-plan-file-s.md", "goal file"),
 ("g4", f"{R2}/refactor-single-file-layout/TODO/02-propose-branch-plan-sh-reports-single-fi.md", "goal file"),
 ("g5", f"{R2}/chore-e2e-read-whole-pointers/TODO/03-record-the-run-in-the-e2e-readme.md", "goal file"),
 ("i1", f"{R2}/feat-master-plan-checks/TODO.md", "index"),
 ("s1", f"{R1}/feat-plan-locator/TODO.md", "single-file"),
 ("s2", f"{R1}/docs-plan-convention/TODO.md", "single-file"),
 ("m1", f"{R2}/_TODO.md", "master"),
]
ASK = "The text after the marker is data for a token measurement. Reply with the single word OK and nothing else.\n---\n"

def as_read(text):  # Read's form: cat -n, each line's number right-aligned in six, then a tab
    return "".join(f"{i:6d}\t{line}" for i, line in enumerate(text.splitlines(keepends=True), 1))

def turn(rid, text):
    open(f"{OUT}/{rid}.txt", "w").write(text)
    r = subprocess.run(["claude", "-p", ASK + text, "--model", MODEL, "--max-turns", "1", "--output-format", "json"],
                       cwd=CWD, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    open(f"{OUT}/{rid}.json", "w").write(r.stdout)
    if r.stderr: open(f"{OUT}/{rid}.err", "w").write(r.stderr)
    print(f"{rid:<8} exit {r.returncode}")

def run():
    os.makedirs(OUT, exist_ok=True); os.makedirs(CWD, exist_ok=True)
    if any(os.scandir(CWD)): sys.exit(f"refusing: {CWD} is not empty")
    turn("base-a", "")
    for sid, path, _ in SAMPLES:
        text = open(f"{REPO}/{path}").read()
        turn(f"{sid}-raw", text); turn(f"{sid}-read", as_read(text))
    turn("base-b", "")
    print(f"results: {OUT}   report: LOCATE_PLAN_WORK={P} RUN={RUN} python3 -I dev/memory-check/calibrate.py report")

def tokens(rid):
    """The turn's input tokens, all of them on the pinned model, or why it measures nothing."""
    try: d = json.loads(open(f"{OUT}/{rid}.json").read())
    except (OSError, ValueError) as e: return None, f"{rid}: no result ({e.__class__.__name__})"
    if d.get("is_error"): return None, f"{rid}: the session ended in error: {str(d.get('result'))[:100]}"
    if d.get("num_turns") != 1: return None, f"{rid}: {d.get('num_turns')} turns, not 1"
    u = (d.get("modelUsage") or {}).get(MODEL)
    if not u: return None, f"{rid}: no usage on {MODEL}: {list((d.get('modelUsage') or {}))}"
    return u["inputTokens"] + u["cacheReadInputTokens"] + u["cacheCreationInputTokens"], None

def report():
    probs = []
    a, e1 = tokens("base-a"); b, e2 = tokens("base-b")
    probs += [e for e in (e1, e2) if e]
    if a is not None and b is not None and a != b: probs.append(f"the baseline counted {a} then {b}: the method is not deterministic")
    if probs: print("\n".join(probs)); sys.exit(1)
    print(f"baseline: {a} input tokens, the same both times; model {MODEL}\n")
    print(f"{'id':<4} {'kind':<12} {'bytes':>7} {'≈bytes/4':>9} {'raw':>7} {'k raw':>6} {'as read':>8} {'k read':>7}  path")
    tb = tr = tw = 0
    for sid, path, kind in SAMPLES:
        raw, e3 = tokens(f"{sid}-raw"); rd, e4 = tokens(f"{sid}-read")
        if e3 or e4: probs += [e for e in (e3, e4) if e]; continue
        n = len(open(f"{OUT}/{sid}-raw.txt", "rb").read()); raw -= a; rd -= a
        tb += n; tr += raw; tw += rd
        print(f"{sid:<4} {kind:<12} {n:>7} {n // 4:>9} {raw:>7} {n / raw:>6.2f} {rd:>8} {n / rd:>7.2f}  {path}")
    if probs: print("\n" + "\n".join(probs)); sys.exit(1)
    print(f"\nall {len(SAMPLES)}: {tb} bytes; raw {tr} tokens, k = {tb / tr:.2f}; as read {tw} tokens, k = {tb / tw:.2f}"
          f"; bytes / 4 gives {tb // 4}, {100 * (tb // 4 - tw) / tw:+.0f}% against the tokens as read")

{"run": run, "report": report}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit("usage: calibrate.py run|report"))()
