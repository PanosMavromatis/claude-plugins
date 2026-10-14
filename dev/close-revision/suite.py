"""close-revision.sh suite: runs the script directly on a fixture repository built here, one
orphan branch per case (the script reads the repository's own root plan), and grades the exit
code, the report key by key, and a rendered file byte for byte. Writes only under
$LOCATE_PLAN_WORK, which must lie outside the repository (the rule dev/locate-plan/ uses, for
the same reasons).

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--script PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

Every case runs twice under each shell found and must print the same thing each time. A
--check case first writes what the close would write, by hand, from the expectations here
and never from the script's own --render, so a wrong render cannot pass a wrong check; it
must leave that working tree as it found it, and is reset after. Every other case must leave
the fixture untouched. A report is always the twelve keys of close-revision-spec.md, in
order, with no absolute path. --mutants applies each patch in mutants/ to a copy of the
script and its library and runs the suite on it once; each must fail it. A patch names the
file it changes relative to scripts/: close-revision.sh, or lib/plan-rules.sh."""
import hashlib, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCRIPT = REPO + "/plugins/workflow-coding/scripts/close-revision.sh"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
LIB = os.path.dirname(SCRIPT) + "/lib/plan-rules.sh"   # sourced by the script, from beside it
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
FX = W + "/crv"
SHELLS = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if os.access(s, os.X_OK)]
if "--once" in sys.argv: SHELLS = SHELLS[:1]
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
AWK127 = f"{W}/bin/{h('crv-awk-127')}"
AWKSEL = {"awk-section": (f"{W}/bin/{h('crv-awk-section')}", "## Subgoals"),
          "awk-pointer": (f"{W}/bin/{h('crv-awk-pointer')}", "- **Revision")}
CAT141 = f"{W}/bin/{h('crv-cat-141')}"   # a cat killed by SIGPIPE, as a writer is when its reader stops early
NOREPO = f"{W}/norepo-{h('crv-norepo')}"
DATE = "2026-10-11"

KEYS = ["result", "layout", "root", "revision", "change", "edits", "section", "pointer", "moves", "warnings", "problem", "fix"]
UNFIN = "finish each, descope it ([-]), or move it to another revision; whether the revision is finished is your call"
BEFORE = "--check runs before the commit, against HEAD as it was when the close was proposed"

# --- fixtures. Line numbers matter: the cases name them. ---

# A legacy root plan: one revision still open, one ready to close (08-c, subtitled) whose
# section holds a duplicated backlink, a fenced block with a heading, an item and a backlink
# in it, a backlink to a branch with no plan, and closed pointers below.
LEGACY = """# Master plan

**Status**: active

## Subgoals — revision 07-rev-2

- [ ] other open

## Subgoals — revision 08-c: A subtitled heading

- [x] One
  > **Branch:** feat/one
  > **Done:** shipped — PR #1
- [-] Two
  > **Branch:** feat/two
- [x] Three
  > **Branch:** fix/three
  > **Branch:** feat/one
- [x] Four
  > **Branch:** feat/gone

```markdown
- [ ] fenced, not an item
## Not a heading
> **Branch:** feat/fenced
```

## Closed revisions

Extracted by `/close-revision` once finished.

- **Revision 05-old** — closed. See `docs/plan/05-old/_TODO.md`.

## Deferred

Nothing.
"""
LL = LEGACY.split("\n")
POINTER = "- **Revision 08-c** — A subtitled heading — closed. See `docs/plan/08-c/_TODO.md`."
ARCHIVE = "\n".join(LL[8:26]) + "\n"                                  # lines 9-26: the section, less its trailing blank line 27
ROOT_AFTER = "\n".join(LL[0:8] + LL[27:32] + [POINTER] + LL[32:])     # cut, pointer after line 32
MERGED = "# b\n\n**Status**: merged — PR #1 — 2026-10-01\n"
ACTIVE = "# b\n\n**Status**: active\n"
LG = {"docs/plan/TODO.md": LEGACY, "docs/plan/feat-one/TODO.md": MERGED, "docs/plan/feat-two/TODO.md": ACTIVE,
      "docs/plan/grp/fix-three/TODO.md": MERGED, "docs/plan/feat-fenced/TODO.md": MERGED,
      "docs/plan/05-old/_TODO.md": "# Revision 05-old\n"}
LG_WARN = ["docs/plan/feat-two is not stamped merged (active), so it stays flat: file it by hand once it merges",
           "no plan directory named feat-gone under docs/plan/, for the branch feat/gone backlinked in the section"]
LG_MOVE = "git mv docs/plan/feat-one docs/plan/08-c/feat-one"
LG_COPY = dict(LG, **{"docs/plan/08-c/feat-one/TODO.md": MERGED})
LG_DEST = dict(LG, **{"docs/plan/08-c/_TODO.md": "# stale\n"})

