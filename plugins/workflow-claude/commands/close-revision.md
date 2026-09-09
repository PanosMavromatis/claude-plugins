---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/close-revision.sh:*), Bash(git status:*), Bash(git log:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git checkout -b:*), Bash(git add:*), Bash(git commit:*), Bash(mkdir:*), Read, Write, Edit, Glob, Grep
argument-hint: "<revision-number>"
description: Extract a finished revision's section from the master plan into its revision directory.
---

# /close-revision

Extract the `## Subgoals — revision <label>` section out of the master plan and into `docs/plan/<label>/_DO.md`, leaving a one-line pointer where it was. The master plan then reads as an index of closed revisions plus whatever is currently open, and stays roughly constant in size instead of accumulating every subgoal the project has ever completed.

Revision label: `$ARGUMENTS` — e.g. `03-subgoal-plan-management`. If none was given, list the revisions present in the master plan with their open-item counts and ask which to close. A revision is identified by its **label**, not by a number: the label names the heading and the directory alike.

**You do not decide that a revision is finished — the user does.** A revision is closed when they say so, not when its last checkbox ticks, because subgoals can still be added to a revision whose earlier items have all merged. This plugin's own revision 3 took three more subgoals after its first three had shipped. The script refuses on unchecked items as a safety net, not as the judgement.

## Workflow

### 1. Propose

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/close-revision.sh <label>
```

Read-only: it prints the section it would extract, the destination, and the pointer that would replace it, then stops. Show the user its output.

If the script refuses, relay the reason and stop — do not work around it:

- **unfinished items** — it lists them. The user closes, descopes, or moves them to another revision first. `[x]` and `[-]` are finished; `[ ]`, `[~]` and `[!]` are not.
- **no such section** — the label is wrong, or the heading is a bare `## Subgoals` with no revision label (this project's revision 1 predates the convention and cannot be closed).
- **destination exists** — that revision is already closed.

### 2. Branch — CONFIRM FIRST

The master plan lives on `main`, where branch protection commonly forbids direct commits. If the current branch is `main`, propose one:

> I'll run `git checkout -b chore/close-revision-<N>` and make the change there. Proceed?

Say which branch the commit will land on either way.

### 3. Extract — CONFIRM FIRST

On approval:

1. `mkdir -p docs/plan/<label>/` if it does not exist — a revision with no branch plans filed into it will not have the directory yet.
2. Write the section verbatim to `docs/plan/<label>/_DO.md` (or `_TODO.md` for a `TODO.md` master), preserving it exactly as it appeared, including every `> **Branch:**` and `> **Done:**` blockquote. Add nothing and reword nothing — this is an archive, not a summary.
3. Delete those same lines from the master plan.
4. Add the pointer line under a `## Closed revisions` heading, creating that section if it does not exist yet. Put it immediately before `## Deferred` if there is one, otherwise at the end. Pointers accumulate there in revision order, so the master plan ends with a short index of finished revisions rather than a scatter of orphan bullets where sections used to be.

Watch the blank lines: a pointer left flush against the following `## ` heading breaks Markdown rendering, and collapsing consecutive newlines while removing the section is an easy way to cause exactly that. Check the result.

**The extraction is a cut, not a copy.** If the section survives in both files, the master plan keeps growing — the one thing this command exists to prevent — and the two copies drift. Verify after writing that the section appears in exactly one file.

**The archive is `_DO.md`, never `DO.md`.** Plan resolution globs `docs/plan/**/DO.md` and matches on filename, so an archive named `DO.md` would be indistinguishable from a branch plan and would surface in the disambiguation prompt as a place to do work. The underscore keeps a finished revision out of resolution entirely, which is the correct behaviour; it stays reachable by explicit path. Do not "normalize" the name.

### 4. Commit — CONFIRM FIRST

```bash
git add docs/plan/DO.md docs/plan/<label>/_DO.md
git commit -m "<subject>"
```

> **Subject.** The wording below is the message's *content*; its **form** is the
> repository's, not this plugin's. Before committing, read `git log --oneline -20` and
> match the dominant subject form — `/smart-commit` Step 3 states the rule in full,
> including why subjects matching this plugin's own templates must be discounted.
>
> Content: revision `<label>` is being closed and its section archived.

### 5. Verify and report

Confirm, and report:

- The section is now in exactly one place.
- `Grep` the master plan for the pointer line to confirm it landed.
- Plan resolution is unaffected: the master plan still resolves on `main`, and the archive does **not** appear among `docs/plan/**/DO.md` matches.
- Which branch the commit landed on, and that it still needs a PR.

## Guidelines

- **Never infer that a revision is done.** The number comes from the user. If they ask you to close a revision the script refuses, relay the refusal rather than editing the plan to satisfy it.
- **The archive is verbatim.** Summarizing a closed revision destroys the record the two-tier plan convention exists to keep.
- **Cut, never copy.**
- **Filing comes first.** Run `/file-plans` before closing a revision, or the revision's directory ends up holding an archive describing branch plans that are still sitting flat elsewhere.
