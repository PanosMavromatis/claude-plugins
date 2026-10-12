# The per-goal layout — write-side specification

The reader side is settled: `scripts/locate-plan.sh` and its specification,
`locate-plan-spec.md` in the `feat-plan-locator` branch plan, already read a
`**Layout**: revisions` root index and a `**Layout**: per-goal` branch plan. Everything
here writes what that reader accepts, and where the two could disagree, the reader's
specification wins. The layout itself is §4.2 of the agreed plan
(`tmp/subagent-refactor-plan.md`, not under version control), with D2 (the goal file is
the source of truth for its marker) and D3 (goal files in `TODO/` or `DO/` beside the
index).

This revision builds the layout and does not adopt it. This repository's plans stay legacy
until the first step of R2. Legacy single-file plans stay readable and writable through 1.x.

## Which layout a new branch plan gets

The root plan decides, so a project switches once, by adopting the index, and upgrading
the plugin changes nothing until it does.

| `docs/plan/F` | The branch | Written |
|---|---|---|
| `**Layout**: revisions` index | executes a subgoal of an open revision | `docs/plan/<label>/<flat>/F` + `<flat>/F-without-.md/`, per-goal |
| `**Layout**: revisions` index | standalone | `docs/plan/<flat>/F` + goal files, per-goal, flat |
| a legacy master plan | either | `docs/plan/<flat>/F`, legacy single file, as today |
| none | standalone | `docs/plan/<flat>/F`, legacy single file, as today |

F is `TODO.md` or `DO.md`, chosen as `/new-branch` chooses it today. `<flat>` is the
branch with `/` flattened to `-`.

## What is written

**The branch index** (`<dir>/F`). Legacy plans keep today's form exactly.

```markdown
# <branch>

**Status**: active
**Created**: <YYYY-MM-DD>
**Revision**: <label>
**Subgoal**: <the subgoal's text, or standalone>
**Layout**: per-goal

## Goals

- [ ] 01 — <first Scope title>
- [ ] 02 — <second Scope title>
```

`**Revision**:` is left out for a standalone branch. Numbers are two digits, or more
when there are more than 99 goals, all zero-padded to the same width. The separator is
` — `. These are the forms `locate-plan.sh` reads: `title()` strips the number and a
following `—`, `-` or `:`.

**A goal file** (`<dir>/F-without-.md/NN-<slug>.md`), one per index line. `<slug>` is the
reader's `slug()` of the title: lowercase, each run of other characters as one `-`, at most
40 characters, `goal` if nothing is left.

```markdown
# NN — <title>

**Goal**: [ ]
```

Everything that sat under a goal in a legacy plan sits in its goal file, **outdented one
level**:
- indent-0 `>` lines are the goal's own (Q&A, `Note`, `Done`, `Blocked`, `Descoped`);
- indent-0 items are its subgoals (TODO model) or tasks (DO model);
- indent-2 `>` lines belong to the item above them.

The goal's own blockquotes go directly under `**Goal**:`, before the first item, so that
they read first.

**The backlink**: `  > **Branch:** <branch>`, inserted after the last line of the
subgoal's block in the master file. The block is the item line plus every following line
that is indented and non-blank, up to the next indent-0 line, heading or blank line. The
master file is the legacy master plan, or the revision's `_F`.

## `scripts/propose-branch-plan.sh`

A read-only script. It proposes, and `/new-branch` writes. It sits alongside
`open-revision.sh`, `file-plans.sh` and `close-revision.sh`, and follows `locate-plan.sh`'s
guarantees: fails loudly, deterministic, Bash 3.2, BSD and GNU, no clock.

```
propose-branch-plan.sh <TODO.md|DO.md> <branch> [--subgoal <file:line> | --standalone] [--] [title]...
```

**Report.** Always these keys, in this order, `—` when empty, with continuation lines
indented two spaces:

```
result:     propose | ask | error
layout:     per-goal | legacy
revision:   <label> | —
subgoal:    <master file>:<line> <the line, verbatim> | standalone
dir:        the branch plan's directory
index:      <dir>/F
goals:      <goal file> <its index line>, one per title (per-goal only)
backlink:   <master file>:<line>, the line to insert after | —
candidates: <master file>:<line> <the line>, one per open subgoal (ask only)
warnings:   one per line
problem:    which convention broke, and where (error only)
fix:        the command or edit that repairs it (error only)
message:    one sentence for the user
```