def ptr(label): return f"- **Revision {label}** — closed. See `docs/plan/{label}/_TODO.md`."
P1 = ptr("01-a")
NOCLOSED_DEF = "# M\n\n## Subgoals — revision 01-a\n\n- [x] a\n\n## Deferred\n\nx\n"
NOCLOSED_DEF_AFTER = f"# M\n\n## Closed revisions\n\n{P1}\n\n## Deferred\n\nx\n"
NOCLOSED_END = "# M\n\nProse.\n\n## Subgoals — revision 01-a\n\n- [x] a\n"
NOCLOSED_END_AFTER = f"# M\n\nProse.\n\n## Closed revisions\n\n{P1}\n"
CLOSED_PROSE = "# M\n\n## Subgoals — revision 01-a\n\n- [x] a\n\n## Closed revisions\n\nNone yet.\n"
CLOSED_PROSE_AFTER = f"# M\n\n## Closed revisions\n\nNone yet.\n\n{P1}\n"
CLOSED_EMPTY = "# M\n\n## Subgoals — revision 01-a\n\n- [x] a\n\n## Closed revisions\n"
CLOSED_EMPTY_AFTER = f"# M\n\n## Closed revisions\n\n{P1}\n"
OPENSEC = "# M\n\n## Subgoals — revision 01-a\n\n- [x] a\n  - [ ] nested open\n- [!] b\n```\n- [ ] fenced\n```\n"
BSL = "# M\n\n## Subgoals — revision a\\tb\n\n- [x] a\n"

# A revisions index: closed, descoped, two open, and a fenced example line.
INDEX = """# Master plan

**Layout**: revisions

## Revisions

- [x] 05-old — closed
- [-] 06-dropped
- [~] 07-rev-2 — in flight
- [~] 08-new — the next one

```markdown
- [~] 09-fenced — an example
```
"""
REV8 = "# Revision 08-new\n\n**Status**: open\n**Version**: —\n\n## Subgoals\n\n- [x] 1. a\n  Scope: x.\n- [-] 2. b\n\n```markdown\n- [ ] fenced\n```\n"
REV7 = "# Revision 07-rev-2\n\n**Status**: open\n\n## Subgoals\n\n- [x] 1. a\n  - [ ] nested open\n- [!] 2. b\n"
IX = {"docs/plan/TODO.md": INDEX, "docs/plan/05-old/_TODO.md": "# Revision 05-old\n",
      "docs/plan/07-rev-2/_TODO.md": REV7, "docs/plan/08-new/_TODO.md": REV8,
      "docs/plan/08-new/feat-x/TODO.md": MERGED}
ST8 = "**Status**: closed — " + DATE
IDX8 = "- [x] 08-new — the next one — closed. See `docs/plan/08-new/_TODO.md`."
EDITS8 = f"docs/plan/08-new/_TODO.md:3: {ST8}\ndocs/plan/TODO.md:10: {IDX8}"
REV8_AFTER = REV8.replace("**Status**: open", ST8)
INDEX_AFTER = INDEX.replace("- [~] 08-new — the next one", IDX8)

