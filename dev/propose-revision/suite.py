"""propose-revision.sh suite: runs the script directly on a fixture repository built here, one
orphan branch per case (the script reads the repository's own root plan), and grades the exit
code, the report key by key, and a rendered root plan byte for byte. Writes only under
$LOCATE_PLAN_WORK, which must lie outside the repository (the rule dev/locate-plan/ uses, for
the same reasons).

  LOCATE_PLAN_WORK=<dir> python3 -I suite.py [-v] [--once] [--script PATH] [ids...]
  LOCATE_PLAN_WORK=<dir> python3 -I suite.py --mutants

Every case runs twice under each shell found and must print the same thing each time, and
must leave the fixture untouched. A report is always the ten keys of propose-revision-spec.md,
in order, with no absolute path. --mutants applies each patch in mutants/ to a copy of the
script and its library and runs the suite on it once; each must fail it. A patch names the
file it changes relative to scripts/: propose-revision.sh, or lib/plan-rules.sh."""
import hashlib, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCRIPT = REPO + "/plugins/workflow-coding/scripts/propose-revision.sh"
if "--script" in sys.argv:
    SCRIPT = os.path.abspath(sys.argv[sys.argv.index("--script") + 1])
LIB = os.path.dirname(SCRIPT) + "/lib/plan-rules.sh"   # sourced by the script, from beside it
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
FX = W + "/prv"
SHELLS = [s for s in ("/bin/bash", "/opt/homebrew/bin/bash") if os.access(s, os.X_OK)]
if "--once" in sys.argv: SHELLS = SHELLS[:1]
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
AWK127 = f"{W}/bin/{h('prv-awk-127')}"
AWKSEL = {"awk-section": (f"{W}/bin/{h('prv-awk-section')}", "## Subgoals"),
          "awk-pointer": (f"{W}/bin/{h('prv-awk-pointer')}", "- **Revision")}
DRY = f"{W}/dry-{h('prv-dry')}"           # outside the repository; created per case as needed
LINK = f"{W}/link-{h('prv-link')}"        # a symlink into the fixture's docs/plan/
NOREPO = f"{W}/norepo-{h('prv-norepo')}"  # a directory in no repository

KEYS = ["result", "layout", "root", "revision", "previous", "change", "open", "warnings", "problem", "fix"]
TAKEN = "choose another label: a revision is never reopened, and a new one can say what it follows on from"

# --- fixtures. Line numbers matter: the cases name them. ---

# Ported from dev/open-revision/: a legacy plan with two open sections, a paragraph quoting the
# old closed form, and closed pointers in the forms close-revision.sh writes, one subtitled.
OPEN_LEGACY = """# Master plan

**Status**: active

## Subgoals — revision 07-rev-2

- [ ] a

## Subgoals — revision 08-c: A subtitled heading

- [ ] b

A paragraph that quotes the old form: - **Revision 09-p** — closed.

## Closed revisions

- **Revision 02-mcp-github-access** — closed. See `docs/plan/workflow-claude/02-mcp-github-access/_DO.md`.
- **Revision 04-sub** — plan layout at scale — closed. See `docs/plan/old/04-sub/_TODO.md`.
- **Revision 05-x-2** — closed. See `docs/plan/old/05-x-2/_TODO.md`.
- **Revision 06-here** — closed. See `docs/plan/06-here/_TODO.md`.
"""
OL = {"docs/plan/TODO.md": OPEN_LEGACY, "docs/plan/06-here/_TODO.md": "# Revision 06-here\n",
      "docs/plan/07-dir/x/TODO.md": "# x\n"}

