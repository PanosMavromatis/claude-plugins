"""check-draft.sh suite: runs the script on files built here, one directory per case, and
grades every report. Writes only under $LOCATE_PLAN_WORK, which must lie outside the
repository, the rule dev/locate-plan/ uses.

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--script PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

The script reads plan-drafter's reply and, with --plan, the plan file as written. An f
case, on the draft's form, runs on both: as a reply, the draft in its fence with a trace
that covers it (its id ends in r), and as a plan file, the draft alone (p). A draft's line
k is line k of the plan and line k + 3 of the reply. Every case runs twice under each shell
found and must print the same thing each time. Every report is checked for key order, exit
code, problem and fix text, one fix per problem, each resolved tag's where: window, the
message its input calls for, nothing on stderr, no absolute paths, and that no file was
changed. --mutants applies each patch in
mutants/ to a copy of the script and its library, scripts/lib/plan-rules.sh, and runs the
suite on it once: each must fail it, and a patch that no longer applies is reported stale.
A patch names its file relative to scripts/."""
import hashlib, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCRIPT = REPO + "/plugins/workflow-coding/scripts/check-draft.sh"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
LIB = os.path.dirname(SCRIPT) + "/lib/plan-rules.sh"
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
FX = W + "/cd"
SHELLS = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if os.access(s, os.X_OK)]
if "--once" in sys.argv: SHELLS = SHELLS[:1]
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
AWK127 = f"{W}/bin/{h('cd-awk-127')}"
KEYS = ["result", "input", "file", "spec", "subgoals", "tags", "where", "problem", "fix", "message"]
EQUIVALENT = set()

# The draft: line k is line k of a plan file and line k + 3 of a reply.
DRAFT = ["# Revision 09-next", "", "**Status**: open", "**Version**: workflow-coding 0.12.0",   # 1-4
         "**Opened**: 2026-10-14", "**Spec**: spec.md", "", "## Preamble", "",                  # 5-9
         "Why this revision exists.", "", "## Settled decisions", "",                          # 10-13
         "- Keep a Changelog, from now on.", "", "## Subgoals", "",                            # 14-17
         "- [ ] 1. Add the changelog", "  Scope: `CHANGELOG.md`. Acceptance: it lists 0.11.0.",  # 18-19
         "- [ ] 2. Check the draft's form", "  Scope: `scripts/check-draft.sh`. Acceptance: its suite passes."]  # 20-21
TRACE = ['- 1. §2.1 The changelog; "Keep a Changelog"', "- 2. Form checks, first item"]
SPEC = ["# A spec", "", "## 2. Releases", "", "### 2.1 The changelog", "",
        "Every release is recorded. Keep a", "  Changelog, from now on.", "", "## Form checks", "",
        "- check the draft; then the trace", "", "```markdown", "## Fenced heading", "```"]

def edit(lines, k, *new): return lines[:k - 1] + list(new) + lines[k:]       # line k becomes new; none drops it
def ins(lines, k, *new): return lines[:k - 1] + list(new) + lines[k - 1:]    # new goes before line k
def reply(draft=DRAFT, trace=TRACE, info="markdown", secs=("Draft", "Trace", "Left out", "Questions"),
          body=None, left=("none",)):
    parts = {"Draft": body if body is not None else ["~~~" + info, *draft, "~~~"], "Trace": list(trace),
             "Left out": list(left), "Questions": ["none"]}
    out = []
    for i, s in enumerate(secs): out += ([""] if i else []) + [f"## {s}", ""] + parts.get(s, ["notes"])
    return out

class Fmt(dict):   # {f} the file, {w} the draft or the plan, {dK} the draft's line K, {tK} the trace's
    def __init__(self, exp): super().__init__(f=exp.get("file", ""), w=exp.get("w", "")); self.exp = exp
    def __missing__(self, k):
        if k[0] == "d": return str(int(k[1:]) + self.exp.get("off", 0))
        if k[0] == "t": return str(int(k[1:]) + 7 + self.exp.get("n", 0))
        raise KeyError(k)

# id, files under cd/<id>/ as (lines, crlf), arguments (paths relative to cd/), expectations
C = []
def case(cid, files, args, **exp): C.append((cid, files, args, exp))
def rcase(cid, lines, *args, n=len(DRAFT), crlf=False, **exp):
    case(cid, {"reply.md": (lines, crlf)}, [f"{cid}/reply.md", *args],
         input="reply", file=f"{cid}/reply.md", off=3, n=n, w="the draft", **exp)