# Large inputs: a reader that wants one match still reads to EOF. One that exits at its match
# leaves its writer (cat, git show, or the printf of the directory list) writing into a closed
# pipe once the rest outgrows awk's read and the pipe buffer, and the script then dies of it, or
# at the directory search warns falsely. Measured on 0.10.0, whose readers exited: every site
# failed every run from 256 KB, some runs at 128 KB, and none at 70 KB. BIG doubles 256 KB.
BIG = 512 * 1024
PAD = "".join(f"Padding {i:05d}: prose, not an item, a heading or a status line.\n" for i in range(9000))
# feat/gone's directory, grp/feat-gone, with BIG bytes of directory listing below it: found in
# the listing's first lines, so the search matches long before the end of its input.
DEEP = "docs/plan/grp/feat-gone/" + "d" * 240
BULK = {f"{DEEP}/{i:04d}-{'e' * 240}/.keep": "" for i in range(BIG // 500)}
assert len(PAD) > BIG and sum(len(os.path.dirname(p)) + 1 for p in BULK) > BIG
LGB = dict(LG, **BULK, **{"docs/plan/TODO.md": LEGACY + PAD, "docs/plan/feat-one/TODO.md": MERGED + PAD})
IXB = dict(IX, **{"docs/plan/TODO.md": INDEX + PAD, "docs/plan/08-new/_TODO.md": REV8 + PAD})

NONE = {"README.md": "x\n"}
BOTH = {"docs/plan/TODO.md": "# a\n", "docs/plan/DO.md": "# b\n"}
def crlf(files): return {k: v.replace("\n", "\r\n") for k, v in files.items()}

# --- the after-states a --check case writes before running the script ---

def write(rel, text): open(f"{FX}/{rel}", "w", newline="").write(text)
def gitmv(src, dst): git("mv", src, dst)
def stamp_ok(): write("docs/plan/08-new/_TODO.md", REV8_AFTER); write("docs/plan/TODO.md", INDEX_AFTER)
def stamp_extra(): write("docs/plan/08-new/_TODO.md", REV8_AFTER + "extra\n"); write("docs/plan/TODO.md", INDEX_AFTER)
def stamp_old():  # the stamp before 0.11.0: the marker flipped, the note alone
    write("docs/plan/08-new/_TODO.md", REV8_AFTER); write("docs/plan/TODO.md", INDEX.replace("- [~] 08-new — the next one", "- [x] 08-new — the next one"))
def stamp_crlf():  # an Edit of one line in a CRLF file keeps the CRs on the lines it did not touch
    write("docs/plan/08-new/_TODO.md", REV8_AFTER.replace("\n", "\r\n")); write("docs/plan/TODO.md", INDEX_AFTER.replace("\n", "\r\n"))
def extract_ok():
    os.makedirs(f"{FX}/docs/plan/08-c", exist_ok=True)
    write("docs/plan/08-c/_TODO.md", ARCHIVE); write("docs/plan/TODO.md", ROOT_AFTER)
    gitmv("docs/plan/feat-one", "docs/plan/08-c/feat-one")
def extract_blank():  # the archive as the section ran, trailing blank line kept
    extract_ok(); write("docs/plan/08-c/_TODO.md", ARCHIVE + "\n")
def extract_word():
    extract_ok(); write("docs/plan/08-c/_TODO.md", ARCHIVE.replace("shipped", "shiped"))
def extract_nomove():
    os.makedirs(f"{FX}/docs/plan/08-c", exist_ok=True)
    write("docs/plan/08-c/_TODO.md", ARCHIVE); write("docs/plan/TODO.md", ROOT_AFTER)
def extract_nocut():
    os.makedirs(f"{FX}/docs/plan/08-c", exist_ok=True)
    write("docs/plan/08-c/_TODO.md", ARCHIVE); gitmv("docs/plan/feat-one", "docs/plan/08-c/feat-one")
def extract_big():
    extract_ok(); write("docs/plan/TODO.md", ROOT_AFTER + PAD)
def stamp_big(): write("docs/plan/08-new/_TODO.md", REV8_AFTER + PAD); write("docs/plan/TODO.md", INDEX_AFTER + PAD)

LG_DONE = {"docs/plan/TODO.md": ROOT_AFTER, "docs/plan/08-c/_TODO.md": ARCHIVE, "docs/plan/08-c/feat-one/TODO.md": MERGED,
           "docs/plan/feat-two/TODO.md": ACTIVE, "docs/plan/grp/fix-three/TODO.md": MERGED,
           "docs/plan/feat-fenced/TODO.md": MERGED, "docs/plan/05-old/_TODO.md": "# Revision 05-old\n"}
IX_DONE = dict(IX, **{"docs/plan/TODO.md": INDEX_AFTER, "docs/plan/08-new/_TODO.md": REV8_AFTER})

def rep(**kv): return kv
STAMP = rep(layout="revisions", root="docs/plan/TODO.md", revision="docs/plan/08-new/_TODO.md")
LEG = rep(layout="legacy", root="docs/plan/TODO.md", revision="docs/plan/08-c/_TODO.md")
LEGOUT = dict(LEG, change="extract", section="docs/plan/TODO.md:9-27", pointer=POINTER, moves=LG_MOVE, warnings="\n".join(LG_WARN))
LGBOUT = dict(LEGOUT, warnings=LG_WARN[0])   # grp/feat-gone is feat/gone's directory, so only feat-two warns
D = ["--date", DATE]
# id, files on the case's branch, arguments (or a special), expectations[, an after-state for --check]
C = [
 # usage
 ("u01", NONE, D, dict(exit=2, err="no label given")),
 ("u02", NONE, ["01-a", "02-b"] + D, dict(exit=2, err="one label only")),
 ("u03", NONE, ["a/b"] + D, dict(exit=2, err="holds no whitespace")),
 ("u04", NONE, ["01-a"], dict(exit=2, err="--date is required")),
 ("u05", NONE, ["01-a", "--date", "2026-1-1"], dict(exit=2, err="--date takes YYYY-MM-DD")),
 ("u06", NONE, ["01-a", "--render", "both"] + D, dict(exit=2, err="--render takes root or archive")),
 ("u07", NONE, ["01-a", "--render", "root", "--check"] + D, dict(exit=2, err="separate runs")),
 ("u08", NONE, ["01-a", "--bogus"] + D, dict(exit=2, err="unknown option")),
 # the repository and the root plan
 ("g01", NONE, "norepo", dict(exit=1, rep=rep(result="error", problem="the working directory is not inside a git repository",
     fix="run it from the repository"))),
 ("g02", BOTH, ["01-a"] + D, dict(exit=1, rep=rep(result="error",
     problem="both docs/plan/DO.md and docs/plan/TODO.md exist, so which one is the root plan is ambiguous"), any=["fix"])),
 ("g03", NONE, ["01-a"] + D, dict(exit=1, rep=rep(result="error",
     problem="there is no root plan, docs/plan/DO.md or docs/plan/TODO.md, so there is no revision to close"), any=["fix"])),
 # a revisions index: the stamp
 ("s01", IX, ["08-new"] + D, dict(exit=0, rep=dict(STAMP, result="proposed", change="stamp", edits=EDITS8))),
 ("s02", IX, ["07-rev"] + D, dict(exit=1, rep=dict(STAMP, result="refused", revision="docs/plan/07-rev/_TODO.md",
     problem="docs/plan/TODO.md lists no revision 07-rev", fix="check the label against the `## Revisions` lines"))),
 ("s03", IX, ["05-old"] + D, dict(exit=1, rep=rep(result="refused", problem="revision 05-old is already closed: docs/plan/TODO.md:7 marks it [x]",
     fix="nothing to do"), any=["layout", "root", "revision"])),
 ("s04", IX, ["06-dropped"] + D, dict(exit=1, rep=rep(result="refused", problem="revision 06-dropped is not open: docs/plan/TODO.md:8 marks it [-]"),
     any=["layout", "root", "revision", "fix"])),
 ("s05", dict(IX, **{"docs/plan/08-new/_TODO.md": "# Revision 08-new\n\n- [x] 1. a\n"}), ["08-new"] + D, dict(exit=1, rep=rep(result="error",
     problem="docs/plan/08-new/_TODO.md has no **Status** line, so it cannot be stamped closed"), any=["layout", "root", "revision", "fix"])),
 ("s06", dict(IX, **{"docs/plan/08-new/_TODO.md": REV8.replace("open", "closed — 2026-10-01", 1)}), ["08-new"] + D, dict(exit=1, rep=rep(result="refused",
     problem="docs/plan/08-new/_TODO.md:3 is already stamped `closed — 2026-10-01`, but docs/plan/TODO.md:10 marks the revision open",
     fix="mark docs/plan/TODO.md:10 [x]: the revision has closed"), any=["layout", "root", "revision"])),
 ("s07", dict(IX, **{"docs/plan/08-new/_TODO.md": REV8.replace("open", "paused", 1)}), ["08-new"] + D, dict(exit=1, rep=rep(result="refused",
     problem="docs/plan/08-new/_TODO.md:3 reads `**Status**: paused`, not `open`"), any=["layout", "root", "revision", "fix"])),
 ("s08", IX, ["07-rev-2"] + D, dict(exit=1, rep=rep(result="refused",
     problem="revision 07-rev-2 still has 2 unfinished item(s):\ndocs/plan/07-rev-2/_TODO.md:8   - [ ] nested open\ndocs/plan/07-rev-2/_TODO.md:9 - [!] 2. b",
     fix=UNFIN), any=["layout", "root", "revision"])),
 ("s09", IX, ["09-fenced"] + D, dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md lists no revision 09-fenced"),
     any=["layout", "root", "revision", "fix"])),
 ("s10", dict(IX, **{"docs/plan/08-new/feat-y/TODO.md": ACTIVE}), ["08-new"] + D, dict(exit=0, rep=dict(STAMP, result="proposed",
     change="stamp", edits=EDITS8, warnings="docs/plan/08-new/feat-y/TODO.md is stamped `active`: its branch may not have merged"))),
 ("s11", IX, ["08-new", "--render", "root"] + D, dict(exit=2, err="--render is for a legacy root plan")),
 ("s12", crlf(IX), ["08-new"] + D, dict(exit=0, rep=dict(STAMP, result="proposed", change="stamp", edits=EDITS8))),
 ("s13", {k: v for k, v in IX.items() if k != "docs/plan/08-new/_TODO.md"}, ["08-new"] + D, dict(exit=1, rep=rep(result="error",
     problem="revision 08-new is open at docs/plan/TODO.md:10, but docs/plan/08-new/_TODO.md is missing"), any=["layout", "root", "revision", "fix"])),
 # an index line with no note closes as `<label> — closed. See …`
 ("s14", dict(IX, **{"docs/plan/TODO.md": INDEX.replace("- [~] 08-new — the next one", "- [~] 08-new")}), ["08-new"] + D, dict(exit=0,
     rep=dict(STAMP, result="proposed", change="stamp",
     edits=f"docs/plan/08-new/_TODO.md:3: {ST8}\ndocs/plan/TODO.md:10: - [x] 08-new — closed. See `docs/plan/08-new/_TODO.md`."))),
 # a legacy root plan: the cut, the pointer and the moves
 ("x01", LG, ["08-c"] + D, dict(exit=0, rep=dict(LEGOUT, result="proposed"))),
 ("x02", LG, ["08-c", "--render", "archive"] + D, dict(exit=0, out=ARCHIVE)),
 ("x03", LG, ["08-c", "--render", "root"] + D, dict(exit=0, out=ROOT_AFTER)),
 ("x04", {"docs/plan/TODO.md": NOCLOSED_DEF}, ["01-a", "--render", "root"] + D, dict(exit=0, out=NOCLOSED_DEF_AFTER)),
 ("x05", {"docs/plan/TODO.md": NOCLOSED_END}, ["01-a", "--render", "root"] + D, dict(exit=0, out=NOCLOSED_END_AFTER)),
 ("x06", {"docs/plan/TODO.md": CLOSED_PROSE}, ["01-a", "--render", "root"] + D, dict(exit=0, out=CLOSED_PROSE_AFTER)),
 ("x07", {"docs/plan/TODO.md": CLOSED_EMPTY}, ["01-a", "--render", "root"] + D, dict(exit=0, out=CLOSED_EMPTY_AFTER)),
 ("x08", LG, ["08"] + D, dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md has no `## Subgoals — revision 08` section",
     fix="check the label; a bare `## Subgoals` heading carries none, and cannot be closed"), any=["layout", "root", "revision"])),
 ("x09", LG, ["05-old"] + D, dict(exit=1, rep=rep(result="refused", problem="revision 05-old is already closed: docs/plan/TODO.md:32 is its pointer",
     fix="nothing to do"), any=["layout", "root", "revision"])),
 ("x10", {"docs/plan/TODO.md": OPENSEC}, ["01-a"] + D, dict(exit=1, rep=rep(result="refused",
     problem="revision 01-a still has 2 unfinished item(s):\ndocs/plan/TODO.md:6   - [ ] nested open\ndocs/plan/TODO.md:7 - [!] b", fix=UNFIN),
     any=["layout", "root", "revision"])),
 ("x11", LG_DEST, ["08-c"] + D, dict(exit=1, rep=rep(result="refused", problem="docs/plan/08-c/_TODO.md already exists, so revision 08-c looks closed already"),
     any=["layout", "root", "revision", "fix"])),
 ("x12", LG_COPY, ["08-c"] + D, dict(exit=1, rep=rep(result="error", problem="both docs/plan/feat-one and docs/plan/08-c/feat-one exist, so one is a copy"),
     any=["layout", "root", "revision", "fix", "warnings"])),
 ("x13", LG, ["07-rev"] + D, dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md has no `## Subgoals — revision 07-rev` section"),
     any=["layout", "root", "revision", "fix"])),
 ("x14", crlf(LG), ["08-c", "--render", "archive"] + D, dict(exit=0, out=ARCHIVE)),
 ("x15", {"docs/plan/TODO.md": BSL}, ["a\\tb"] + D, dict(exit=0, rep=rep(result="proposed", layout="legacy", root="docs/plan/TODO.md",
     revision="docs/plan/a\\tb/_TODO.md", change="extract", section="docs/plan/TODO.md:3-5",
     pointer="- **Revision a\\tb** — closed. See `docs/plan/a\\tb/_TODO.md`."))),
 ("x16", LG, ["07-rev-2"] + D, dict(exit=1, rep=rep(result="refused", problem="revision 07-rev-2 still has 1 unfinished item(s):\ndocs/plan/TODO.md:7 - [ ] other open",
     fix=UNFIN), any=["layout", "root", "revision"])),
 ("x17", crlf(LG), ["08-c", "--render", "root"] + D, dict(exit=0, out=ROOT_AFTER)),
 ("x18", LG, ["08-c", "--render", "root", "--date", "2026-12-31"], dict(exit=0, out=ROOT_AFTER)),
 ("x19", {"docs/plan/DO.md": NOCLOSED_END}, ["01-a"] + D, dict(exit=0, rep=rep(result="proposed", layout="legacy", root="docs/plan/DO.md",
     revision="docs/plan/01-a/_DO.md", change="extract", section="docs/plan/DO.md:5-7",
     pointer="- **Revision 01-a** — closed. See `docs/plan/01-a/_DO.md`."))),
 # The command runs each move as printed: a backlink holding shell syntax, with a merged plan
 # directory of that name, is an error, and no move is printed for it.
 ("x20", {"docs/plan/TODO.md": "# M\n\n## Subgoals — revision 01-a\n\n- [x] a\n  > **Branch:** feat/a$(touch${IFS}PWNED)\n\n## Closed revisions\n",
          "docs/plan/feat-a$(touch${IFS}PWNED)/TODO.md": MERGED}, ["01-a"] + D, dict(exit=1, rep=rep(result="error",
     problem="the backlink `feat/a$(touch${IFS}PWNED)` names a plan directory that is not a plain name, so no move is printed for it",
     fix="check the backlink; move the directory by hand if it is genuine (your call)"), any=["layout", "root", "revision"])),
 # the archive drops the section's trailing blank and whitespace-only lines, and keeps those inside it
 ("x21", {"docs/plan/TODO.md": "# M\n\n## Subgoals — revision 01-a\n\nPreamble.\n\n- [x] a\n\n \n\t\n\n## Closed revisions\n"},
     ["01-a", "--render", "archive"] + D, dict(exit=0, out="## Subgoals — revision 01-a\n\nPreamble.\n\n- [x] a\n")),
 # tool failures: every awk, then only the matcher named by the label it is passed
 ("t01", LG, "awk127", dict(exit=3, err="awk failed")),
 ("t02", LG, "awk-section", dict(exit=3, err="awk failed reading /dev/stdin")),
 ("t03", LG, "awk-pointer", dict(exit=3, err="awk failed reading /dev/stdin")),
 # die's hints when a writer dies of SIGPIPE: the writer's own status (141), then the reader's
 # pipeline, which fails with die's (3); neither blames PATH or a tool
 ("t04", IX, "cat141", dict(exit=3, err="cat failed reading docs/plan/TODO.md\nhint: status 141 is SIGPIPE")),
 ("t05", IX, "cat141", dict(exit=3, err="awk failed reading the revisions of docs/plan/TODO.md\nhint: status 3 is close-revision.sh's own failure status")),
 # --check
 ("k01", IX, ["08-new", "--check"] + D, dict(exit=0, rep=dict(STAMP, result="verified", change="stamp", edits=EDITS8)), stamp_ok),
 ("k02", IX, ["08-new", "--check"] + D, dict(exit=1, rep=dict(STAMP, result="error",
     problem=f"docs/plan/08-new/_TODO.md does not read as stamped: line 3 should be `{ST8}`, and nothing else should change",
     fix="edit line 3 to that, and undo any other change")), stamp_extra),
 ("k03", crlf(IX), ["08-new", "--check"] + D, dict(exit=0, rep=dict(STAMP, result="verified", change="stamp", edits=EDITS8)), stamp_crlf),
 ("k04", LG, ["08-c", "--check"] + D, dict(exit=0, rep=dict(LEGOUT, result="verified")), extract_ok),
 ("k05", LG, ["08-c", "--check"] + D, dict(exit=1, rep=dict(LEG, result="error", warnings="\n".join(LG_WARN),
     problem="docs/plan/08-c/_TODO.md is not the section, verbatim",
     fix="write it again from `close-revision.sh 08-c --date 2026-10-11 --render archive`, run before the cut")), extract_word),
 ("k06", LG, ["08-c", "--check"] + D, dict(exit=1, rep=dict(LEG, result="error", warnings="\n".join(LG_WARN),
     problem="docs/plan/feat-one has not been moved into docs/plan/08-c/", fix=f"run: {LG_MOVE}")), extract_nomove),
 ("k07", LG, ["08-c", "--check"] + D, dict(exit=1, rep=dict(LEG, result="error", warnings="\n".join(LG_WARN),
     problem="docs/plan/TODO.md is not the root plan with the section cut and the pointer added"), any=["fix"]), extract_nocut),
 ("k10", LG, ["08-c", "--check"] + D, dict(exit=1, rep=dict(LEG, result="error", warnings="\n".join(LG_WARN),
     problem="docs/plan/08-c/_TODO.md is not the section, verbatim",
     fix="write it again from `close-revision.sh 08-c --date 2026-10-11 --render archive`, run before the cut")), extract_blank),
 ("k08", IX_DONE, ["08-new", "--check"] + D, dict(exit=1, rep=dict(STAMP, result="error",
     problem="docs/plan/TODO.md:10 at HEAD marks revision 08-new [x], not [~]", fix=BEFORE))),
 ("k09", LG_DONE, ["08-c", "--check"] + D, dict(exit=1, rep=dict(LEG, result="error",
     problem="docs/plan/TODO.md at HEAD has no section for revision 08-c", fix=BEFORE))),
 # the stamp's old form, the note alone, no longer verifies
 ("k11", IX, ["08-new", "--check"] + D, dict(exit=1, rep=dict(STAMP, result="error",
     problem=f"docs/plan/TODO.md does not read as stamped: line 10 should be `{IDX8}`, and nothing else should change",
     fix="edit line 10 to that, and undo any other change")), stamp_old),
 # large inputs (BIG): LGB reaches section_line, status_src (feat-one) and the directory search
 # (feat-gone), and with 05-old pointer_line; IXB reaches the stamp's index line and the
 # revision's status, and under --check the **Layout** read
 ("b01", LGB, ["08-c"] + D, dict(exit=0, rep=dict(LGBOUT, result="proposed"))),
 ("b02", LGB, ["08-c", "--check"] + D, dict(exit=0, rep=dict(LGBOUT, result="verified")), extract_big),
 ("b03", LGB, ["05-old"] + D, dict(exit=1, rep=rep(result="refused", problem="revision 05-old is already closed: docs/plan/TODO.md:32 is its pointer",
     fix="nothing to do"), any=["layout", "root", "revision"])),
 ("b04", IXB, ["08-new"] + D, dict(exit=0, rep=dict(STAMP, result="proposed", change="stamp", edits=EDITS8))),
 ("b05", IXB, ["08-new", "--check"] + D, dict(exit=0, rep=dict(STAMP, result="verified", change="stamp", edits=EDITS8)), stamp_big),
]

