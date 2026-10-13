---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/close-revision.sh:*), Bash(git status:*), Bash(git log:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git checkout -b:*), Bash(git add:*), Bash(git commit:*), Read, Write, Edit
argument-hint: "<label>"
description: Close a finished revision: stamp it, or archive a legacy one and file its branch plans.
---

# /close-revision

Close a revision the user says is finished. How depends on the root plan's layout:

- **A revisions index** — the revision's master plan, `docs/plan/<label>/_TODO.md` (or
  `_DO.md`), already is the archive, and its branch plans already sit inside it. Closing
  is a stamp: `**Status**: open` becomes `**Status**: closed — <date>`, and the index
  line's `[~]` becomes `[x]`.
- **A legacy root plan** — the revision's `## Subgoals — revision <label>` section is cut,
  verbatim, into `docs/plan/<label>/_TODO.md`, a pointer takes its place under
  `## Closed revisions`, and the revision's merged branch plans, still flat under
  `docs/plan/`, are moved into its directory.

Revision label: `$ARGUMENTS`. If none was given, ask for it; do not guess. A revision is
identified by its **label**, which names its directory and its line in the root plan.

**You do not decide that a revision is finished — the user does.** A revision is closed
when they say so, not when its last checkbox ticks: subgoals can still be added to a
revision whose earlier items have all merged. The script refuses on open items as a safety
net, not as the judgement.

**Run every command alone**: one `Bash` call per command, never chained with `&&`, `;` or
a pipe, so each is matched against `allowed-tools` and its failure is seen. Run `git` in
the repository as `git <subcommand>`, never `git -C <path>`: a permission matches the
plain form only, so `git -C <path> status` is refused where `git status` is granted. Pass
today's date, `YYYY-MM-DD`, as `--date` to every run of the script, the same date each time.

## 1. Propose

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/close-revision.sh <label> --date <YYYY-MM-DD>
```

Read-only. It reports in twelve `key: value` lines: `result`, `layout`, `root`,
`revision`, `change`, `edits`, `section`, `pointer`, `moves`, `warnings`, `problem`,
`fix`. Show the user the report.

- **`result: error`** or **`result: refused`** — relay `problem:` and `fix:` and stop.
  Never edit the plan to satisfy a refusal: an open item is the user's to finish, descope
  (`[-]`) or move, and a closed revision stays closed.
- **`result: proposed`** — say what closing will do:
  - **`change: stamp`** — the two lines in `edits:`, each `<path>:<line>: <new text>`;
  - **`change: extract`** — the `section:` that moves to `revision:`, the `pointer:` that
    replaces it, and each `moves:` line.

  Show `warnings:` if there are any: a branch plan not yet merged stays where it is, and
  the user may want to merge it before closing.

## 2. Branch — CONFIRM FIRST

The root plan lives on `main`, where branch protection commonly forbids direct commits. On
`main`, propose:

> I'll run `git checkout -b chore/close-<label>` and make the change there. Proceed?

On another branch, say which, and ask whether to write there or branch from `main` first.

## 3. Write — CONFIRM FIRST

**A stamp.** For each `edits:` line, `Edit` that line of that file to the new text: the
whole line, and nothing else in the file.

**A cut.** Render both files first, before writing either: once the archive exists the
script refuses, and once the root plan is cut there is no section left to render.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/close-revision.sh <label> --date <YYYY-MM-DD> --render archive
${CLAUDE_PLUGIN_ROOT}/scripts/close-revision.sh <label> --date <YYYY-MM-DD> --render root
```

Then:

1. write the archive's output, exactly, to `revision:`. This creates
   `docs/plan/<label>/`, which the moves need;
2. write the root plan's output, exactly, to `root:`;
3. run each `moves:` line exactly as printed, one at a time. The script prints a move only
   for a plain directory name, `[A-Za-z0-9._+-]`, since a backlink is text from the plan and
   shell syntax in it would run. `git mv` is deliberately not allow-listed, so each also asks
   for permission: a second gate on a move.

The archive is the section **verbatim** — a closed revision is a record, so summarising it
destroys what the plan convention exists to keep — and the cut is a **cut**, not a copy:
the section must not survive in the root plan.

## 4. Check, before committing

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/close-revision.sh <label> --date <YYYY-MM-DD> --check
```

It recomputes from `HEAD` what closing must have written and compares it with the working
tree: the two edited lines, or the archive, the root plan and every move. It must report
`result: verified`. If not, relay `problem:` and `fix:`, put the file right, and check
again. Never commit a close the check has not verified.

## 5. Commit — CONFIRM FIRST

```bash
git add <root> <revision>
git commit -m "<subject>"
```

The moves are already staged by `git mv`.

> **Subject.** The wording below is the message's *content*; its **form** is the
> repository's, not this plugin's. Before committing, run `git log --oneline -20`, alone,
> and match the dominant subject form — `/smart-commit` Step 3 states the rule in full,
> including why subjects matching this plugin's own templates must be discounted. To
> read it, `Read` `${CLAUDE_PLUGIN_ROOT}/commands/smart-commit.md`; never search the
> plugin's directory with `ls` or `grep`.
>
> Content: revision `<label>` is being closed.

## 6. Report

- The label, and how it closed: stamped, or archived with its pointer.
- The branch plans moved, and any `warnings:` left: a plan not yet merged stays flat, and
  is moved by hand with `git mv` once it merges.
- The branch the commit landed on, and that it still needs a PR (`/smart-merge`).

## Guidelines

- **Never infer that a revision is done.** The label comes from the user. If the script
  refuses, relay the refusal rather than editing the plan to satisfy it.
- **Never retype a file the script renders.** The archive and the cut root plan come from
  `--render`, so their rules live in one script, and `--check` confirms the copy.
- **Cut, never copy; the archive is verbatim.**
- **The close files the plans.** The legacy close moves the revision's merged branch plans;
  there is no separate filing command.
