"""Build the goal-10 trial arms under $LOCATE_PLAN_WORK/p/: copies of the working tree's
workflow-claude, each at p/<8 hex>/workflow-claude, so that no path a session sees names
its arm or its fault.

  baseline   the shipped tree, plus a probe-resolver command that runs Step 1 as shipped
  haiku      plan-resolver.md on Haiku, the variant Step 1 in /hitl-step and /step, and a
  sonnet     probe-resolver command that runs that Step 1 alone (the same, on Sonnet)

Each arm also gets three fault copies, whose scripts/locate-plan.sh wraps the real script
(kept outside the plugin root, as p/<hex>/core.sh, with its library in p/<hex>/lib/): f03 cuts the report short, f04 gives
a well-formed wrong answer, f05 swaps the plan path so next: no longer matches. f01 and f02
need no copy: run.sh removes the plan's read bit, or puts a failing awk first on PATH.

  LOCATE_PLAN_WORK=<dir> python3 -I build-arms.py [--rebuild]

Writes only under $LOCATE_PLAN_WORK/p. Refuses to overwrite unless --rebuild. Prints each
copy's directory; run.sh and grade.py derive the same names."""
import hashlib, os, shutil, stat, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PLUGIN = REPO + "/plugins/workflow-claude"
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
AGENT = open(HERE + "/plan-resolver.md").read()
ARMS, FAULTS = ("baseline", "haiku", "sonnet"), ("", "f03", "f04", "f05")

def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
def arm_dir(arm, fault=""): return f"{W}/p/{h(f'arm/{arm}/{fault}')}"

NEXT_CHECK = """
Finally, the next: check that Step 1 ends with. If the report you acted on has
`result: found` and a `next:` other than `—`, `Read` that one line of the file it names
(`offset` the line, `limit` 1) and print `next-check: match` if it equals the text after
the line number, else `next-check: differ`. Otherwise print `next-check: n/a`.
"""

BASELINE_PROBE = """---
description: Throwaway probe. Runs the shipped Step 1 (locate-plan.sh, no agent) alone and prints what it did.
argument-hint: "<model> [path]"
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh:*), Read
---

This command tests Step 1 of `/hitl-step` and `/step` as shipped, and nothing else.
`$ARGUMENTS` holds a model (`TODO.md` or `DO.md`) and, optionally, a path. Do not resolve,
read or search for any plan yourself beyond what is asked here, and do not edit anything.

1. Run, alone, with nothing appended, chained or piped, leaving out `<path>` if none:

       ${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh <model> -- <path>

2. Print its output verbatim in a fenced block.
3. Under a line `Step 1 would:`, say what Step 1 tells the user, and nothing more: for
   `found`, the plan, rung, kind and any warnings; for `ask`, the candidates; for
   `none`, that there is no plan; for `error`, each `problem:` with its `fix:`; with no
   `result:` line, the output, and that the script failed.
""" + NEXT_CHECK

STEP1 = """The `workflow-claude:plan-resolver` agent runs the bundled `scripts/locate-plan.sh`,
which resolves the plan by the five rungs the plugin's `CLAUDE.md` describes, and
troubleshoots it if it fails. Do not resolve the plan yourself.

1. Spawn `subagent_type: workflow-claude:plan-resolver` with one line per input you have:

       model: {model}
       path: <the path token from `$ARGUMENTS`, if any>
       goal: <the line of an item the user named out of order, found with `Grep`, if any>

   If the spawn itself fails, say so with the error and stop.
2. **Wait for its return, then vet it.** The spawn may run in the background. Run its
   `invocation:` line yourself, alone, with nothing appended, chained or piped, and
   compare your output with its `output:`. If they differ, show both and stop. From here
   on, your own run is the report. A key with several items continues on lines indented
   two spaces.
3. Act on `result:` in that report:
   - `found`: the plan file is `plan:`. State it, with `rung:` and `kind:`,
     before any work, and show every `warnings:` line; then carry on. If `layout:` is
     `per-goal`, say this version cannot yet edit goal files, and stop.
   - `ask`: show `candidates:` and `message:`, wait for the user's choice, and
     spawn the agent again with it as `path:`. Never pick a candidate yourself.
   - `none`: say there is no plan, and stop.
   - `error`: the repository breaks a convention resolution relies on. Relay
     each `problem:` line with its `fix:` line, then the agent's `diagnosis:` and `fix:`
     lines, marked as the agent's, and its `suggested:` invocation if it has one. Stop.
     Never use a suggestion unasked; the fix is the user's to make.
   - no `result:` line (a usage error, or the script itself failed): show its output
     and the agent's `diagnosis:` and `fix:` lines, marked as the agent's, and stop.
4. **Check before trusting.** Confirm the `next:` line matches the file verbatim, within
   the read Step 2 makes or with a one-line `Read`. A mismatch means the file changed
   after the script read it: run `invocation:` once more, and stop if it still disagrees.

"""