def sh(args, cwd, env=None):
    # Decoded here rather than with text=True, which turns \r\n into \n and would hide a
    # render that kept a CRLF plan's carriage returns.
    r = subprocess.run(args, cwd=cwd, capture_output=True, env=env)
    return subprocess.CompletedProcess(r.args, r.returncode, r.stdout.decode(), r.stderr.decode())
def git(*a, cwd=FX):
    r = sh(["git", *a], cwd)
    if r.returncode: sys.exit(f"git {' '.join(a)} failed: {r.stderr}")
    return r.stdout

def build():
    shutil.rmtree(FX, ignore_errors=True); os.makedirs(FX)
    git("init", "-q", "-b", "main"); git("config", "user.email", "suite@example.invalid"); git("config", "user.name", "suite")
    git("config", "commit.gpgsign", "false")
    open(FX + "/README.md", "w").write("fixture\n"); git("add", "-A"); git("commit", "-q", "-m", "root")
    for c in C:
        cid, files = c[0], c[1]
        git("checkout", "-q", "--orphan", f"case/{cid}"); git("rm", "-rq", "--cached", ".")
        for f in os.listdir(FX):
            if f != ".git": os.remove(FX + "/" + f) if os.path.isfile(FX + "/" + f) else shutil.rmtree(FX + "/" + f)
        for rel, text in files.items():
            p = f"{FX}/{rel}"; os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", newline="").write(text)
        git("add", "-A"); git("commit", "-q", "-m", cid)
    git("checkout", "-q", "main")
    os.makedirs(AWK127, exist_ok=True)
    open(AWK127 + "/awk", "w").write("#!/bin/sh\nexit 127\n"); os.chmod(AWK127 + "/awk", 0o755)
    os.makedirs(CAT141, exist_ok=True)
    open(CAT141 + "/cat", "w").write("#!/bin/sh\nkill -PIPE $$\nexit 141\n"); os.chmod(CAT141 + "/cat", 0o755)
    real = shutil.which("awk") or sys.exit("no awk on PATH")
    for d, prefix in AWKSEL.values():
        os.makedirs(d, exist_ok=True)
        open(d + "/awk", "w").write(f'#!/bin/sh\ncase "$L" in "{prefix}"*) exit 2 ;; esac\nexec {real} "$@"\n')
        os.chmod(d + "/awk", 0o755)
    shutil.rmtree(NOREPO, ignore_errors=True); os.makedirs(NOREPO)

