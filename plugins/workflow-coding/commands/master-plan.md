---
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/propose-revision.sh:*), Bash(${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh:*), Bash(${CLAUDE_PLUGIN_ROOT}/scripts/check-draft.sh:*), Bash(git status:*), Bash(git log:*), Bash(git branch --show-current:*), Bash(git rev-parse:*), Bash(git checkout -b:*), Bash(git add:*), Bash(git commit:*), Read, Write, Edit, Agent, AskUserQuestion
argument-hint: "<label> [spec] [--dry-run <path>]"
description: Open a revision, drafting its master plan from a specification.
---

# /master-plan

Open a revision: a milestone whose subgoals each spawn a branch. This command drafts the
revision's master plan, `docs/plan/<label>/_TODO.md` (or `_DO.md`), from a specification,
has you review it, and lists the revision in the root plan, `docs/plan/TODO.md` (or
`DO.md`). The draft is the `plan-drafter` agent's; every write is yours to confirm.

Arguments: `$ARGUMENTS`. Read them as:

- **the label**, the first word: the revision's identity, naming its directory and its
  root-plan line. If there is none, ask for one; do not invent it. Suggest the shape
  `NN-topic` (`04-revision-lifecycle`): the ordinal sorts, the topic says what it covers.
- **`--dry-run <path>`**, anywhere: write the result to a directory instead (step 5).
- **the spec**, the rest: a path to a document if it names a file, otherwise pasted text.
  With no spec, it is the conversation, or what you ask for in step 2.

**Run every command alone**: one `Bash` call per command, never chained with `&&`, `;` or
a pipe, so each is matched against `allowed-tools` and its failure is seen. Run `git` in
the repository as `git <subcommand>`, never `git -C <path>`: a permission matches the
plain form only, so `git -C <path> status` is refused where `git status` is granted. If
step 1 settles on `--model TODO.md`, pass it to every later `propose-revision.sh` run too.

## 1. Propose

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/propose-revision.sh <label> [--dry-run <path>]
```

Read-only. It finds the root plan's layout (`none`, `legacy` or `revisions`), refuses a
label already taken, and reports in ten `key: value` lines: `result`, `layout`, `root`,
`revision`, `previous`, `change`, `open`, `warnings`, `problem`, `fix`. Show `warnings:`
if there are any.

- **`layout: none`.** There is no root plan yet. The default is `DO.md`, as `/new-branch`
  defaults; say so in one line and offer `TODO.md`, the `/hitl-step` model. If you
  choose `TODO.md`, run the script again with `--model TODO.md`.
- **`result: error`.** Relay `problem:` and `fix:` and stop. The fix is the user's to
  make, so do not work around it.
- **`result: refused`.** Relay `problem:` and `fix:`. A real run stops here: a label is
  never reopened, and a legacy root plan with a revision still open cannot be converted
  until that revision closes. A dry run carries on, saying that a real run would refuse.
- **`result: proposed`.** Carry on. `change:` says what the root plan gains: `create` a
  new index, `append` a line to the index, or `convert` a legacy root plan into an index.
  Say which in one line; `convert` rewrites each closed revision's pointer as an index
  line and moves no files.

## 2. The spec

- **A path.** Do not read it: the drafter reads it, so a long document stays out of this
  session.
- **Pasted text, or the conversation.** Pass it as written. From the conversation, take
  what the user said about this revision, not your summary of it.
- **Nothing.** Ask for what the revision is for, any decisions already settled, and the
  units of work, and pass the answers on as the spec.

## 3. Draft, and check it

Spawn the drafter with the `Agent` tool, `subagent_type: workflow-coding:plan-drafter`.
Its prompt gives: the label; today's date; the file name, `_TODO.md` or `_DO.md` from
`revision:`; the spec (the path, or the text); the root plan (`root:`, unless `layout:`
is `none`); and the previous revision's master plan (`previous:`, unless it is `—`).

It returns `## Draft`, `## Trace`, `## Left out` and `## Questions`. A script checks the
reply, so do not judge its form yourself. Write the reply to a file exactly as returned:
a line corrected in the copy hides the drafter's mistake from the check. Claude Code hands
a subagent's report back in a frame, a hand-back note before it, `agentId:` and `<usage>`
lines after it and two spaces before every line: write the report alone, without the
frame or its indent, so that `## Draft` starts its line. Use `reply.md`
in the scratchpad directory your system prompt names, or
`/tmp/master-plan-<label>-reply.md` if it names none; outside the repository, the file is
never committed and needs no cleanup. If the spec is pasted text or the conversation,
write the text you passed the drafter to `spec.md` beside it (in `/tmp`,
`/tmp/master-plan-<label>-spec.md`), so the trace's quoted phrases can be checked
against it. Then run:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/check-draft.sh <the reply file> --spec <the spec file> --label <label>
```

`--spec` takes the spec's path as given, or the `spec.md` just written. Read-only, it
reports in ten `key: value` lines: `result`, `input`, `file`, `spec`, `subgoals`, `tags`,
`where`, `problem`, `fix`, `message`; a key with several items continues on lines
indented two spaces.

- **`result: clean`.** Go on to step 4.
- **`result: problems`, in tags alone**, as `message:` says. Go on to step 4, where each
  tag that names nothing in the spec is a question.
- **`result: problems`, the reply copied in its frame**, as `message:` says. The copy is
  yours to correct, not the drafter's: write the file again without the frame, and check
  it again.
- **`result: problems`, otherwise.** Spawn the drafter once more, with the same prompt
  and each `problem:` line with its `fix:` line. Write its reply to `reply-2.md` beside
  the first, and check it the same way. If it still has problems other than tags, show
  them and stop.
- **`result: error`, or no `result:` or `message:` line.** Show the output and stop.

## 4. Review

Show the draft, the trace and `## Left out` as returned. Then work through the questions
with the user, one at a time (`AskUserQuestion` suits a choice between options): the
drafter's `## Questions`, and one for each tag the check could not resolve, since a
subgoal no part of the spec supports may be invented.

Judge the draft's fidelity from the trace, not by reading the spec. Every subgoal is
tagged, and every tag that resolved names a real part of the spec; whether that part
supports its subgoal is the judgement left. Where a subgoal is in doubt, its scope
reaching past what its tag names, read only that part. `where:` gives each tag's lines:
`N. <spec>:<from>-<to>` for a § or heading's section, `N. <spec>:<line>` for the line a
quoted phrase begins on. `Read` the spec with that `offset` and `limit`, about 20 lines
for a phrase, and never whole. Raise what you find as a question.

Apply each answer, and every edit the user asks for — merge, split, reorder, drop — to
the draft text here. Spawn the drafter again only if the user asks for a fresh draft, and
check its reply as step 3 does. Show the whole draft again after a round of edits, and
repeat until the user approves it.

Agree the root-plan line's note with the draft: one line, no tab, saying what the
revision is for. The line will read `- [~] <label> — <note>`.

## 5. Write — CONFIRM FIRST

**A dry run** writes into `<path>`, with no branch and no commit:

1. the approved draft to `<path>/<revision's file name>`;
2. if `result:` was `proposed`, the root plan as it would read: run

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/propose-revision.sh <label> --render "<note>"
   ```

   and write its output, exactly, to `<path>/<root's file name>`. Suggest
   `diff <root> <path>/<root's file name>` to see the change.

Then go to step 6.

**A real run** writes on a branch. The root plan lives on `main`, where branch
protection commonly forbids direct commits. On `main`, propose:

> I'll run `git checkout -b chore/open-<label>` and write there. Proceed?

On another branch, say which, and ask whether to write there or branch from `main`
first. Then:

1. run `propose-revision.sh <label> --render "<note>"` and write its output, exactly, to
   `root:`. With `change: convert` this rewrites the root plan; show the user what
   changes before writing it;
2. write the approved draft to `revision:`.

## 6. Check, before committing

Check the plan as written, alone:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/check-draft.sh --plan <the plan file> --label <label>
```

It takes `revision:`, or in a dry run `<path>/<revision's file name>`, and must report
`result: clean`: the review's edits kept the form. A dry run checks nothing more, and
goes to step 8. A real run must also pass these two, each run alone:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/locate-plan.sh <TODO.md|DO.md> -- <the revision: path>
${CLAUDE_PLUGIN_ROOT}/scripts/propose-revision.sh <label>
```

- `locate-plan.sh` takes the path step 1 reported as `revision:`
  (`docs/plan/<label>/_TODO.md`), not the label, and must report `result: found`, `plan:` the revision's file, and `next:`
  on subgoal 1: the revision's master plan reads as every later command will read it.
- `propose-revision.sh` must now refuse, with `problem:` saying the root plan already
  lists the label: the index reads, and it holds the new line.

If a check fails, relay its `problem:` and `fix:`, do not commit, and offer to correct the
written file; then run every check again. Never commit a revision the commands cannot
read.

## 7. Commit — CONFIRM FIRST

Once the user approves the commit, run the form check once more, alone, immediately
before `git add`, whether or not an edit was mentioned:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/check-draft.sh --plan <the revision: path> --label <label>
```

The file may have been edited since step 6 outside this session, by hand or by an
editor's formatter on save, and nothing tells the session so. If the check is not
`clean`, relay its `problem:` and `fix:` lines and do not commit. Then:

```bash
git add <root> <revision>
git commit -m "<subject>"
```

> **Subject.** The wording below is the message's *content*; its **form** is the
> repository's, not this plugin's. Before committing, run `git log --oneline -20`, alone,
> and match the dominant subject form — `/smart-commit` Step 3 states the rule in full,
> including why subjects matching this plugin's own templates must be discounted. To
> read it, `Read` `${CLAUDE_PLUGIN_ROOT}/commands/smart-commit.md` whole; never `grep`
> or `ls` it, or anything else in the plugin's directory: a shell read outside the
> repository prompts, where `Read` does not.
>
> Content: revision `<label>` is being opened.

Do not push: the branch reaches `main` through `/smart-merge`.

## 8. Report

- The label, its `**Version**:` line, and how many subgoals it has.
- What the root plan gained: created, a line appended, or converted.
- A dry run: the two files written, the form check's result, and the `diff` to run.
- A real run: the branch and commit, and that `/smart-merge` must land it before
  `/new-branch`, run from `main`, can see the revision.
- The first `/new-branch` to run: subgoal 1's text.

## Guidelines

- **Never invent a label, a subgoal or a decision.** What the spec does not support is a
  question for the user.
- **Never write a placeholder and leave it.** A preamble or subgoal with no content is
  worse than none, because it looks finished.
- **Never edit the root plan by hand.** Its new form comes from `--render`, so the rules
  for it live in one script.
- **A revision is never reopened.** Work that continues a closed revision opens a new one
  that says what it follows on from.