def pcase(cid, lines, *args, crlf=False, **exp):
    case(cid, {"plan.md": (lines, crlf)}, ["--plan", f"{cid}/plan.md", *args],
         input="plan", file=f"{cid}/plan.md", w="the plan", **exp)
def fcase(cid, draft, *args, trace=TRACE, crlf=False, **exp):
    rcase(cid + "r", reply(draft, trace), *args, n=len(draft), crlf=crlf, **exp)
    pcase(cid + "p", draft, *args, crlf=crlf, **exp)
NAMED = "names nothing in spec.md"

# --- the reply: its sections, its fence, its trace ------------------------------------
rcase("s01", reply(), result="clean", subgoals="2", tags="3, not checked: no spec given", spec="—",
      msg="its trace covers its 2 subgoals; its tags were not checked against a spec")
WHERE = ["1. spec.md:5-8 §2.1 The changelog", '1. spec.md:7 "Keep a Changelog"', "2. spec.md:10-16 Form checks, first item"]
rcase("s01b", reply(), "--spec", "spec.md", "--label", "09-next", result="clean", spec="spec.md",
      tags="3 of 3 resolve", where=WHERE, msg="every tag names a part of spec.md")
rcase("s02", reply(secs=("Draft", "Trace", "Questions")), result="problems", nprob=1, subgoals="2",
      prob=["the reply's sections are ## Draft, ## Trace, ## Questions, not ## Draft, ## Trace, ## Left out and ## Questions in that order"],
      fix=["return the four sections, in that order, and nothing else"])
rcase("s03", reply(secs=("Draft", "Left out", "Trace", "Questions")), result="problems", nprob=1,
      prob=["the reply's sections are ## Draft, ## Left out, ## Trace, ## Questions, not"])
rcase("s04", reply(secs=("Draft", "Trace", "Left out", "Questions", "Notes")), result="problems", nprob=1,
      prob=["the reply's sections are ## Draft, ## Trace, ## Left out, ## Questions, ## Notes, not"])
rcase("s04b", ["Here is the plan."], result="problems", nprob=1, subgoals="—",
      prob=["the reply's sections are none, not"])
rcase("s05", reply(body=["(the draft)"]), result="problems", nprob=1, subgoals="—",
      prob=["## Draft holds no ~~~markdown fence"], fix=["put the whole plan file in one `~~~markdown` fence under ## Draft"])
rcase("s06", reply(body=["~~~markdown", *DRAFT]), result="problems", nprob=2, subgoals="—",
      prob=["the reply's sections are ## Draft, not", "the draft's fence, opened at {f}:3, is never closed"],
      fix=["close it with a `~~~` line"])
rcase("s07", reply(info="md"), result="problems", nprob=1, prob=["{f}:3 opens the draft's fence as `~~~md`"],
      fix=["open it as `~~~markdown`"])
rcase("s07b", reply(info=""), result="problems", nprob=1, prob=["{f}:3 opens the draft's fence as `~~~`"])
rcase("s08", reply(body=["~~~markdown", *DRAFT, "~~~", "", "~~~", "## Not a section", "~~~"]), result="problems",
      nprob=1, prob=["{f}:27 opens a second fence under ## Draft"], fix=["keep the whole plan file in one fence"])
rcase("s09", reply(trace=[*TRACE, "Subgoal 3 was dropped."]), result="problems", nprob=1,
      prob=["{f}:{t3} is not a trace line: `Subgoal 3 was dropped.`"], fix=["write each trace line as `- N. <tag>`"])
rcase("s10", reply(trace=["- 1. §2.1 The changelog; ", TRACE[1]]), result="problems", nprob=1, tags="2, not checked: no spec given",
      prob=["{f}:{t1} has an empty tag"], fix=["tag the subgoal with the spec item it carries, or drop the empty tag"])
rcase("s10b", reply(trace=["- 1.", TRACE[1]]), result="problems", nprob=1, prob=["{f}:{t1} has an empty tag"])
rcase("s11", reply(trace=TRACE[::-1]), result="problems", nprob=2,
      prob=["{f}:{t1} traces subgoal 2 where subgoal 1 is next", "subgoal 2 has no trace line"],
      fix=["give each subgoal one trace line, in the draft's order"])