def reset():
    git("reset", "-q", "--hard"); git("clean", "-fdq")

def run(cid, args, shell, script, apply):
    env = dict(os.environ); cwd = FX; git("checkout", "-q", f"case/{cid}")
    env["GIT_CEILING_DIRECTORIES"] = W
    if apply: apply()
    if args == "awk127": env["PATH"] = AWK127 + ":" + env["PATH"]; args = ["01-new"] + D
    if args == "cat141": env["PATH"] = CAT141 + ":" + env["PATH"]; args = ["08-new"] + D
    if isinstance(args, str) and args in AWKSEL:
        env["PATH"] = AWKSEL[args][0] + ":" + env["PATH"]
        args = (["08-c"] if args == "awk-section" else ["99-none"]) + D
    if args == "norepo": cwd = NOREPO; args = ["01-a"] + D
    before = git("status", "--porcelain")
    r = sh([shell, script, *args], cwd, env)
    changed = git("status", "--porcelain") != before
    if apply: reset()
    return r, changed

def parse(text):
    """The report as (keys in order, values): a continuation line, indented two spaces, joins its key's value."""
    keys, vals = [], {}
    for line in text.splitlines():
        if line.startswith("  ") and keys: vals[keys[-1]] += "\n" + line[2:]; continue
        k, sep, v = line.partition(": ")
        if not sep: return None, None
        keys.append(k); vals[k] = v
    return keys, vals