WRAPPER_PROBE = """---
description: Throwaway probe. Runs the plan-resolver variant of Step 1 alone and prints what it did.
argument-hint: "<model> [path]"
allowed-tools: Agent, Bash(${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh:*), Read
---

This command tests Step 1 of the plan-resolver variant and nothing else. `$ARGUMENTS`
holds a model (`TODO.md` or `DO.md`) and, optionally, a path. Do not resolve, read or
search for any plan yourself, and do not edit anything.

1. Spawn `subagent_type: workflow-claude:plan-resolver` with these lines, leaving out
   `path:` if no path was given:

       model: <the model>
       path: <the path>

   If the spawn errors, print the error verbatim and stop.
2. The spawn may run in the background: wait for its return. Then run its `invocation:`
   line yourself, alone, with nothing appended, chained or piped.
3. Print exactly three fenced blocks and two lines, nothing else:
   - the agent's return, verbatim;
   - your own run's output, verbatim;
   - `vetting: match` if your output equals the agent's `output:`, else `vetting: differ`.
""" + NEXT_CHECK

# Each wrapper calls the real script, kept outside the plugin root. No comments: the agent
# may read this file, and a comment naming the fault would tell it what to look for.
WRAPPERS = {
 "f03": '#!/usr/bin/env bash\n"$(dirname "$0")/../../core.sh" "$@" | head -5\n',
 "f04": '#!/usr/bin/env bash\nexec "$(dirname "$0")/../../core.sh" --branch no-such-branch "$@"\n',
 "f05": '#!/usr/bin/env bash\n"$(dirname "$0")/../../core.sh" "$@" | sed -E "s#docs/plan/case-[a-z0-9-]+/(TODO|DO)\\.md#docs/plan/TODO.md#g"\n',
}

def mkexec(path, text):
    open(path, "w").write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def lockstep(cmds):
    """The plugin CLAUDE.md's lockstep check: Step 1 of the two commands differs only in the
    model and the command name."""
    r = subprocess.run(["bash", "-c",
        'diff <(sed -n "/^## Step 1/,/^### Status stamp/p" "$1/hitl-step.md" | sed "s/TODO\\.md/DO.md/g; s#/hitl-step#/step#g") '
        '<(sed -n "/^## Step 1/,/^### Status stamp/p" "$1/step.md")', "_", cmds], capture_output=True, text=True)
    return r.returncode == 0 and not r.stdout

def build_arm(arm, dst):
    shutil.copytree(PLUGIN, dst)
    if arm == "baseline":
        open(dst + "/commands/probe-resolver.md", "w").write(BASELINE_PROBE); return
    os.makedirs(dst + "/agents", exist_ok=True)
    a = AGENT if arm == "haiku" else AGENT.replace("\nmodel: haiku\n", "\nmodel: sonnet\n", 1)
    assert a.count("\nmodel: ") == 1 and f"model: {arm}" in a
    open(dst + "/agents/plan-resolver.md", "w").write(a)
    for fn, m in (("hitl-step.md", "TODO.md"), ("step.md", "DO.md")):
        p = f"{dst}/commands/{fn}"; s = open(p).read()
        i = s.index("The bundled `scripts/locate-plan.sh` resolves the plan")
        j = s.index("A master plan (`kind: legacy-master`")
        s = s[:i] + STEP1.format(model=m) + s[j:]
        old = "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh:*), "
        assert s.count(old) == 1
        open(p, "w").write(s.replace(old, "Agent, " + old))
    open(dst + "/commands/probe-resolver.md", "w").write(WRAPPER_PROBE)

if __name__ == "__main__":
    if "--rebuild" in sys.argv: shutil.rmtree(W + "/p", ignore_errors=True)
    for arm in ARMS:
        for fault in FAULTS:
            root = arm_dir(arm, fault)
            if os.path.exists(root): sys.exit(f"refusing: {root} exists (use --rebuild)")
            dst = root + "/workflow-claude"
            build_arm(arm, dst)
            if fault:
                # core.sh sources lib/plan-rules.sh from beside itself, so it takes a copy
                os.rename(dst + "/scripts/locate-plan.sh", root + "/core.sh")
                shutil.copytree(dst + "/scripts/lib", root + "/lib")
                mkexec(dst + "/scripts/locate-plan.sh", WRAPPERS[fault])
            print(f"{arm:<8} {fault or '-':<4} {root}  lockstep {'empty' if lockstep(dst + '/commands') else 'DIFFERS'}")
    body = AGENT.split("---", 2)[2]
    print(f"agent body: {len(body.strip())} characters")