**Rules.**
- **The layout** comes from `docs/plan/F`, read with the reader's own functions: a
  revisions index (validated: E5, E6, E7) → per-goal; otherwise legacy.
- **The subgoal.**
  - `--subgoal` names the master file's line. It must be an open (`[ ]` or `[~]`)
    indent-0 item, in `_F` of an open revision or in the legacy master plan; otherwise
    an error.
  - `--standalone` takes none.
  - With neither, the candidates are every open indent-0 item in those files that has no
    `> **Branch:**` line yet. One or more → `ask`, and the command asks the user, offering
    standalone as well. None → `propose` standalone, with a warning saying why.
  - A `--subgoal` that already has a `> **Branch:**` line gets a warning: the subgoal may
    have been branched before.
- **The directory.** A directory named `<flat>` anywhere under `docs/plan/` is an error.
  That branch name has a plan already, and a second copy would be rung 2's stale
  duplicate. The fix names the existing plan, so the user can resume it, or says to pick
  another name.
- **The goals.** The titles come in order and are numbered `01…`. A title that is empty
  after trimming is an error. Two titles with one slug are fine, since the numbers
  differ.
  - A per-goal plan needs at least one title.
  - A title can't hold a newline or a tab (a usage error).
  - The width is two digits, or more at 100 goals and beyond.
- **The block and the backlink.** `SUBGOALS_AWK` in the library reads a master file's
  subgoals. A block is the item line and every following indented, non-blank line, up
  to the next indent-0 line, heading or blank line. `backlink:` names its last line.
  `/smart-merge` step 7 will look the backlink up with the same program.
- **Also reported, and checked:**
  - A legacy subgoal's `revision:` is its `## Subgoals — revision <label>` heading's
    label.
  - Under a revisions index with no revision open, the plan is standalone and flat, with
    a warning that says to open a revision first to file it under one.
  - With no `docs/plan/F` but a `docs/plan/F′`, it warns that the master plan uses the
    other model.
  - A branch name that is empty, holds whitespace or starts with `-` is a usage error.
- **When it runs.** `/new-branch` runs it once the name is agreed, before
  `git checkout -b`. A refused name or an `ask` happens while nothing exists yet, and the
  script never reads the current branch.
- **Read-only.** It writes nothing. The command writes exactly the paths it lists, and
  the date, which the script never reads.

Its suite is `dev/propose-branch-plan/`. Its case p24 writes what a proposal lists, then
checks it four ways:
- `locate-plan.sh` resolves it;
- `check-plan-index.sh` finds it clean;
- a second proposal for the same name is refused;
- the subgoal is no longer a candidate.

## One home for the rules

The rules that more than one script applies live in one sourced file,
`scripts/lib/plan-rules.sh`, which `locate-plan.sh`, `propose-branch-plan.sh` and
`check-plan-index.sh` all source. Those rules are:
- `slug()`, `title()` and `num()`;
- the revision-line and `**Layout**:` checks;
- the goal-file reading;
- the status read.

Copies would drift, and a slug that drifts names a file the reader can't find (E10).

Two things follow, and are part of the work:
- the `locate-plan` suite and its mutants must still pass, with the mutants also covering
  the shared file;
- `dev/locate-plan/trial/build-arms.py` moves the script out of the plugin root for its
  fault copies (`core.sh`), so it must take the shared file along.

## `/step` and `/hitl-step` on a per-goal plan

Step 1's text stays byte-identical across the two commands. The legacy path is unchanged
unless a line below says otherwise.

- **Step 1.** The "cannot yet edit goal files" stop goes. When the selected goal carries
  W11 (its index marker differs from its `**Goal**:`), the command offers to correct the
  index line to match the goal file, and re-runs the script once it is corrected. W11
  can occur because an interrupted Step 3 or Step 4 leaves the goal file ahead of the
  index.
- **Step 2.** The command reads the index and `goal-file:` whole. Both are small. A goal
  named out of order is found in the index the command has just read, and passed as
  `--goal`. No `Grep`.
- **Step 3.** On a flip to `[~]`, the command edits `**Goal**:` first, then the index
  line (D2). The goal file takes the Q&A, notes and subgoal markers. Escape hatch 3f:
  - a split goal becomes `NNa`, as a new index line right after NN plus a new goal file;
  - a descoped goal is flipped in both files, goal file first.
- **Step 4.** The parent rules read the goal file's items. The command edits
  `**Goal**:` first, then the index line. `> **Done:**` goes in the goal file, because
  that is where the PR drafter will read it.