def grade_report(exp, text, where):
    probs = []
    keys, vals = parse(text)
    if keys != KEYS or vals is None: return [f"{where} is not the twelve-key report: {text[:160]!r}"]
    for k in KEYS:
        if k in exp["rep"]:
            if vals[k] != exp["rep"][k]: probs.append(f"{k}: {vals[k]!r}, want {exp['rep'][k]!r}")
        elif k not in exp.get("any", []) and vals[k] != "—":
            probs.append(f"{k}: {vals[k]!r}, want —")
    return probs

def grade(exp, r):
    probs = []
    if r.returncode != exp["exit"]: probs.append(f"exit {r.returncode}, want {exp['exit']} (stderr: {r.stderr.strip()[:100]!r})")
    if "err" in exp:
        if exp["err"] not in r.stderr: probs.append(f"stderr lacks {exp['err']!r}: {r.stderr.strip()[:140]!r}")
        if r.stdout: probs.append(f"a usage error or tool failure printed to stdout: {r.stdout[:80]!r}")
    if "rep" in exp:
        probs += grade_report(exp, r.stdout, "stdout")
        if r.stderr: probs.append(f"a report run wrote to stderr: {r.stderr.strip()[:100]!r}")
    if "out" in exp:
        if r.stdout != exp["out"]: probs.append(f"stdout differs from the expected render: {r.stdout[:300]!r}")
        if r.stderr: probs.append(f"a render wrote to stderr: {r.stderr.strip()[:100]!r}")
    # A tool failure prints no report, and its PATH hint names the binary by absolute path.
    if exp["exit"] != 3 and W in r.stdout + r.stderr: probs.append("an absolute path in the output")
    return probs