rcase("s12", reply(trace=[*TRACE, "- 3. Form checks"]), result="problems", nprob=1,
      prob=["{f}:{t3} traces subgoal 3, which the draft does not have"], fix=["trace only the draft's subgoals, 1 to 2"])
rcase("s13", reply(trace=TRACE[:1]), result="problems", nprob=1, prob=["subgoal 2 has no trace line"],
      fix=["tag each subgoal with the spec item it carries, one line each"])
rcase("s14", reply(trace=[]), result="problems", nprob=1, tags="0, not checked: no spec given",
      prob=["subgoals 1 to 2 have no trace line"])
rcase("s15", reply(trace=["- 0. Form checks", *TRACE]), result="problems", nprob=1,
      prob=["{f}:{t1} traces subgoal 0, which the draft does not have"])
rcase("s16", reply(trace=[TRACE[0], TRACE[0], TRACE[1]]), result="problems", nprob=1,
      prob=["{f}:{t2} traces subgoal 1 where subgoal 2 is next"])
rcase("s17", reply(left=["- [ ] a checkbox outside the draft"]), result="clean", subgoals="2")
# Claude Code hands a subagent's report back in a frame: a note before it, its agent id and
# usage after it, and two spaces before every line. A copy kept in its frame is the session's
# to write again; one with the note and trailer but no indent reads as the reply it holds.
NOTE = "[Subagent hand-back] The text below is the final report of a subagent this session delegated to. The report follows:"
TRAILER = ["agentId: a1b2c3 (use SendMessage with to: 'a1b2c3' to continue this agent)",
           "<usage>subagent_tokens: 14044", "tool_uses: 7", "duration_ms: 46834</usage>"]
FRAMED = "{f}:{line} has `## Draft` indented: the reply was copied inside the frame Claude Code puts around a subagent's report"
rcase("s19", [NOTE, *("  " + l for l in reply()), *TRAILER], result="problems", nprob=1, subgoals="—", tags="0, not checked: no spec given",
      prob=[FRAMED.replace("{line}", "2")], fix=["write the reply again as plan-drafter returned it, without the hand-back note before it"])
rcase("s19b", ["  " + l for l in reply()], result="problems", nprob=1, subgoals="—", prob=[FRAMED.replace("{line}", "1")])
rcase("s19c", [NOTE, *reply(), *TRAILER], result="clean", subgoals="2")
rcase("s19d", reply(left=["  ## Draft"]), result="clean", subgoals="2")
rcase("s18", reply(), crlf=True, result="clean", subgoals="2", tags="3, not checked: no spec given")

# --- the tags, against the spec -------------------------------------------------------
def tcase(cid, trace, spec="spec.md", **exp): rcase(cid, reply(trace=trace), "--spec", spec, spec=spec, **exp)
tcase("t01", ['- 1. "Keep a Changelog"', "- 2. Form checks"], result="clean", tags="2 of 2 resolve",
      where=['1. spec.md:7 "Keep a Changelog"', "2. spec.md:10-16 Form checks"])
tcase("t02", ["- 1. “Keep a Changelog”", "- 2. Form checks"], result="clean", tags="2 of 2 resolve",
      where=['1. spec.md:7 "Keep a Changelog"', "2. spec.md:10-16 Form checks"])
tcase("t03", ["- 1. §2.1; §9.9", "- 2. §2"], result="problems", nprob=1, tags="2 of 3 resolve",
      where=["1. spec.md:5-8 §2.1", "2. spec.md:3-8 §2"],
      prob=["{f}:{t1} has the tag `§9.9`, which " + NAMED],
      fix=["tag with a heading or § as spec.md writes it, or a phrase copied from it verbatim"])
tcase("t04", ["- 1. Form checksum", "- 2. Form checks: the first item"], result="problems", nprob=1,
      tags="1 of 2 resolve", prob=["{f}:{t1} has the tag `Form checksum`, which " + NAMED])
tcase("t05", ["- 1. Fenced heading", "- 2. Form checks"], result="problems", nprob=1,
      prob=["{f}:{t1} has the tag `Fenced heading`, which " + NAMED])
