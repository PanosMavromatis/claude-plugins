# `propose-revision.sh`: specification

The read-only proposer behind `/master-plan` (`feat-master-plan` goal 4, Q1–Q6). It
decides whether a revision may be opened and what the root plan would read afterwards. It
writes nothing; `/master-plan` writes, after the user confirms.

## Usage

    propose-revision.sh <label> [--model DO.md|TODO.md] [--dry-run <path>]
    propose-revision.sh <label> [--model DO.md|TODO.md] --render <note>

- `<label>`: non-empty; no space, `/` or `—`; does not start with `#` or `-`.
- `--model`: only matters with no root plan, where the default is `DO.md`, as in
  `/new-branch`. With a root plan, naming the other file is an error.
- `--dry-run <path>`: also check the path, taken relative to the repository root, with no
  `.` or `..` component, and resolved through symlinks. A path inside `docs/plan/`, one that
  runs through a file, or one where `<path>/_<model>` or `<path>/<model>` exists, is an error.
- `--render <note>`: print only the root plan as it would read after the change. Exit 1
  unless the result would be `proposed`, with the report on stderr and nothing on stdout.
  `<note>` is the new index line's note: one line, non-empty, no tab.

Exit: 0 proposed or rendered; 1 refused or error; 2 usage; 3 a tool failed.

## The report

Ten lines, always in this order, repo-relative paths, `—` for an empty value:

    result: proposed | refused | error
    layout: none | legacy | revisions
    root: docs/plan/<model>
    revision: docs/plan/<label>/_<model>
    previous: docs/plan/<previous>/_<model>, or —
    change: create | convert | append, or — unless proposed
    open: the open revisions' labels, comma-separated
    warnings: …
    problem: …
    fix: …

## The rules

The layout: `none` with neither `docs/plan/DO.md` nor `docs/plan/TODO.md`; `revisions`
when the root plan has `**Layout**: revisions`; otherwise `legacy`. Both root files is an
error. Checks run in the order given; the first refusal is the one reported.

**none**: `docs/plan/<label>` existing refuses. Otherwise `change: create`, rendered as:

    # Master plan

    **Layout**: revisions

    ## Revisions

    - [~] <label> — <note>

**revisions**: the index is read by `index_open`; an E5–E7 violation is `result: error`
with its problem and fix. A `## Revisions` line for the label, under any marker, refuses;
then `docs/plan/<label>` existing refuses. Otherwise `change: append`: the new line goes
directly after the section's last revision line, or first in it if it has none. A
non-empty `open:` warns that `/new-branch` and the step commands will ask which revision.

**legacy**: refuses, in order, on a `## Subgoals — revision <label>` heading (alone or
with `: <subtitle>`); a line starting `- **Revision <label>**`; `docs/plan/<label>`
existing; and any other `## Subgoals` heading, named with its line ("close that revision
first, or convert by hand"). Otherwise `change: convert`, rendered as the root plan with:
1. `**Layout**: revisions` directly after the first `**Status**:` line, as headers stack,
   or after line 1 and a blank line if there is none. An existing `**Layout**:` line is
   rewritten instead, since only the first is read;
2. `## Closed revisions` renamed `## Revisions`, or a `## Revisions` section appended if
   there is no such heading;
3. each `- **Revision <l>**<rest>` line under `## Closed revisions` as `- [x] <l><rest>`;
   one quoted in another section is left alone. A pointer that would not convert to a line
   `index_open` accepts (a label, then nothing or ` — <note>`) is `result: error`, naming it;
4. the new line after the last revision line;
5. every other line unchanged.

Prose a legacy close left, carried over by 5, may describe that close. A paragraph outside
fenced blocks, a run of non-blank lines, that names `/close-revision` and a word starting
`extract` or `move`, in any case and at a word's start, warns once, naming its first line
that names `/close-revision`: `<root>:<n> describes the legacy close, which extracts or
moves a revision; under a revisions index /close-revision only stamps, so reword it once
converted`. It is checked only once nothing refuses, and it warns rather than rewrites:
only the user can reword free text.

Matching is whole-label and literal throughout (`ENVIRON`, never `-v`), and a trailing CR
is dropped on read. Rendered output is LF. The label refusals read fenced lines too, as
`open-revision.sh` did: refusing a label an example mentions errs safe. The open-section
check and the conversion skip fenced blocks, and must.

**previous**: the last revision line listed (revisions) or the last `- **Revision …**`
pointer (legacy), as `docs/plan/<that>/_<model>` when that file exists, else `—`. Last
listed, not highest sorting: the index's order is the project's.