def mutants():
    d = HERE + "/mutants"; tmp = W + "/crv-mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; root = f"{tmp}/{name}"; out = root + "/close-revision.sh"
        os.makedirs(root + "/lib"); shutil.copy2(SCRIPT, out); shutil.copy2(LIB, root + "/lib/plan-rules.sh")
        ap = sh(["patch", "-s", "-F0", "-p1", "-d", root, "-i", f"{d}/{fn}"], tmp)
        if ap.returncode:
            bad += 1; print(f"STALE  {name}: the patch no longer applies ({(ap.stdout + ap.stderr).strip()[:120]})"); continue
        r = sh([sys.executable, "-I", os.path.abspath(__file__), "--once", "--script", out], HERE)
        killed = r.returncode != 0
        why = next((l for l in r.stdout.splitlines() if l.startswith("FAIL")), "")
        print(f"{'KILLED' if killed else 'SURVIVED'} {name}" + (f"  ({why[:100]})" if killed else ""))
        bad += not killed
    shutil.rmtree(tmp); print(f"\n{bad} failing"); sys.exit(1 if bad else 0)

def main():
    if "--mutants" in sys.argv: mutants()
    want = [a for a in sys.argv[1:] if re.match(r"^[a-z]\d\d$", a)]
    build()
    heads = git("for-each-ref", "--format=%(refname) %(objectname)")
    fails = 0
    for c in C:
        cid, _, args, exp = c[:4]; apply = c[4] if len(c) > 4 else None
        if want and cid not in want: continue
        outs, probs = set(), []
        for shell in SHELLS:
            for _ in range(1 if "--once" in sys.argv else 2):
                r, changed = run(cid, args, shell, SCRIPT, apply); outs.add((r.returncode, r.stdout, r.stderr))
                probs += [p for p in grade(exp, r) if p not in probs]
                if changed or git("status", "--porcelain") or git("for-each-ref", "--format=%(refname) %(objectname)") != heads:
                    if "the fixture changed" not in probs: probs.append("the fixture changed")
        if len(outs) > 1: probs.append("output differs between runs or shells")
        print(f"{'PASS' if not probs else 'FAIL'} {cid:<4} " + "; ".join(probs))
        if "-v" in sys.argv: print("".join(o[1] + o[2] for o in sorted(outs)))
        fails += bool(probs)
    git("checkout", "-q", "main")
    print(f"\n{fails} failing"); sys.exit(1 if fails else 0)

main()