tcase("t06", ['- 1. "check the draft; then the trace"', "- 2. §2.1"], result="clean", tags="2 of 2 resolve",
      where=['1. spec.md:12 "check the draft; then the trace"', "2. spec.md:5-8 §2.1"])
tcase("t07", ['- 1. "Keep a Changelog', "- 2. Form checks"], result="problems", nprob=1, tags="1 of 2 resolve",
      prob=['{f}:{t1} has the tag `"Keep a Changelog`, which ' + NAMED])
tcase("t08", ["- 1. § intro", "- 2. Form checks"], result="problems", nprob=1, prob=["{f}:{t1} has the tag `§ intro`"])
tcase("t09", TRACE, spec="spec-crlf.md", result="clean", tags="3 of 3 resolve",
      where=[w.replace("spec.md", "spec-crlf.md") for w in WHERE])
tcase("t10", ['- 1. "  "', "- 2. Form checks"], result="problems", nprob=1, prob=['{f}:{t1} has the tag `"  "`'])
tcase("t11", ["- 1. Form checks;first item", "- 2. §2"], result="clean", tags="2 of 2 resolve",
      where=["1. spec.md:10-16 Form checks;first item", "2. spec.md:3-8 §2"])
tcase("t12", ['- 1. "Keep  a Changelog"', "- 2. §2"], result="clean", tags="2 of 2 resolve",
      where=['1. spec.md:7 "Keep  a Changelog"', "2. spec.md:3-8 §2"])
tcase("t13", ["- 1. 2.1 The changelog, its first line", "- 2. The changelog"], result="problems", nprob=1,
      tags="1 of 2 resolve", where=["1. spec.md:5-8 2.1 The changelog, its first line"],
      prob=["{f}:{t2} has the tag `The changelog`"])
tcase("t15", ['- 1. "A spec"', '- 2. "Fenced heading"'], result="clean", tags="2 of 2 resolve",
      where=['1. spec.md:1 "A spec"', '2. spec.md:15 "Fenced heading"'])
rcase("t16", reply(edit(DRAFT, 3, "**Status**: active"), ["- 1. §9.9", "- 2. §2"]), "--spec", "spec.md", spec="spec.md",
      result="problems", nprob=2, tags="1 of 2 resolve", where=["2. spec.md:3-8 §2"],
      prob=["{f}:{d3} has `**Status**: active`", "{f}:{t1} has the tag `§9.9`, which " + NAMED])
case("t14", {}, ["s01/reply.md", "--spec", "nope.md"], result="error", input="reply", spec="nope.md", subgoals="—",
     tags="—", nprob=1, prob=["nope.md does not exist"], fix=["pass the spec's path"])

# --- the draft's form, in a reply and in a plan file -------------------------------------
fcase("f00", DRAFT, "--label", "09-next", result="clean", subgoals="2")
FIRST = "{f}:{d1}, {w}'s first line, reads "
fcase("f01", edit(DRAFT, 1, "# 09-next"), result="problems", nprob=1,
      prob=[FIRST + "`# 09-next`, not `# Revision <label>`"], fix=["begin {w} `# Revision <label>`, with the revision's label"])
fcase("f02", edit(DRAFT, 1, "# Revision 09 next"), result="problems", nprob=1,
      prob=[FIRST + "`# Revision 09 next`, not `# Revision <label>`"])
fcase("f02b", edit(DRAFT, 1, "# Revision"), result="problems", nprob=1, prob=[FIRST + "`# Revision`, not"])
fcase("f03", DRAFT, "--label", "09-other", result="problems", nprob=1,
      prob=[FIRST + "`# Revision 09-next`, not `# Revision 09-other`"], fix=["begin {w} `# Revision 09-other`"])
fcase("f04", edit(DRAFT, 3, "**Status**: active"), result="problems", nprob=1,
      prob=["{f}:{d3} has `**Status**: active`; a revision opens `open`"], fix=["write `**Status**: open`"])
fcase("f04b", ins(DRAFT, 4, "**Status**: closed"), result="problems", nprob=1,
      prob=["{f}:{d4} has `**Status**: closed`; a revision opens `open`"])
fcase("f05", edit(DRAFT, 4, "**Version**:"), result="problems", nprob=1, prob=["{f}:{d4} has an empty `**Version**:`"],
      fix=["state the version each package reaches"])
