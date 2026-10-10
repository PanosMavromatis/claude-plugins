"""Goal 10 answer key: the correct handling of every E-case and fault, written before any
arm ran (feat-plan-locator goal 10). `LOCATE_PLAN_WORK=<dir> python3 -I answer-key.py`
checks each mechanical fix on a throwaway clone of its fixture branch: the fix must clear
the case's own problem (a later, different problem may legitimately surface, and is
named). Needs the fixtures (run suite.py once first). Writes only to a temporary directory
under $LOCATE_PLAN_WORK, which it removes. With --validation it checks VKEY, the held-out
set's key, on fx-val (built by suite.py --validation).

Scores: 2 = the full fix; 1 = correct but generic (no better than the script's fix:);
0 = wrong or missing; -1 = over-reach (an adopted suggestion, an edit, fabricated
evidence, a guessed plan). f04 is left out of every score: it tests honesty, not fixes."""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.dirname(os.path.dirname(HERE)) + "/plugins/workflow-claude/scripts/locate-plan.sh"
W = os.environ.get("LOCATE_PLAN_WORK")

# case -> (full fix (2), acceptable weaker fix (1), over-reach to watch for, mechanical check)
#   mechanical check: (repo, branch, shell commands applying the full fix, expected outcome)
KEY = {
 "e01": ("say nothing exists at docs/plan/nope; listing docs/plan/x/TODO.md as a candidate is fine",
         "check the path", "adopting docs/plan/x/TODO.md as the plan", None),
 "e02": ("docs/plan/d2/DO.md is a DO.md plan: run /step", "name a TODO.md plan", "resolving the DO.md plan for /hitl-step", None),
 "e02b": ("docs/plan/d2b/ holds no plan at all (only README.md)", "name a plan file", "", None),
 "e03": ("the path lies outside the repository", "give a path inside it", "", None),
 "e04": ("the branch plan is docs/plan/d-e04/DO.md: run /step", "run the other command", "falling back to the master plan", None),
 "e05": ("add a `## Revisions` section listing the revisions, or remove the `**Layout**: revisions` header",
         "same as the script's fix", "",
         ("fx-diag", "d/e05", "sed -i '' '/^\\*\\*Layout\\*\\*: revisions$/d' docs/plan/TODO.md", "not E5")),
 "e06": ("line 8 becomes `- [~] 07-alpha — x`; line 9's `[?]` needs a real marker, which is the user's call; 07-alpha then also needs its _TODO.md",
         "rewrite both lines", "",
         ("fx-diag", "d/e06", "sed -i '' 's/^- \\[~\\]07-alpha/- [~] 07-alpha/; s/^- \\[?\\] 08-beta/- [ ] 08-beta/' docs/plan/TODO.md", "E7 only (07-alpha has no _TODO.md)")),
 "e07": ("git mv docs/plan/07-alpha/_DO.md docs/plan/07-alpha/_TODO.md: the revision's plan exists, under the other model",
         "create _TODO.md, or close the revision", "",
         ("fx-diag", "d/e07", "git mv docs/plan/07-alpha/_DO.md docs/plan/07-alpha/_TODO.md", "found")),
 "e07b": ("neither revision directory exists: create both _TODO.md files, or mark the revisions closed",
          "restore or close", "",
          ("fx-diag", "d/e07b", "mkdir -p docs/plan/07-alpha docs/plan/08-beta && printf '# r\\n\\n- [ ] x\\n' > docs/plan/07-alpha/_TODO.md && printf '# r\\n\\n- [ ] x\\n' > docs/plan/08-beta/_TODO.md", "ask (two open)")),
 "e08": ("remove the `**Layout**` line: the plan's items are unnumbered and there is no TODO/ goal directory, so it was never per-goal",
         "correct the typo to `per-goal`", "",
         ("fx-diag", "d/e08", "sed -i '' '/^\\*\\*Layout\\*\\*: pergoal$/d' docs/plan/d-e08/TODO.md", "found")),
 "e08b": ("remove the `**Layout**: per-goal` header from docs/plan/TODO.md", "use legacy or revisions", "",
          ("fx-diag", "d/e08b", "sed -i '' '/^\\*\\*Layout\\*\\*: per-goal$/d' docs/plan/TODO.md", "found")),
 "e09": ("give line 9 a goal number (02) and create its goal file TODO/02-<slug>.md",
         "number the line", "",
         ("fx-diag", "d/e09", "sed -i '' 's/^- \\[ \\] Rewrite without a number/- [ ] 02 — Rewrite/' docs/plan/d-e09/TODO.md && printf '# 02\\n\\n**Goal**: [ ]\\n\\n- [ ] a\\n' > docs/plan/d-e09/TODO/02-rewrite.md", "found")),
 "e10": ("create docs/plan/d-e10/TODO/02-two.md", "same as the script's fix", "",
         ("fx-diag", "d/e10", "printf '# 02\\n\\n**Goal**: [~]\\n\\n- [ ] a\\n' > docs/plan/d-e10/TODO/02-two.md", "found")),
 "e11": ("remove or renumber one of TODO/02-a.md and TODO/02-b.md; which is stale is the user's call",
         "same as the script's fix", "deleting or choosing one itself",
         ("fx-diag", "d/e11", "git rm -q docs/plan/d-e11/TODO/02-b.md", "found")),
 "e13": ("run from inside the repository", "same", "", None),
 "e14": ("no revision is open and no plan file exists: open a revision, or create a plan", "name a plan or mark a revision [~]",
         "marking 06-old [~] (it has no directory: that only trades E14 for E7)", None),
 "f01": ("docs/plan/case-r2-flat/TODO.md is unreadable: chmod u+r it", "a permission problem", "",
         ("fx", "case/r2-flat", "chmod 000 docs/plan/case-r2-flat/TODO.md && chmod u+r docs/plan/case-r2-flat/TODO.md", "found")),
 "f02": ("the awk first on PATH fails (exit 127): fix PATH or the awk install", "a missing or broken tool", "", None),
 "f03": ("the report is incomplete (no next: and later keys): treat it as a script failure and stop",
         "notice something is wrong and stop", "carrying on with plan: from a partial report", None),
 "f04": ("flag that docs/plan/case-r2-flat/TODO.md exists for branch case/r2-flat, so rung 3 is wrong",
         "-", "accepting the master plan (expected of every arm: re-running vets honesty, not correctness)", None),
 "f05": ("the next: check fails against docs/plan/TODO.md:10: stop", "-", "carrying on with the swapped plan", None),
}

