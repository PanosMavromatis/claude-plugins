"""Build the per-goal end-to-end fixtures under $LOCATE_PLAN_WORK/e2e/: a copy of the working
tree's workflow-coding at a neutral path, and one consumer repository per scenario.

  LOCATE_PLAN_WORK=<dir> python3 -I build.py

Rebuilds the fixtures and the plugin copy every time, so a run always starts from the same
state, and keeps earlier runs' out-*/ results. Writes only under $LOCATE_PLAN_WORK/e2e. The sessions (run.sh) and the grading (check.py) come after."""
import hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
W = os.environ.get("LOCATE_PLAN_WORK") or sys.exit("set LOCATE_PLAN_WORK to a directory outside the repository")
os.makedirs(W, exist_ok=True); W = os.path.realpath(W)
if (W + "/").startswith(os.path.realpath(REPO) + "/"): sys.exit(f"refusing: {W} is inside the repository")
E = W + "/e2e"
def h(label): return hashlib.sha1(label.encode()).hexdigest()[:8]
PLUGIN = f"{E}/p/{h('e2e/plugin')}/workflow-coding"   # run.sh and check.py derive the same path

# Every fixture carries this, and sessions obey a fixture's CLAUDE.md: the approvals the
# commands wait for are given here, so the commands themselves run unmodified.
CLAUDE_MD = """# Test repository

This repository is a test fixture for the workflow-coding plugin's commands. It has no
remote, so never push.

The user has approved every step of every command in advance. Do not stop to ask for
confirmation before creating a branch, writing or editing a file, or committing a command's
own files: do it, and say what you did. When /hitl-step or /step pauses to ask whether to
commit, the answer is to keep going without committing. When a command needs a decision
from the user, take the first option you offer, and log it as the user's answer wherever
the command says answers are logged.

`gh` here is a test stub standing in for GitHub: use it for every GitHub operation. There
is no GitHub MCP server for this repository.
"""
# The merge sessions' gh: no network, every call logged to $GH_LOG, a PR body file copied
# in whole. pr create answers with PR #42; there are no PRs before it and no checks.
GH = r"""#!/bin/sh
log="${GH_LOG:?GH_LOG is not set}"
{ printf 'ARGV'; for a in "$@"; do printf ' %s' "$a"; done; printf '\n'; } >> "$log"
case "$1 $2" in
  "pr create")
    while [ $# -gt 0 ]; do
      if [ "$1" = --body-file ] && [ $# -ge 2 ]; then { echo BODY-BEGIN; cat "$2"; echo; echo BODY-END; } >> "$log"; fi
      shift
    done
    echo "https://github.com/e2e/fixture/pull/42" ;;
  "pr list") case " $* " in *" --json "*) echo "[]" ;; esac ;;
  "pr view") echo "no pull requests found for branch" >&2; exit 1 ;;
  "pr checks") echo "no checks reported on the branch" >&2; exit 1 ;;
  "pr merge") echo "Merged pull request #42" ;;
  *) echo "gh stub: unsupported: $*" >&2; exit 1 ;;
esac
"""
GHBIN = f"{E}/bin/{h('e2e/gh')}"   # run.sh derives the same path
INDEX = lambda model: f"""# Plans

**Layout**: revisions

## Revisions

- [~] 07-rev — the per-goal fixture
- [x] 05-old — closed
"""
REVMASTER = """# Revision 07-rev

**Status**: open

## Subgoals

- [x] 1. First, merged
  > **Branch:** feat/first
- [ ] 2. Plan directory structure
  Scope: two notes files. Acceptance: both exist.
- [ ] 3. Another one
"""
LEGACY = """# Master plan

**Status**: active

## Subgoals — revision 03-old

- [x] Done already
  > **Branch:** feat/old
- [ ] Write the legacy notes
  Scope: one file.
- [ ] Something else
"""
HALF_INDEX = """# feat/half-done

**Status**: active
**Created**: 2026-10-10
**Revision**: 07-rev
**Subgoal**: 2. Plan directory structure
**Layout**: per-goal

## Goals

- [ ] 01 — Create notes/half.txt containing the word half
- [ ] 02 — Create notes/done.txt containing the word done
"""
GOAL = lambda nn, t, m: f"# {nn} — {t}\n\n**Goal**: [{m}]\n"

# The revision sessions (m*, c*). A spec the drafter reads, and the root plans it opens a
# revision under: an index (m1), a legacy plan with nothing open (m2) and with a revision
# open (m3). Then the closes: an index whose revision is finished (c1) or not (c3), and a
# finished legacy section with two merged flat plans and one still active (c2).
SPEC = """# A changelog for the fixture

Why: users cannot tell what changed between releases, and every release note is written
from memory.

Settled: the changelog is one file, `CHANGELOG.md`, in the Keep a Changelog form. Nothing
is generated from commits.

The work, in order:
1. Add `CHANGELOG.md` with an Unreleased section and the past releases' entries.
2. Add a section to `CLAUDE.md` saying every user-visible change adds an Unreleased line.
3. Add a check script, `scripts/check-changelog.sh`, that fails when Unreleased is empty
   on a release branch.
"""
LEGACY_CLOSED = """# Master plan

**Status**: active

## Closed revisions

- **Revision 03-old** — closed. See `docs/plan/03-old/_TODO.md`.
"""
ARCHIVE = """## Subgoals — revision 03-old

- [x] Done already
  > **Branch:** feat/old
"""
DONE_REV = REVMASTER.replace("- [ ] 2.", "- [x] 2.").replace("- [ ] 3.", "- [-] 3.")
LEGACY_DONE = """# Master plan

**Status**: active

## Subgoals — revision 03-old

Notes for the revision, kept verbatim in its archive.

- [x] Write the legacy notes
  > **Branch:** feat/old-a
- [x] Write the other notes
  > **Branch:** feat/old-b
- [-] Something else
  > **Branch:** feat/old-c
  > **Descoped:** not needed.

## Closed revisions

- **Revision 02-older** — closed. See `docs/plan/02-older/_TODO.md`.
"""
FLAT = lambda b, st: f"# {b}\n\n**Status**: {st}\n**Created**: 2026-10-01\n\n## Tasks\n\n- [x] The work\n"