fcase("f06", edit(DRAFT, 5, "**Opened**: 2026-1-4"), result="problems", nprob=1,
      prob=["{f}:{d5} has `**Opened**: 2026-1-4`, not a date"], fix=["write the date the revision opens, as YYYY-MM-DD"])
fcase("f07", edit(DRAFT, 6, "**Spec**: "), result="problems", nprob=1, prob=["{f}:{d6} has an empty `**Spec**:`"],
      fix=["name the spec"])
fcase("f08", edit(DRAFT, 6), result="problems", nprob=1,
      prob=["{w} has no `**Spec**:` line before its first ## heading"], fix=["add it to the header"])
fcase("f09", ins(edit(DRAFT, 3), 8, "**Status**: open"), result="problems", nprob=1,
      prob=["{w} has no `**Status**:` line before its first ## heading"])
fcase("f10", edit(DRAFT, 12, "## Decisions"), result="problems", nprob=1,
      prob=["{w}'s ## headings are ## Preamble, ## Decisions, ## Subgoals, not ## Preamble, ## Settled decisions and ## Subgoals in that order"],
      fix=["use subdividing.md's three sections, in that order, and no others"])
fcase("f11", [*DRAFT, "", "## Notes", "", "Later."], result="problems", nprob=1,
      prob=["{w}'s ## headings are ## Preamble, ## Settled decisions, ## Subgoals, ## Notes, not"])
fcase("f12", ins(DRAFT, 11, "", "```markdown", "## Not a heading", "- [ ] 9. Not a subgoal", "```"),
      result="clean", subgoals="2")
fcase("f13", edit(DRAFT, 14, "- [ ] Keep a Changelog, from now on."), result="problems", nprob=1, subgoals="2",
      prob=["{f}:{d14} is a checkbox under ## Settled decisions, outside ## Subgoals: `- [ ] Keep a Changelog, from now on.`"],
      fix=["write it as a plain `- ` bullet"])
fcase("f13b", ins(DRAFT, 7, "- [ ] stray"), result="problems", nprob=1,
      prob=["{f}:{d7} is a checkbox under no heading, outside ## Subgoals: `- [ ] stray`"])
fcase("f14", edit(DRAFT, 20, "- [ ] 3. Check the draft's form"), result="problems", nprob=1,
      prob=["{f}:{d20} reads `- [ ] 3. Check the draft's form`, where subgoal 2 should begin `- [ ] 2. `"],
      fix=["number the subgoals from 1, in order"])
fcase("f15", edit(DRAFT, 18, "- [ ] Add the changelog"), result="problems", nprob=1,
      prob=["{f}:{d18} reads `- [ ] Add the changelog`, where subgoal 1 should begin `- [ ] 1. `"])
fcase("f15b", edit(DRAFT, 18, "- [x] 1. Add the changelog"), result="problems", nprob=1,
      prob=["{f}:{d18} reads `- [x] 1. Add the changelog`, where subgoal 1"])
fcase("f16", ins(DRAFT, 19, ""), result="problems", nprob=1, subgoals="2",
      prob=["subgoal 1, at {f}:{d18}, has no `Scope: … Acceptance: …` line in its block"],
      fix=["put that line directly under it, indented two spaces, with no blank line between"])
fcase("f16b", ins(DRAFT, 19, "  "), result="problems", nprob=1, prob=["subgoal 1, at {f}:{d18}, has no `Scope:"])
fcase("f17", edit(DRAFT, 21, "  Scope: `scripts/check-draft.sh`. Acceptance: its suite", "  passes."), result="problems",
      nprob=1, prob=["subgoal 2, at {f}:{d20}, runs to line {d22}: a subgoal is two lines"],
      fix=["write its scope and acceptance as one `Scope: … Acceptance: …` line"])
fcase("f18", edit(DRAFT, 19, "  Scope: `CHANGELOG.md`."), result="problems", nprob=1,
      prob=["{f}:{d19} is not `Scope: … Acceptance: …`"], fix=["write subgoal 1's second line as"])
fcase("f18b", edit(DRAFT, 19, "Scope: `CHANGELOG.md`. Acceptance: it lists 0.11.0."), result="problems", nprob=1,
      prob=["subgoal 1, at {f}:{d18}, has no `Scope:"])
fcase("f19", [*DRAFT, "> **Done:** already"], result="problems", nprob=1,
      prob=["{f}:{d22} is a `> **Branch:**` or `> **Done:**` line"], fix=["/new-branch and /smart-merge write those"])