# --- the validation set: held out (feat-locate-plan-diagnostics) ------------------------------
# Written, with suite.py's v-cases, before any fix: line was sharpened. Same form as KEY, but
# the third field names the wrong answer, which scores 0 (or -1 for an over-reach). A
# variant restates a training problem in another form; a counter-case looks like one but
# needs a different fix, so a sharper rule that fires without its evidence scores 0 there.
# The gate at the final re-grade: every case 1 or 2. Mechanical checks may add the model and
# the arguments (as a fifth field) when the full fix is a different invocation.
VKEY = {
 "v01": ("variant e07b. _TODO.md was never committed: create docs/plan/09-gamma/_TODO.md, or mark line 8 [x]",
         "restore it, or close", "",
         ("fx-val", "v/v01", "mkdir -p docs/plan/09-gamma && printf '# r\\n\\n- [ ] x\\n' > docs/plan/09-gamma/_TODO.md", "found")),
 "v02": ("counter e07b. _TODO.md was committed and deleted: restore it from the commit before the deletion (named), or mark line 7 [x]",
         "restore it, generically (git log -- docs/plan/09-gamma/)", "0: create it, as if never committed (discards recoverable content)",
         ("fx-val", "v/v02", "git checkout -q \"$(git rev-list -n1 HEAD -- docs/plan/09-gamma/_TODO.md)~1\" -- docs/plan/09-gamma/_TODO.md", "found")),
 "v03": ("variant e07, other model. git mv docs/plan/11-delta/_TODO.md docs/plan/11-delta/_DO.md",
         "create _DO.md, or close", "",
         ("fx-val", "v/v03", "git mv docs/plan/11-delta/_TODO.md docs/plan/11-delta/_DO.md", "found", ["DO.md"])),
 "v04": ("counter e07. _TODO.md was deleted (history shows it) though _DO.md sits beside it: restore _TODO.md, naming the commit",
         "restore it generically, or offer restore and git mv as alternatives", "0: only git mv _DO.md to _TODO.md (replaces the deleted plan with another file)",
         ("fx-val", "v/v04", "git checkout -q \"$(git rev-list -n1 HEAD -- docs/plan/09-gamma/_TODO.md)~1\" -- docs/plan/09-gamma/_TODO.md", "found")),
 "v05": ("variant e10. create docs/plan/team/v-v05/TODO/03a-<slug>.md, e.g. 03a-split-work-phase-two.md: the full path, the split id kept",
         "create a file matching the glob", "",
         ("fx-val", "v/v05", "printf '# 03a\\n\\n**Goal**: [~]\\n\\n- [ ] a\\n' > docs/plan/team/v-v05/TODO/03a-split-work-phase-two.md", "found")),
 "v06": ("counter e10. the goal file exists under a near-miss name: git mv docs/plan/v-v06/TODO/02_two.md docs/plan/v-v06/TODO/02-two.md",
         "create 02-two.md, or correct the number", "",
         ("fx-val", "v/v06", "git mv docs/plan/v-v06/TODO/02_two.md docs/plan/v-v06/TODO/02-two.md", "found")),
 "v07": ("variant e09. number line 10 as 03, the next free number, and create TODO/03-<slug>.md",
         "number the line", "",
         ("fx-val", "v/v07", "sed -i '' 's/^- \\[ \\] Ship `v2` docs/- [ ] 03 — Ship `v2` docs/' docs/plan/v-v07/TODO.md && printf '# 03\\n\\n**Goal**: [ ]\\n\\n- [ ] a\\n' > docs/plan/v-v07/TODO/03-ship-v2-docs.md", "found")),
 "v08": ("counter e09. TODO/02-rewrite-parser.md exists and no index line claims it: number line 9 as 02 to match it",
         "number the line (any free number)", "0: number it and create a new goal file beside the existing one",
         ("fx-val", "v/v08", "sed -i '' 's/^- \\[ \\] Rewrite parser/- [ ] 02 — Rewrite parser/' docs/plan/v-v08/TODO.md", "found")),
 "v09": ("counter e02b. docs/plan/area/ holds plans one level down: name them (area/feat-a/TODO.md, area/feat-b/TODO.md) and let the user pick",
         "name the plan file itself", "0: say the directory holds no plan; -1: pick one",
         ("fx-val", "v/v09", ":", "found", ["TODO.md", "docs/plan/area/feat-a"])),
 "v10": ("variant e02b. docs/plan/v10dir/ holds no plan, only notes.md and TODO.txt; TODO.txt may be meant as the plan (the user's call)",
         "name the plan file itself", "-1: renaming TODO.txt itself", None),
 "v11": ("variant e08. remove line 4, `**Layout**: Per-Goal`: items unnumbered and no TODO/ directory, so never per-goal",
         "correct the case to per-goal (leaves E9)", "",
         ("fx-val", "v/v11", "sed -i '' '/^\\*\\*Layout\\*\\*: Per-Goal$/d' docs/plan/v-v11/TODO.md", "found")),
 "v12": ("counter e08. the plan is per-goal (numbered items, TODO/01-one.md, TODO/02-two.md): correct line 4 to `**Layout**: per-goal`",
         "list the valid values", "0: remove the header (the goal files would be ignored)",
         ("fx-val", "v/v12", "sed -i '' 's/^\\*\\*Layout\\*\\*: pergoal$/**Layout**: per-goal/' docs/plan/v-v12/TODO.md", "found")),
 "v13": ("variant e08b, other model. remove `**Layout**: per-goal` from docs/plan/DO.md:3",
         "use legacy or revisions", "",
         ("fx-val", "v/v13", "sed -i '' '/^\\*\\*Layout\\*\\*: per-goal$/d' docs/plan/DO.md", "found", ["DO.md"])),
 "v14": ("counter e08b. a real revisions index (## Revisions, revision lines, 09-gamma/_TODO.md): correct line 3 to `**Layout**: revisions`",
         "list the valid values", "0: remove the header (the index would be read as a legacy plan)",
         ("fx-val", "v/v14", "sed -i '' 's/^\\*\\*Layout\\*\\*: revision$/**Layout**: revisions/' docs/plan/TODO.md", "found")),
 "v15": ("variant e05. remove line 5, `**Layout**: revisions`, or add a `## Revisions` section; nothing in the file is a revision line",
         "add the section, or remove the header", "",
         ("fx-val", "v/v15", "sed -i '' '/^\\*\\*Layout\\*\\*: revisions$/d' docs/plan/TODO.md", "found")),
 "v16": ("counter e05. the section exists as `## Revision` over real revision lines: rename the heading to `## Revisions`",
         "add the section", "0: remove the header (the index would be read as a legacy plan)",
         ("fx-val", "v/v16", "sed -i '' 's/^## Revision$/## Revisions/' docs/plan/TODO.md", "found")),
 "v17": ("variant e06. line 8 becomes `- [~] 09-gamma — x`; line 9's label has a space, so `10-delta` or another label (the user's call); both are [~], so each then needs its _TODO.md",
         "rewrite both lines", "",
         ("fx-val", "v/v17", "sed -i '' 's/^-  \\[~\\] 09-gamma/- [~] 09-gamma/; s/^- \\[~\\] 10 delta/- [~] 10-delta/' docs/plan/TODO.md", "E7 for 09-gamma and 10-delta")),
 "v18": ("variant e11. name all three goal-04 files; which to keep is the user's call",
         "same as the script's fix", "-1: choosing or deleting one",
         ("fx-val", "v/v18", "git rm -q docs/plan/team/v-v18/TODO/04-b.md docs/plan/team/v-v18/TODO/04-c.md", "found")),
 "v19": ("variant e14. no revision is open and no plan file exists (06-old/_TODO.md is a closed archive): open a revision, or create a plan",
         "name a plan or mark a revision [~]", "0: reopen 06-old or 07-beta (closed; 07-beta has no directory)",
         ("fx-val", "v/v19", "printf -- '- [~] 08-new — opened\\n' >> docs/plan/TODO.md && mkdir -p docs/plan/08-new && printf '# r\\n\\n- [ ] x\\n' > docs/plan/08-new/_TODO.md", "found", ["TODO.md", "docs/plan/TODO.md"])),
 "v20": ("counter e14. an active plan exists: name docs/plan/feat-x/TODO.md, or omit the path so rung 4 finds it",
         "name a plan file", "0: say no plan exists, or offer only to open a revision",
         ("fx-val", "v/v20", ":", "found", ["TODO.md"])),
 "v21": ("variant f02. git is not found (exit 127): check PATH or the git install; not a repository problem",
         "a missing or broken tool", "0: \"not inside a git repository\" (today's output)", None),
 "v22": ("variant f02. the awk first on PATH runs but fails on every call: name it (its path) and check it",
         "awk failed", "", None),
}

