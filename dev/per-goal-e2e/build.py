"""Build the per-goal end-to-end fixtures under $LOCATE_PLAN_WORK/e2e/: a copy of the working
tree's workflow-claude at a neutral path, and one consumer repository per scenario.

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
PLUGIN = f"{E}/p/{h('e2e/plugin')}/workflow-claude"   # run.sh and check.py derive the same path

# Every fixture carries this, and sessions obey a fixture's CLAUDE.md: the approvals the
# commands wait for are given here, so the commands themselves run unmodified.
CLAUDE_MD = """# Test repository

This repository is a test fixture for the workflow-claude plugin's commands. It has no
remote, so never push.

The user has approved every step of every command in advance. Do not stop to ask for
confirmation before creating a branch, writing or editing a file, or committing a command's
own files: do it, and say what you did. When /hitl-step or /step pauses to ask whether to
commit, the answer is to keep going without committing. When a command needs a decision
from the user, take the first option you offer, and log it as the user's answer wherever
the command says answers are logged.
"""
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
for d in ("p", "r1", "r3", "r4", "r5"): shutil.rmtree(f"{E}/{d}", ignore_errors=True)
os.makedirs(E, exist_ok=True)
shutil.copytree(REPO + "/plugins/workflow-claude", PLUGIN)
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
for r in ("r1", "r3", "r4", "r5"):
    print(f"{r}: {E}/{r} on {git(E + '/' + r, 'branch', '--show-current').strip()} at {git(E + '/' + r, 'rev-parse', '--short', 'HEAD').strip()}")
print(f"plugin copy: {PLUGIN}")