# A legacy plan with nothing open: the state pfsmgraph is in, and this repository after R1.
CLOSED_LEGACY = """# Master plan

**Status**: active

Prose about the plan, kept as it is.

```markdown
## Subgoals — revision 99-example
- **Revision 98-fenced** — closed. See `x`.
```

## Closed revisions

Extracted by `/close-revision` once finished.

- **Revision 02-a** — closed. See `docs/plan/old/02-a/_TODO.md`.
- **Revision 03-b** — a subtitle — closed. See `docs/plan/03-b/_TODO.md`.
- **Revision 04-c** — closed. See `docs/plan/04-c/_TODO.md`.

## Deferred

Nothing.
"""
CLOSED_LEGACY_AFTER = """# Master plan

**Status**: active
**Layout**: revisions

Prose about the plan, kept as it is.

```markdown
## Subgoals — revision 99-example
- **Revision 98-fenced** — closed. See `x`.
```

## Revisions

Extracted by `/close-revision` once finished.

- [x] 02-a — closed. See `docs/plan/old/02-a/_TODO.md`.
- [x] 03-b — a subtitle — closed. See `docs/plan/03-b/_TODO.md`.
- [x] 04-c — closed. See `docs/plan/04-c/_TODO.md`.
- [~] 05-new — the next one

## Deferred

Nothing.
"""
CL = {"docs/plan/TODO.md": CLOSED_LEGACY, "docs/plan/03-b/_TODO.md": "# Revision 03-b\n",
      "docs/plan/04-c/_TODO.md": "# Revision 04-c\n"}
CL_NOPREV = {"docs/plan/TODO.md": CLOSED_LEGACY, "docs/plan/03-b/_TODO.md": "# Revision 03-b\n"}

# Prose a legacy close left is carried over, and warns a paragraph at a time: a sentence
# still true, one wrapped across lines, a fenced copy, and a pointer.
PROSE = """# Master plan

**Status**: active

Run `/close-revision` once a revision is finished; it removes nothing.

A finished revision is closed
by `/close-revision`, which then
moves it into `docs/plan/<label>/`.

```markdown
`/close-revision` moves a revision.
```

## Closed revisions

- **Revision 01-a** — closed. See `docs/plan/01-a/_TODO.md`.
"""
def legacy_prose(n): return f"docs/plan/TODO.md:{n} describes the legacy close, which extracts or moves a revision; under a revisions index /close-revision only stamps, so reword it once converted"

NOSTATUS = "# Master plan\n\nProse.\n\n## Closed revisions\n\n- **Revision 01-a** — closed.\n"
NOSTATUS_AFTER = "# Master plan\n\n**Layout**: revisions\n\nProse.\n\n## Revisions\n\n- [x] 01-a — closed.\n- [~] 02-b — next\n"
LAYOUT_LEGACY = "# Master plan\n\n**Status**: active\n**Layout**: legacy\n\n## Closed revisions\n\n- **Revision 01-a**\n"
LAYOUT_LEGACY_AFTER = "# Master plan\n\n**Status**: active\n**Layout**: revisions\n\n## Revisions\n\n- [x] 01-a\n- [~] 02-b — next\n"
NOCLOSED = "# Master plan\n\n**Status**: active\n\nNothing has closed yet.\n"
NOCLOSED_AFTER = "# Master plan\n\n**Status**: active\n**Layout**: revisions\n\nNothing has closed yet.\n\n## Revisions\n\n- [~] 01-a — first\n"
EMPTYCLOSED = "# Master plan\n\n**Status**: active\n\n## Closed revisions\n\nNone yet.\n"
EMPTYCLOSED_AFTER = "# Master plan\n\n**Status**: active\n**Layout**: revisions\n\n## Revisions\n\n- [~] 01-a — first\n\nNone yet.\n"
# Only pointers under `## Closed revisions` convert; one quoted in a later section stays.
LATER = "# Master plan\n\n## Closed revisions\n\n- **Revision 01-a** — closed.\n\n## Notes\n\n- **Revision 07-z** — quoted in a note.\n"
LATER_AFTER = "# Master plan\n\n**Layout**: revisions\n\n## Revisions\n\n- [x] 01-a — closed.\n- [~] 02-b — next\n\n## Notes\n\n- **Revision 07-z** — quoted in a note.\n"
BADPTR_STARS ="# Master plan\n\n## Closed revisions\n\n- **Revision 01-a — closed.\n"
BADPTR_REST = "# Master plan\n\n## Closed revisions\n\n- **Revision 01-a**: closed.\n"
BADPTR_SPACE = "# Master plan\n\n## Closed revisions\n\n- **Revision 01 a** — closed.\n"