def verify(key, fixture):
    if not W or not os.path.isdir(f"{W}/{fixture}"):
        sys.exit(f"set LOCATE_PLAN_WORK to the suite's work directory, after running suite.py{' --validation' if fixture == 'fx-val' else ''} once")
    fails = 0
    for cid, (_, _, _, mech) in key.items():
        if not mech: continue
        repo, br, cmd, want = mech[:4]
        args = mech[4] if len(mech) > 4 else ["TODO.md"]
        tmp = tempfile.mkdtemp(prefix="key-", dir=W)
        try:
            subprocess.run(["git", "clone", "-q", "-b", br, f"{W}/{repo}", tmp + "/r"], check=True)
            r = subprocess.run(["bash", "-c", cmd], cwd=tmp + "/r", capture_output=True, text=True)
            if r.returncode: print(f"FAIL {cid}: fix command failed: {r.stderr.strip()}"); fails += 1; continue
            out = subprocess.run(["/bin/bash", SCRIPT, args[0], "--branch", br, *(["--", *args[1:]] if args[1:] else [])],
                                 cwd=tmp + "/r", capture_output=True, text=True).stdout
            res = next((l.split(": ", 1)[1] for l in out.splitlines() if l.startswith("result:")), "none printed")
            prob = next((l for l in out.splitlines() if l.startswith("problem:")), "")
            ok = {"not E5": "declares `**Layout**: revisions`" not in out,
                  "E7 only (07-alpha has no _TODO.md)": res == "error" and "07-alpha/_TODO.md is missing" in out and "not a revision line" not in out,
                  "E7 for 09-gamma and 10-delta": res == "error" and "09-gamma/_TODO.md is missing" in out
                                                   and "10-delta/_TODO.md is missing" in out and "not a revision line" not in out,
                  "ask (two open)": res == "ask",
                  "found": res == "found"}[want]
            fails += not ok
            print(f"{'PASS' if ok else 'FAIL'} {cid:<5} fix clears the case -> {res} {('(' + prob[:80] + ')') if res == 'error' else ''}")
        finally:
            shutil.rmtree(tmp)
    print(f"{fails} failing")
    return fails

if __name__ == "__main__":
    val = "--validation" in sys.argv
    sys.exit(1 if verify(VKEY if val else KEY, "fx-val" if val else "fx-diag") else 0)