fcase("f19b", [*DRAFT, "> **Branch:** feat/x"], result="problems", nprob=1, prob=["{f}:{d22} is a `> **Branch:**`"])
fcase("f19c", [*DRAFT, "  > **Branch:** feat/x"], result="problems", nprob=2,
      prob=["subgoal 2, at {f}:{d20}, runs to line {d22}", "{f}:{d22} is a `> **Branch:**`"])
fcase("f20", DRAFT[:17], trace=[], result="problems", nprob=1, subgoals="0",
      prob=["{w} has no subgoals under ## Subgoals"], fix=["subdivide the spec into subgoals"])
fcase("f21", [], result="problems", nprob=1, subgoals="—", prob=["{w} is empty"], fix=["write the whole plan file"])
fcase("f22", DRAFT, crlf=True, result="clean", subgoals="2")
fcase("f22b", edit(DRAFT, 20, "- [ ] 3. Check the draft's form"), crlf=True, result="problems", nprob=1,
      prob=["{f}:{d20} reads `- [ ] 3. Check the draft's form`, where"])

# --- a plan file, as edited, and an input given the wrong way ------------------------------
EDITED = ins(DRAFT, 19, "")                                          # a blank line inside subgoal 1
EDITED = edit(EDITED, 21, "- [ ] 3. Check the draft's form")           # renumbered by hand
EDITED = edit(EDITED, 22, "  Scope: `scripts/check-draft.sh`. Acceptance: its suite", "  passes.")   # rewrapped
pcase("p01", EDITED, result="problems", nprob=3, subgoals="2",
      prob=["subgoal 1, at {f}:18, has no `Scope:", "{f}:21 reads `- [ ] 3. Check the draft's form`",
            "subgoal 2, at {f}:21, runs to line 23"])
pcase("p02", reply(), result="problems", nprob=6,
      prob=["{f}:1, the plan's first line, reads `## Draft`", "the plan has no `**Status**:` line"])
rcase("p03", DRAFT, result="problems", nprob=1, subgoals="—",
      prob=["the reply's sections are ## Preamble, ## Settled decisions, ## Subgoals, not"])

# --- usage, and files that cannot be checked ---------------------------------------------
case("u01", {}, [], raw=True, exit=2, err=["give one file"])
case("u02", {}, ["s01/reply.md", "s02/reply.md"], raw=True, exit=2, err=["give one file"])
case("u03", {}, ["--foo", "s01/reply.md"], raw=True, exit=2, err=["unknown option '--foo'"])
case("u04", {}, ["s01/reply.md", "--spec"], raw=True, exit=2, err=["--spec needs a path"])
case("u05", {}, ["--plan", "f00p/plan.md", "--spec", "spec.md"], raw=True, exit=2, err=["a plan file has none"])
case("u06", {}, ["s01/reply.md", "--label", "09 next"], raw=True, exit=2, err=["a label holds no whitespace"])
case("u07", {}, ["nope.md"], result="error", input="reply", file="nope.md", spec="—", subgoals="—", tags="—", nprob=1,
     prob=["nope.md does not exist"], fix=["pass the file /master-plan wrote the drafter's reply to"])
case("u07b", {}, ["--plan", "nope.md"], result="error", input="plan", file="nope.md", nprob=1,
     prob=["nope.md does not exist"], fix=["pass the plan file as /master-plan wrote it"])
case("u08", {}, ["s01"], result="error", nprob=1, prob=["s01 is not a file"])
case("u09", {}, ["s01/reply.md"], chmod="s01/reply.md", result="error", nprob=1,
     prob=["s01/reply.md cannot be read"], fix=["chmod u+r s01/reply.md"])
case("u10", {}, ["s01/reply.md"], awk127=True, raw=True, exit=3,
     err=["check-draft.sh: awk failed reading s01/reply.md", "hint: awk exited 127"])
case("u10b", {}, ["--plan", "f00p/plan.md"], awk127=True, raw=True, exit=3,
     err=["check-draft.sh: awk failed counting the lines of f00p/plan.md"])
case("u11", {}, ["--", "s01/reply.md"], result="clean", input="reply", file="s01/reply.md", subgoals="2")

def sh(args, cwd, env=None): return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)