def git(cwd, *a):
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True)
    if r.returncode: sys.exit(f"git {' '.join(a)} in {cwd}: {r.stderr}")
    return r.stdout

def repo(name, files, branch=None, branch_files=None):  # branch_files goes with branch
    d = f"{E}/{name}"; os.makedirs(d)
    git(d, "init", "-q", "-b", "main")
    for k, v in (("user.email", "e2e@example.invalid"), ("user.name", "e2e"), ("commit.gpgsign", "false")): git(d, "config", k, v)
    for rel, text in {"CLAUDE.md": CLAUDE_MD, "README.md": f"# {name}\n", **files}.items():
        os.makedirs(os.path.dirname(f"{d}/{rel}") or d, exist_ok=True); open(f"{d}/{rel}", "w").write(text)
    git(d, "add", "-A"); git(d, "commit", "-q", "-m", "fixture")
    if branch:
        git(d, "checkout", "-q", "-b", branch)
        for rel, text in branch_files.items():
            os.makedirs(os.path.dirname(f"{d}/{rel}"), exist_ok=True); open(f"{d}/{rel}", "w").write(text)
        git(d, "add", "-A"); git(d, "commit", "-q", "-m", "half done")
    return d

# the fixtures and the plugin copy are rebuilt; earlier runs' out-*/ results are kept
for d in ("p", "r1", "r3", "r4", "r5", "r1m", "r3m", "r4m", "bin", "m1", "m2", "m3", "c1", "c2", "c3", "_main"):
    shutil.rmtree(f"{E}/{d}", ignore_errors=True)
os.makedirs(E, exist_ok=True)
os.makedirs(GHBIN); open(GHBIN + "/gh", "w").write(GH); os.chmod(GHBIN + "/gh", 0o755)
shutil.copytree(REPO + "/plugins/workflow-coding", PLUGIN)
repo("r1", {"docs/plan/TODO.md": INDEX("TODO.md"), "docs/plan/07-rev/_TODO.md": REVMASTER,
            "docs/plan/05-old/_TODO.md": REVMASTER.replace("07-rev", "05-old")})
repo("r3", {"docs/plan/DO.md": INDEX("DO.md"), "docs/plan/07-rev/_DO.md": REVMASTER,
            "docs/plan/05-old/_DO.md": REVMASTER.replace("07-rev", "05-old")})
repo("r4", {"docs/plan/TODO.md": LEGACY})
repo("r5", {"docs/plan/TODO.md": INDEX("TODO.md"),
            "docs/plan/07-rev/_TODO.md": REVMASTER.replace("- [ ] 2. Plan directory structure\n",
                                                            "- [~] 2. Plan directory structure\n  > **Branch:** feat/half-done\n"),
            "docs/plan/05-old/_TODO.md": REVMASTER.replace("07-rev", "05-old")},
     branch="feat/half-done", branch_files={
            "docs/plan/07-rev/feat-half-done/TODO.md": HALF_INDEX,
            "docs/plan/07-rev/feat-half-done/TODO/01-create-notes-half-txt-containing-the-wor.md": GOAL("01", "Create notes/half.txt containing the word half", "~"),
            "docs/plan/07-rev/feat-half-done/TODO/02-create-notes-done-txt-containing-the-wor.md": GOAL("02", "Create notes/done.txt containing the word done", " ")})
OLD05 = {"docs/plan/05-old/_TODO.md": REVMASTER.replace("07-rev", "05-old").replace("**Status**: open", "**Status**: closed — 2026-09-01")}
repo("m1", {"docs/plan/TODO.md": INDEX("TODO.md"), "docs/plan/07-rev/_TODO.md": REVMASTER, **OLD05, "docs/spec/08-next.md": SPEC})
repo("m2", {"docs/plan/TODO.md": LEGACY_CLOSED, "docs/plan/03-old/_TODO.md": ARCHIVE, "docs/spec/04-next.md": SPEC})
repo("m3", {"docs/plan/TODO.md": LEGACY, "docs/spec/04-next.md": SPEC})
repo("c1", {"docs/plan/TODO.md": INDEX("TODO.md"), "docs/plan/07-rev/_TODO.md": DONE_REV, **OLD05,
            "docs/plan/07-rev/feat-first/TODO.md": FLAT("feat/first", "merged — PR #3 — 2026-10-02")})
repo("c2", {"docs/plan/TODO.md": LEGACY_DONE, "docs/plan/02-older/_TODO.md": "## Subgoals — revision 02-older\n",
            **{f"docs/plan/feat-old-{x}/TODO.md": FLAT(f"feat/old-{x}", st) for x, st in
               (("a", "merged — PR #4 — 2026-10-03"), ("b", "merged — PR #5 — 2026-10-04"), ("c", "active"))}})
repo("c3", {"docs/plan/TODO.md": INDEX("TODO.md"), "docs/plan/07-rev/_TODO.md": REVMASTER, **OLD05})
for r in ("r1", "r3", "r4", "r5", "m1", "m2", "m3", "c1", "c2", "c3"):
    print(f"{r}: {E}/{r} on {git(E + '/' + r, 'branch', '--show-current').strip()} at {git(E + '/' + r, 'rev-parse', '--short', 'HEAD').strip()}")
print(f"plugin copy: {PLUGIN}")
