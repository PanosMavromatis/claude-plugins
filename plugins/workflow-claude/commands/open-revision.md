---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/open-revision.sh:*), Bash(git status:*), Bash(git log:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git checkout -b:*), Bash(git add:*), Bash(git commit:*), Read, Write, Edit, Glob, Grep
argument-hint: "<label>"
description: Open a new revision in the master plan, identified by a label.
---

# /open-revision

Open a new revision: a milestone whose subgoals each spawn a branch, whose branch plans `/file-plans` gathers into one directory, and which `/close-revision` archives when it is finished.

Label: `$ARGUMENTS`. If none was given, ask for one — do not invent it. Suggest the shape `NN-topic` (`04-revision-lifecycle`), where the ordinal is for sorting and the topic says what the revision covers.

**The label is the revision's identity, not a position in a sequence.** It names the master-plan heading and the directory, so `docs/plan/` and the master plan each read without cross-referencing the other. That is the same rule branch plans follow — resolved by name, free to move — applied one level up. The numeric prefix is a sorting convention inside the label; nothing counts revisions or requires them to be consecutive.

## Workflow

### 1. Propose

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/open-revision.sh <label>
```

Read-only. It validates the label, refuses a duplicate, and prints the section it would insert and where. Show the user its output.

Relay a refusal rather than working around it:

- **section already exists** / **directory already exists** / **listed under Closed revisions** — that label is taken. A closed revision is never reopened by opening it again; if work continues on that theme, open a new revision with a new label and say what it follows on from.

### 2. Write the preamble — ASK

The script emits a placeholder paragraph. **Replace it with something that means something**, drafted from what the user has actually said: what prompted this revision, what it covers, and any decision already settled that should not be relitigated. Show the user your draft and take their corrections.

This is the one part of the revision lifecycle no command can generate. A revision's preamble is where the reasoning behind a milestone lives, and it is what a reader — human or model — hits first months later. A placeholder left in place is worse than no preamble at all, because it looks like a preamble.

Seed the section with the subgoals the user has described. If they have not described any yet, one `- [ ]` placeholder is fine — subgoals are added to an open revision as the work reveals them, which is the normal case, not an exception.

### 3. Branch — CONFIRM FIRST

The master plan lives on `main`, where branch protection commonly forbids direct commits. If the current branch is `main`, propose one:

> I'll run `git checkout -b chore/open-revision-<label>` and make the change there. Proceed?

Often the more natural move is to fold this into the branch that starts the revision's first subgoal — `/new-branch` will want to add a backlink under it anyway. Offer that when it applies, and say which branch the commit will land on.

### 4. Insert — CONFIRM FIRST

Insert the section at the line the script named, above `## Closed revisions` / `## Deferred` so open revisions stay together and the closed index stays at the bottom.

Watch the blank lines: a section run flush against the following `## ` heading breaks Markdown rendering.

**Do not create the directory.** `docs/plan/<label>/` is created by `/file-plans` when the first plan is filed into it. An empty directory is not tracked by git, so creating one here would either be lost or need a placeholder file that serves no purpose.

### 5. Commit — CONFIRM FIRST

```bash
git add docs/plan/DO.md
git commit -m "<subject>"
```

> **Subject.** The wording below is the message's *content*; its **form** is the
> repository's, not this plugin's. Before committing, read `git log --oneline -20` and
> match the dominant subject form — `/smart-commit` Step 3 states the rule in full,
> including why subjects matching this plugin's own templates must be discounted.
>
> Content: revision `<label>` is being opened.

### 6. Report

- The label, and where the section landed
- That the directory will appear on the first `/file-plans` run
- The branch the commit landed on, and that it still needs a PR
- The lifecycle from here: `/new-branch` per subgoal → work → `/smart-merge` → `/file-plans` → `/close-revision <label>` when the user says it is finished

## Guidelines

- **Never invent a label.** It is the name the project will use for this body of work.
- **Never write a placeholder preamble and leave it.** Draft a real one from what the user has said, or ask.
- **Revisions are not consecutive by contract.** Nothing counts them or checks the ordinal. A project may skip, or use a date prefix instead — the label only has to be unique.
- **Closing is a separate decision.** `/open-revision` never closes anything, and subgoals may be added to an open revision at any time.