def write(rel, lines, crlf=False):
    p = f"{FX}/{rel}"; os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="") as f: f.write("".join(l + ("\r\n" if crlf else "\n") for l in lines))

def build():
    shutil.rmtree(FX, ignore_errors=True); os.makedirs(FX)
    write("spec.md", SPEC); write("spec-crlf.md", SPEC, crlf=True)
    for cid, files, _, _ in C:
        for rel, (lines, crlf) in files.items(): write(f"{cid}/{rel}", lines, crlf)
    os.makedirs(AWK127, exist_ok=True)
    open(AWK127 + "/awk", "w").write("#!/bin/sh\nexit 127\n"); os.chmod(AWK127 + "/awk", 0o755)

def snap():
    out = {}
    for root, _, files in os.walk(FX):
        for fn in files: p = os.path.join(root, fn); out[p] = open(p, "rb").read()
    return out

def parse(out):
    rep, order, key = {}, [], None
    for line in out.splitlines():
        if line.startswith("  ") and key: rep[key].append(line[2:]); continue
        m = re.match(r"^([a-z-]+): (.*)$", line)
        if not m: return None, order
        key = m.group(1); order.append(key); rep[key] = [m.group(2)]
    return rep, order

def run(args, exp, shell):
    env = dict(os.environ); chmod = f"{FX}/{exp['chmod']}" if "chmod" in exp else None
    if exp.get("awk127"): env["PATH"] = AWK127 + ":" + env["PATH"]
    if chmod: os.chmod(chmod, 0)
    try: return sh([shell, SCRIPT, *args], FX, env)
    finally:
        if chmod: os.chmod(chmod, 0o644)

# What the message says to do next, by result and input; a reply's problems in its tags
# alone are questions for the user, and a reply copied in its frame is the session's to fix.
NEXT = {("clean", "reply"): "The draft has subdividing.md's form", ("clean", "plan"): "The plan has subdividing.md's form",
        ("problems", "reply"): "ask plan-drafter once for a fresh reply", ("problems", "plan"): "correct the plan file, then check it again",
        ("problems", "tags"): "in tags alone: ask the user, for each tag that names nothing in",
        ("problems", "framed"): "write the reply file again without the frame around plan-drafter's report",
        ("error", "reply"): "The reply could not be checked", ("error", "plan"): "The plan could not be checked"}

def grade(exp, r):
    probs = []
    want = exp.get("exit", 0 if exp.get("result") == "clean" else 1)
    if r.returncode != want: probs.append(f"exit {r.returncode}, want {want} (stderr: {r.stderr.strip()[:80]!r})")
    for e in exp.get("err", []):
        if e not in r.stderr: probs.append(f"stderr lacks {e!r}: {r.stderr.strip()[:120]!r}")
    if exp.get("raw"):
        if r.stdout: probs.append("a report printed on a raw failure")
        return probs
    if r.stderr: probs.append(f"stderr beside a report: {r.stderr.strip()[:120]!r}")
    rep, order = parse(r.stdout)
    if rep is None: return probs + [f"unparseable report: {r.stdout[:120]!r}"]
    if order != KEYS: return probs + [f"keys {order}"]
    fm = Fmt(exp)
    one = lambda k: "\n".join(rep[k])
    allv = lambda k: [] if rep[k] == ["—"] else rep[k]
    if exp.get("input") == "plan": exp = {"spec": "—", "tags": "—", **exp}    # a plan file has no trace
    for k in ("result", "input", "file", "spec", "subgoals", "tags"):
        if k in exp and one(k) != exp[k]: probs.append(f"{k}: want {exp[k]!r} got {one(k)!r}")
    if "where" in exp and allv("where") != exp["where"]: probs.append(f"where: want {exp['where']} got {allv('where')}")
    if one("spec") == "—" and allv("where"): probs.append(f"where without a spec: {allv('where')}")
    for k, key in (("prob", "problem"), ("fix", "fix")):
        for w in exp.get(k, []):
            w = w.format_map(fm)
            if not any(w in v for v in allv(key)): probs.append(f"{key} lacks {w!r}: {allv(key)}")
    if len(allv("problem")) != len(allv("fix")): probs.append(f"{len(allv('problem'))} problems but {len(allv('fix'))} fixes")
    if "nprob" in exp and len(allv("problem")) != exp["nprob"]: probs.append(f"{len(allv('problem'))} problems, want {exp['nprob']}: {allv('problem')}")
    res = one("result")
    if res == "clean" and allv("problem"): probs.append("a problem on a clean result")
    if res in ("problems", "error") and not allv("problem"): probs.append(f"{res} without a problem")
    if "msg" in exp and exp["msg"].format_map(fm) not in one("message"): probs.append(f"message lacks {exp['msg']!r}: {one('message')!r}")
    tags_alone = res == "problems" and one("input") == "reply" and all("which names nothing in" in p for p in allv("problem"))
    framed = res == "problems" and any("has `## Draft` indented" in p for p in allv("problem"))
    nxt = NEXT.get((res, "framed" if framed else "tags" if tags_alone else one("input")))
    if nxt is None or nxt not in one("message"): probs.append(f"message lacks {nxt!r} for {res} on a {one('input')}: {one('message')!r}")
    for k in KEYS:
        for v in rep[k]:
            if v.startswith("/") or W in v: probs.append(f"an absolute path in {k}: {v[:80]!r}")
    return probs