# A revisions index: an open revision, a closed one, a descoped one, and a fenced example line.
INDEX = """# Master plan

**Layout**: revisions

## Revisions

- [x] 05-old — closed
- [-] 06-dropped
- [~] 07-rev-2 — in flight

```markdown
- [~] 09-fenced — an example
```

## Notes

Prose.
"""
INDEX_AFTER = INDEX.replace("- [~] 07-rev-2 — in flight\n", "- [~] 07-rev-2 — in flight\n- [~] 08-new — the next one\n")
IX = {"docs/plan/TODO.md": INDEX, "docs/plan/07-rev-2/_TODO.md": "# Revision 07-rev-2\n\n**Status**: open\n",
      "docs/plan/05-old/_TODO.md": "# Revision 05-old\n"}
IX_DIR = dict(IX, **{"docs/plan/08-new/keep.md": "x\n"})
IX_BROKEN = {"docs/plan/TODO.md": INDEX}   # 07-rev-2 is open but has no _TODO.md
EMPTYINDEX = "# Master plan\n\n**Layout**: revisions\n\n## Revisions\n\nNone yet.\n"
EMPTYINDEX_AFTER = "# Master plan\n\n**Layout**: revisions\n\n## Revisions\n\n- [~] 01-a — first\n\nNone yet.\n"

NONE = {"README.md": "x\n"}
NONE_AFTER = "# Master plan\n\n**Layout**: revisions\n\n## Revisions\n\n- [~] 01-a — first\n"
BOTH = {"docs/plan/TODO.md": "# a\n", "docs/plan/DO.md": "# b\n"}

def crlf(files): return {k: v.replace("\n", "\r\n") for k, v in files.items()}
BSL = {"docs/plan/TODO.md": "# Master plan\n\n## Subgoals — revision a\\tb\n\n- [ ] a\n"}