- **Step 5.** The command re-runs `locate-plan.sh` to find the next goal, rather than
  re-reading or `Grep`ping. A per-goal plan's index is a few lines and the script takes
  about 60 ms. Moving the legacy path to the same mechanism belongs to the next subgoal
  (`Grep` and `Glob` can be missing).
- **Step 6.** The completion check runs `check-plan-index.sh` on Step 1's `plan:`. It
  reads the index and every goal file, and reports open items and drift. A per-goal plan
  has no `##` sections inside its goals, so "section complete" becomes "plan complete".
- **DO model (`/step`).** The unit is one task: the first `[ ]` in `subgoals:`, or the
  goal itself if its file has no tasks. When the last task is ticked, the command sets
  `**Goal**: [x]`, then the index line.

## `scripts/check-plan-index.sh`

A read-only drift report for a per-goal plan. It is built in goal 3, on the shared
library.

```
check-plan-index.sh <TODO.md|DO.md> [--] <index>
```

**The index is required.** It is the index file, or its directory, relative to the
repository root: the `plan:` that `locate-plan.sh` reports. Every caller already holds a
resolved plan, and resolving again would mean a second resolver to keep in step. An
absolute path is an error, since the report never carries one.

**Report.** Always these keys, in this order, `—` when empty, with continuation lines
indented two spaces:

```
result:   clean | drift | error
plan:     the index checked
goals:    the number of index lines
open:     path:line <the line>, every [ ] [~] [!] item in the index and its goal files
warnings: W6, as locate-plan.sh words it
problem:  one line per finding (drift), or why the plan could not be checked (error)
fix:      one line per problem, in the same order, read from the evidence
message:  one sentence
```

`problem:` and `fix:` pair line for line, because a command relays them in pairs. So a
finding never takes a continuation line: it lists line numbers, not paths. A branch name,
and so a path, may contain a comma.

**Exit.** 0 clean. 1 drift or error, which `result:` tells apart, so a hook or CI fails
on drift as `check-agents-md.sh` does. 2 usage. 3 a tool failed (stderr, with
`locate-plan.sh`'s `hint:` line).

**Findings**, goal by goal, in index order:

| # | When | Fix |
|---|---|---|
| D1 | an index marker differs from its goal file's `**Goal**:` | the goal file is the source of truth: the index line rewritten with its marker |
| D2 | a goal has no `NN-*.md` (E10) | E10's: `git mv` a near-miss name, else create `NN-<slug>.md`; or correct the number |
| D3 | a goal matches several files (E11) | which copy is stale is the user's call |
| D4 | a goal file no index line claims | the index line, from its heading and `**Goal**:`, or `git rm` it (the user's call) |
| D5 | an index line has no goal number (E9) | E9's, from `e9_fixes` |
| D6 | a goal number is on several index lines, compared as numbers (`02` is `2`) | which line keeps it is the user's call; the others get free numbers, past every goal file and past E9's |
| D7 | a goal file has no `**Goal**:` line | add one, with the index line's marker |
| D8 | `**Goal**: [x]` while the file still has open items | close the items, or reopen the goal; the user's call |

- **One report per file.** Only the first index line carrying a number is checked
  against its file. Any other line with that number belongs to D6, so a file is never
  read or reported twice.
- **Near misses and E9 come first.** A near-miss file name (`2-two.md` for goal `02`) is
  claimed by number and reported under D2, not D4. A file whose slug is an unnumbered
  line's title is E9's to place, not D4's.
- **`[-]` is not D8.** A descoped goal may keep open items: that is what descoping
  without doing means.
- **Errors, not drift:**
  - a plan without `**Layout**: per-goal`, since a legacy plan has nothing to drift;
  - E8, a `**Layout**:` value that is not valid;
  - E15, a file or directory that cannot be read;
  - a missing index;
  - an absolute path;
  - not being in a repository.

**Its callers.** Step 6 of both step commands (goal 5), and later `/smart-merge`
step 2's unfinished-items warning (the merge subgoal). Its suite is
`dev/check-plan-index/`.

## Not on this branch

These follow R1's order:
- `/smart-merge` stamping the branch index and editing `_TODO.md` (subgoal 5);
- `/master-plan` creating the index and `_TODO.md`, and `/close-revision` as a stamp
  (subgoal 6).

Until then a revisions index exists only in fixtures. `open-revision.sh` still writes the
old layout.