def static_checks():
    src = open(SCRIPT).read() + "\n" + open(LIB).read()
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#")); probs = []
    if "<<" in code: probs.append("a heredoc or here-string (a temporary file on Bash 3.2)")
    if "mktemp" in code: probs.append("mktemp")
    for m in re.finditer(r"(?:^|\s)[0-9]?>>?(?!=)\s*([^\s)\"';|]+)", code.replace("goal > 0", "")):
        if m.group(1) != "/dev/null" and not m.group(1).startswith("&"): probs.append(f"a redirect to {m.group(1)}")
    for bad in ("globstar", "mapfile", "readarray", "declare -A", ",,}", "^^}"):
        if bad in code: probs.append(f"Bash 4 feature {bad}")
    if re.search(r"grep[^|\n]*\\\|", code): probs.append("grep with \\| alternation")
    return probs

def mutants():
    d = HERE + "/mutants"; tmp = W + "/cd-mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; root = f"{tmp}/{name}"; out = root + "/check-draft.sh"
        os.makedirs(root + "/lib"); shutil.copy2(SCRIPT, out); shutil.copy2(LIB, root + "/lib/plan-rules.sh")
        ap = sh(["patch", "-s", "-F0", "-p1", "-d", root, "-i", f"{d}/{fn}"], tmp)
        if ap.returncode:
            bad += 1; print(f"STALE  {name}: the patch no longer applies ({(ap.stdout + ap.stderr).strip()[:120]})"); continue
        r = sh([sys.executable, "-I", os.path.abspath(__file__), "--once", "--script", out], HERE)
        killed = r.returncode != 0
        why = next((l for l in r.stdout.splitlines() if l.startswith("FAIL") or (l.startswith("static:") and l != "static: ok")), "")
        if name in EQUIVALENT:
            ok = not killed; print(f"{'EQUIV ' if ok else 'CHANGED'} {name}")
        else:
            ok = killed; print(f"{'KILLED' if ok else 'SURVIVED'} {name}" + (f"  ({why[:90]})" if ok else ""))
        bad += not ok
    shutil.rmtree(tmp); print(f"\n{bad} failing"); sys.exit(1 if bad else 0)

def main():
    if "--mutants" in sys.argv: mutants()
    ids = {c[0] for c in C}
    want = [a for a in sys.argv[1:] if a in ids]
    build()
    before = snap()
    st = static_checks(); print("static: " + ("ok" if not st else "; ".join(st)))
    fails = len(st)
    for cid, _, args, exp in C:
        if want and cid not in want: continue
        outs, probs = set(), []
        for shell in SHELLS:
            for _ in range(1 if "--once" in sys.argv else 2):
                r = run(args, exp, shell); outs.add((r.returncode, r.stdout, r.stderr))
                probs += [p for p in grade(exp, r) if p not in probs]
        if snap() != before: probs.append("a file changed"); before = snap()
        if len(outs) > 1: probs.append("output differs between runs or shells")
        print(f"{'PASS' if not probs else 'FAIL'} {cid:<5} " + "; ".join(probs))
        if "-v" in sys.argv: print("".join(o[1] + o[2] for o in sorted(outs)))
        fails += bool(probs)
    print(f"\n{fails} failing"); sys.exit(1 if fails else 0)

main()
