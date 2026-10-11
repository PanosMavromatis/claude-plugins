# `close-revision.sh`: specification

The read-only proposer behind `/close-revision` (`feat-master-plan` goal 5, Q1 and Q3). It
decides whether a revision may be closed and what closing it changes, and checks the
command's writes before they are committed. It writes nothing.

## Usage

    close-revision.sh <label> --date <YYYY-MM-DD>
    close-revision.sh <label> --date <YYYY-MM-DD> --render root|archive
    close-revision.sh <label> --date <YYYY-MM-DD> --check

- `<label>`: as `propose-revision.sh` takes it.
- `--date`: the closing date, which the command supplies; the script never reads the clock.
- `--render`, legacy only: print the root plan after the cut (`root`), or the archive
  (`archive`), and nothing else. Exit 1 unless the result would be `proposed`, with the
  report on stderr.
- `--check`: compare the working tree with what closing must have written, computed from
  `HEAD`'s files. `result: verified`, or `result: error` naming what differs.

Exit: 0 proposed, rendered or verified; 1 refused or error; 2 usage; 3 a tool failed.

## The report

Twelve lines, always in this order, repo-relative paths, `—` for an empty value:

    result: proposed | refused | error | verified
    layout: legacy | revisions
    root: docs/plan/<model>
    revision: docs/plan/<label>/_<model>
    change: stamp | extract, or — unless proposed
    edits: stamp only, one per line: <path>:<line>: <new text>
    section: extract only: <root>:<start>-<end>
    pointer: extract only: the pointer line
    moves: extract only, one per line: git mv docs/plan/<plan> docs/plan/<label>/<plan>
    warnings: …
    problem: …
    fix: …

## The rules

The layout is `master_files`': no root plan is an error ("nothing to close"); an index
violation (E5–E8) is an error with its problem and fix.

**revisions** (`change: stamp`), refusing in order:
1. the index has no `## Revisions` line for the label;
2. its marker is not `[~]`, naming it: `[x]` is already closed, the others never opened;
3. `_<model>` has no `**Status**:` line (error), or its value is not `open`, naming it;
4. `_<model>` has an open item, `[ ]`, `[~]` or `[!]`, at any indent outside fences (the
   check `/hitl-step` makes before calling a plan complete), each listed with its line.

Then `edits:` names `_<model>`'s `**Status**:` line as `**Status**: closed — <date>`,
and the index line with its marker as `[x]`, the rest unchanged. A branch plan inside
`docs/plan/<label>/` still stamped `active` is a warning, not a refusal. Nothing moves:
`/new-branch` created each plan inside the revision.

**legacy** (`change: extract`): today's rules, with whole-label matching. Refused, in order:
1. no section, `## Subgoals — revision <label>` alone or with `: <subtitle>`
   (`section_line`);
2. an open item in the section, at any indent outside fences, each listed;
3. `docs/plan/<label>/_<model>` already exists.

The section runs from its heading to the line before the next `## ` heading, or to the end
of the file. The pointer is `- **Revision <label>**[ — <subtitle>] — closed. See \`<archive>\`.`

`moves:` files the revision's branch plans, the job `/file-plans` did. Each
`> **Branch:** <name>` line in the section, at any indent outside fences, names a plan
directory, `<name>` with `/` flattened to `-`, matched whole:
- flat, `docs/plan/<plan>/<model>`, stamped `merged`: moved into `docs/plan/<label>/`;
- flat and not stamped `merged`: a warning, left flat;
- not flat, but found by name elsewhere under `docs/plan/`: already grouped, nothing to do;
- not found at all: a warning;
- `docs/plan/<label>/<plan>` already there: an error, naming both.

`--render archive` is the section, verbatim, LF. `--render root` is the root plan without
the section, with the pointer after the last `- **Revision ` line under `## Closed
revisions`, or after the last non-blank line of that section if it has none. With no such
section, `## Closed revisions`, a blank line and the pointer go before `## Deferred`, or at
the end, with a blank line on each side.

**`--check`** recomputes from `HEAD`: for `stamp`, the two files with the two lines
rewritten; for `extract`, the archive and the root plan as `--render` gives them, and each
move done (the plan under `docs/plan/<label>/`, nothing left at its flat path). Each file
must match the working tree byte for byte. If `HEAD` already holds the result, say so: the
check runs before the commit.

Matching is whole-label and literal (`ENVIRON`, never `-v`); a trailing CR is dropped on
read.