def rep(**kv): return kv
# id, files on the case's branch, arguments (or a special), expectations. A report case gives
# the keys it checks (every other key must be "—" unless `any` names it); a render case gives
# the exact stdout; a usage or tool failure gives exit and an stderr fragment.
C = [
 # usage
 ("u01", NONE, [], dict(exit=2, err="no label given")),
 ("u02", NONE, ["01-a", "02-b"], dict(exit=2, err="one label only")),
 ("u03", NONE, ["feat/x"], dict(exit=2, err="holds no whitespace")),
 ("u04", NONE, ["a b"], dict(exit=2, err="holds no whitespace")),
 ("u05", NONE, ["a—b"], dict(exit=2, err="holds no whitespace")),
 ("u06", NONE, ["--", "-a"], dict(exit=2, err="does not start with")),
 ("u07", NONE, ["01-a", "--model", "X.md"], dict(exit=2, err="--model takes")),
 ("u08", NONE, ["01-a", "--dry-run", "x", "--render", "n"], dict(exit=2, err="separate runs")),
 ("u09", NONE, ["01-a", "--render", ""], dict(exit=2, err="the note is empty")),
 ("u10", NONE, ["01-a", "--render", "a\tb"], dict(exit=2, err="one line")),
 ("u11", NONE, ["01-a", "--dry-run", "a/../b"], dict(exit=2, err="without . or ..")),
 ("u12", NONE, ["01-a", "--bogus"], dict(exit=2, err="unknown option")),
 # no root plan
 ("n01", NONE, ["01-a"], dict(exit=0, rep=rep(result="proposed", layout="none", root="docs/plan/DO.md",
     revision="docs/plan/01-a/_DO.md", change="create"))),
 ("n02", NONE, ["01-a", "--model", "TODO.md"], dict(exit=0, rep=rep(result="proposed", layout="none",
     root="docs/plan/TODO.md", revision="docs/plan/01-a/_TODO.md", change="create"))),
 ("n03", dict(NONE, **{"docs/plan/01-a/x.md": "x\n"}), ["01-a"], dict(exit=1, rep=rep(result="refused", layout="none",
     root="docs/plan/DO.md", revision="docs/plan/01-a/_DO.md",
     problem="docs/plan/01-a already exists, so revision 01-a has been opened before", fix=TAKEN))),
 ("n04", NONE, ["01-a", "--model", "TODO.md", "--render", "first"], dict(exit=0, out=NONE_AFTER)),
 # legacy, with sections open: ported from dev/open-revision/ (o01-o11, o15)
 ("l01", OL, ["02-mcp-github-access"], dict(exit=1, rep=rep(result="refused", layout="legacy", root="docs/plan/TODO.md",
     revision="docs/plan/02-mcp-github-access/_TODO.md",
     problem="docs/plan/TODO.md:17 lists revision 02-mcp-github-access as closed", fix=TAKEN))),
 ("l02", OL, ["04-sub"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:18 lists revision 04-sub as closed"), any=["layout", "root", "revision", "fix"])),
 ("l03", OL, ["05-x"], dict(exit=1, rep=rep(result="refused",
     problem="docs/plan/TODO.md:5 has a section still open, `## Subgoals — revision 07-rev-2`, which a revisions index has no place for",
     fix="close that revision first (/close-revision), or convert the root plan to a revisions index by hand"), any=["layout", "root", "revision"])),
 ("l04", OL, ["07-rev"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:5 has a section still open"), prefix=["problem"], any=["layout", "root", "revision", "fix"])),
 ("l05", OL, ["07-rev-2"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:5 already has a section for revision 07-rev-2"), any=["layout", "root", "revision", "fix"])),
 ("l06", OL, ["08-c"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:9 already has a section for revision 08-c"), any=["layout", "root", "revision", "fix"])),
 ("l07", OL, ["07-dir"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/07-dir already exists, so revision 07-dir has been opened before"), any=["layout", "root", "revision", "fix"])),
 ("l08", OL, ["06-here"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:20 lists revision 06-here as closed"), any=["layout", "root", "revision", "fix"])),
 ("l09", OL, ["09-p"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:5 has a section still open"), prefix=["problem"], any=["layout", "root", "revision", "fix"])),
 ("l10", crlf(OL), ["07-rev-2"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:5 already has a section for revision 07-rev-2"), any=["layout", "root", "revision", "fix"])),
 ("l11", BSL, ["a\\tb"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:3 already has a section for revision a\\tb"), any=["layout", "root", "revision", "fix"])),
 ("l12", OL, "awk127", dict(exit=3, err="awk failed")),
 # An awk that fails only for one matcher, found by the label it is passed in ENVIRON["L"]:
 # every earlier awk works, so the failure is the matcher's own.
 ("l14", OL, "awk-section", dict(exit=3, err="awk failed reading docs/plan/TODO.md")),
 ("l15", OL, "awk-pointer", dict(exit=3, err="awk failed reading docs/plan/TODO.md")),
 ("l13", crlf(OL), ["06-here"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:20 lists revision 06-here as closed"), any=["layout", "root", "revision", "fix"])),
 # legacy, nothing open: the conversion
 ("c01", CL, ["05-new"], dict(exit=0, rep=rep(result="proposed", layout="legacy", root="docs/plan/TODO.md",
     revision="docs/plan/05-new/_TODO.md", previous="docs/plan/04-c/_TODO.md", change="convert", warnings=legacy_prose(14)))),
 ("c02", CL, ["05-new", "--render", "the next one"], dict(exit=0, out=CLOSED_LEGACY_AFTER)),
 ("c03", {"docs/plan/TODO.md": NOSTATUS}, ["02-b", "--render", "next"], dict(exit=0, out=NOSTATUS_AFTER)),
 ("c04", {"docs/plan/TODO.md": LAYOUT_LEGACY}, ["02-b", "--render", "next"], dict(exit=0, out=LAYOUT_LEGACY_AFTER)),
 ("c05", {"docs/plan/TODO.md": NOCLOSED}, ["01-a", "--render", "first"], dict(exit=0, out=NOCLOSED_AFTER)),
 ("c06", {"docs/plan/TODO.md": EMPTYCLOSED}, ["01-a", "--render", "first"], dict(exit=0, out=EMPTYCLOSED_AFTER)),
 ("c07", {"docs/plan/TODO.md": BADPTR_STARS}, ["02-b"], dict(exit=1, rep=rep(result="error",
     problem="docs/plan/TODO.md:5 is a closed pointer that would not convert to an index line: `- **Revision 01-a — closed.`"),
     any=["layout", "root", "revision", "fix"])),
 ("c08", {"docs/plan/TODO.md": BADPTR_REST}, ["02-b"], dict(exit=1, rep=rep(result="error",
     problem="docs/plan/TODO.md:5 is a closed pointer that would not convert"), prefix=["problem"], any=["layout", "root", "revision", "fix"])),
 ("c09", {"docs/plan/TODO.md": BADPTR_SPACE}, ["02-b"], dict(exit=1, rep=rep(result="error",
     problem="docs/plan/TODO.md:5 is a closed pointer that would not convert"), prefix=["problem"], any=["layout", "root", "revision", "fix"])),
 ("c10", crlf(CL), ["05-new", "--render", "the next one"], dict(exit=0, out=CLOSED_LEGACY_AFTER)),
 ("c11", CL_NOPREV, ["05-new"], dict(exit=0, rep=rep(result="proposed", previous="—", change="convert", warnings=legacy_prose(14)), any=["layout", "root", "revision"])),
 # The refusals read fenced lines too, as open-revision.sh did: refusing a label an example
 # mentions errs safe. The open-section check and the conversion skip fences, and must.
 ("c12", CL, ["98-fenced"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:9 lists revision 98-fenced as closed"), any=["layout", "root", "revision", "fix"])),
 ("c14", CL, ["99-example"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:8 already has a section for revision 99-example"), any=["layout", "root", "revision", "fix"])),
 ("c13", CL, ["03-b"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:17 lists revision 03-b as closed"), any=["layout", "root", "revision", "fix"])),
 ("c15", {"docs/plan/TODO.md": LATER}, ["02-b", "--render", "next"], dict(exit=0, out=LATER_AFTER)),
 # prose a legacy close left: warned on a paragraph at a time, outside fences, and carried over
 ("c16", {"docs/plan/TODO.md": PROSE}, ["02-b"], dict(exit=0, rep=rep(result="proposed", layout="legacy", root="docs/plan/TODO.md",
     revision="docs/plan/02-b/_TODO.md", change="convert", warnings=legacy_prose(8)))),
 ("c17", crlf({"docs/plan/TODO.md": PROSE}), ["02-b"], dict(exit=0, rep=rep(result="proposed", change="convert",
     warnings=legacy_prose(8)), any=["layout", "root", "revision"])),
 # a revisions index
 ("r01", IX, ["08-new"], dict(exit=0, rep=rep(result="proposed", layout="revisions", root="docs/plan/TODO.md",
     revision="docs/plan/08-new/_TODO.md", previous="docs/plan/07-rev-2/_TODO.md", change="append", open="07-rev-2",
     warnings="already open: 07-rev-2; with 08-new open too, /new-branch and the step commands will ask which revision a branch belongs to"))),
 ("r02", IX, ["05-old"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:7 already lists revision 05-old"), any=["layout", "root", "revision", "fix"])),
 ("r03", IX, ["06-dropped"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:8 already lists revision 06-dropped"), any=["layout", "root", "revision", "fix"])),
 ("r04", IX, ["07-rev-2"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:9 already lists revision 07-rev-2"), any=["layout", "root", "revision", "fix"])),
 ("r05", IX, ["07-rev"], dict(exit=0, rep=rep(result="proposed", change="append"), any=["layout", "root", "revision", "previous", "open", "warnings"])),
 ("r06", IX_DIR, ["08-new"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/08-new already exists, so revision 08-new has been opened before"), any=["layout", "root", "revision", "fix"])),
 ("r07", IX_BROKEN, ["08-new"], dict(exit=1, rep=rep(result="error", problem="revision 07-rev-2 is open at docs/plan/TODO.md:9, but docs/plan/07-rev-2/_TODO.md is missing"), any=["layout", "root", "revision", "fix"])),
 ("r08", IX, ["08-new", "--render", "the next one"], dict(exit=0, out=INDEX_AFTER)),
 ("r09", {"docs/plan/TODO.md": EMPTYINDEX}, ["01-a", "--render", "first"], dict(exit=0, out=EMPTYINDEX_AFTER)),
 ("r10", IX, ["09-fenced"], dict(exit=0, rep=rep(result="proposed", change="append"), any=["layout", "root", "revision", "previous", "open", "warnings"])),
 ("r11", crlf(IX), ["08-new", "--render", "the next one"], dict(exit=0, out=INDEX_AFTER)),
 ("r12", dict(IX, **{"docs/plan/TODO.md": INDEX + "\n## Revisions\n\n- [x] 10-last\n", "docs/plan/10-last/_TODO.md": "x\n"}),
     ["11-z"], dict(exit=0, rep=rep(result="proposed", previous="docs/plan/10-last/_TODO.md", change="append"),
     any=["layout", "root", "revision", "open", "warnings"])),
 # the model
 ("m01", BOTH, ["01-a"], dict(exit=1, rep=rep(result="error",
     problem="both docs/plan/DO.md and docs/plan/TODO.md exist, so which one is the root plan is ambiguous"), any=["fix"])),
 ("m02", IX, ["08-new", "--model", "DO.md"], dict(exit=1, rep=rep(result="error",
     problem="--model DO.md names the other file: the root plan is docs/plan/TODO.md", fix="leave --model out, or pass --model TODO.md"),
     any=["root", "revision"])),
 ("m03", IX, ["08-new", "--model", "TODO.md"], dict(exit=0, rep=rep(result="proposed"), any=KEYS[1:])),
 # --dry-run
 ("d01", IX, ["08-new", "--dry-run", DRY + "/new"], dict(exit=0, rep=rep(result="proposed"), any=KEYS[1:])),
 ("d02", IX, ["08-new", "--dry-run", "docs/plan/x"], dict(exit=1, rep=rep(result="error",
     problem="the dry-run path is inside docs/plan/, where its files would be read as plans"), any=["root", "revision", "fix"])),
 ("d03", IX, ["08-new", "--dry-run", "holds"], dict(exit=1, rep=rep(result="error",
     problem="the dry-run path already holds _TODO.md, which a dry run would overwrite"), any=["root", "revision", "fix"]), "holds"),
 ("d04", IX, ["08-new", "--dry-run", "README.md/x"], dict(exit=1, rep=rep(result="error",
     problem="the dry-run path runs through a file that is not a directory"), any=["root", "revision", "fix"])),
 ("d05", OL, ["05-x", "--dry-run", DRY + "/new"], dict(exit=1, rep=rep(result="refused", problem="docs/plan/TODO.md:5 has a section still open"),
     prefix=["problem"], any=["layout", "root", "revision", "fix"])),
 ("d06", IX, ["08-new", "--dry-run", "tmp/scratch"], dict(exit=0, rep=rep(result="proposed"), any=KEYS[1:])),
 ("d07", IX, ["08-new", "--dry-run", LINK + "/x"], dict(exit=1, rep=rep(result="error",
     problem="the dry-run path is inside docs/plan/, where its files would be read as plans"), any=["root", "revision", "fix"])),
 ("d08", IX, ["08-new", "--dry-run", "docs/plan"], dict(exit=1, rep=rep(result="error",
     problem="the dry-run path is inside docs/plan/, where its files would be read as plans"), any=["root", "revision", "fix"])),
 ("d09", IX, ["08-new", "--dry-run", "holds2"], dict(exit=1, rep=rep(result="error",
     problem="the dry-run path already holds TODO.md, which a dry run would overwrite"), any=["root", "revision", "fix"]), "holds2"),
 # --render when the result is not proposed: nothing on stdout, the report on stderr
 ("f01", IX, ["05-old", "--render", "x"], dict(exit=1, out="", errrep=rep(result="refused"))),
 # not a repository
 ("g01", NONE, "norepo", dict(exit=1, rep=rep(result="error", problem="the working directory is not inside a git repository",
     fix="run it from the repository"))),
]
# d03/d09 need a directory in the fixture holding a file; they name it in a fifth field.
EXTRA = {"holds": {"holds/_TODO.md": "x\n"}, "holds2": {"holds2/TODO.md": "x\n", "README.md": "x\n"}}
CASES = []
for c in C:
    cid, files, args, exp = c[:4]
    if len(c) > 4: files = dict(files, **EXTRA[c[4]])
    if cid == "d04": files = dict(files, **{"README.md": "x\n"})
    CASES.append((cid, files, args, exp))

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
    for cid, files, _, _ in CASES:
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
    real = shutil.which("awk") or sys.exit("no awk on PATH")
    for d, prefix in AWKSEL.values():
        os.makedirs(d, exist_ok=True)
        open(d + "/awk", "w").write(f'#!/bin/sh\ncase "$L" in "{prefix}"*) exit 2 ;; esac\nexec {real} "$@"\n')
        os.chmod(d + "/awk", 0o755)
    shutil.rmtree(DRY, ignore_errors=True); os.makedirs(DRY)
    if os.path.lexists(LINK): os.remove(LINK)
    os.symlink(FX + "/docs/plan", LINK)
    shutil.rmtree(NOREPO, ignore_errors=True); os.makedirs(NOREPO)

def run(cid, args, shell, script):
    env = dict(os.environ); cwd = FX; git("checkout", "-q", f"case/{cid}")
    env["GIT_CEILING_DIRECTORIES"] = W
    if args == "awk127": env["PATH"] = AWK127 + ":" + env["PATH"]; args = ["01-new"]
    if isinstance(args, str) and args in AWKSEL: env["PATH"] = AWKSEL[args][0] + ":" + env["PATH"]; args = ["01-new"]
    if args == "norepo": cwd = NOREPO; args = ["01-a"]
    return sh([shell, script, *args], cwd, env)

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
    if keys != KEYS or vals is None: return [f"{where} is not the ten-key report: {text[:160]!r}"]
    for k in KEYS:
        if k in exp["rep"]:
            want, got = exp["rep"][k], vals[k]
            ok = got.startswith(want) if k in exp.get("prefix", []) else got == want
            if not ok: probs.append(f"{k}: {got!r}, want {want!r}")
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
        if "errrep" in exp: probs += grade_report(dict(rep=exp["errrep"], any=KEYS[1:]), r.stderr, "stderr")
        elif r.stderr: probs.append(f"a render wrote to stderr: {r.stderr.strip()[:100]!r}")
    # A tool failure prints no report, and its PATH hint names the binary by absolute path.
    if exp["exit"] != 3 and W in r.stdout + r.stderr: probs.append("an absolute path in the output")
    return probs

def mutants():
    d = HERE + "/mutants"; tmp = W + "/prv-mut"; bad = 0
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for fn in sorted(f for f in os.listdir(d) if f.endswith(".patch")):
        name = fn[:-6]; root = f"{tmp}/{name}"; out = root + "/propose-revision.sh"
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
    for cid, _, args, exp in CASES:
        if want and cid not in want: continue
        outs, probs = set(), []
        for shell in SHELLS:
            for _ in range(1 if "--once" in sys.argv else 2):
                r = run(cid, args, shell, SCRIPT); outs.add((r.returncode, r.stdout, r.stderr))
                probs += [p for p in grade(exp, r) if p not in probs]
                if git("status", "--porcelain") or git("for-each-ref", "--format=%(refname) %(objectname)") != heads:
                    probs.append("the fixture changed")
                if os.listdir(DRY): probs.append("the dry-run directory gained a file")
        if len(outs) > 1: probs.append("output differs between runs or shells")
        print(f"{'PASS' if not probs else 'FAIL'} {cid:<4} " + "; ".join(probs))
        if "-v" in sys.argv: print("".join(o[1] + o[2] for o in sorted(outs)))
        fails += bool(probs)
    git("checkout", "-q", "main")
    print(f"\n{fails} failing"); sys.exit(1 if fails else 0)

main()
