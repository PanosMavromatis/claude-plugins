---
description: Write tmp/session-handoff.md for the next session: what to keep, what to drop, and where things are.
---

# /session-handoff

Write a handoff for the next session to `tmp/session-handoff.md`: what it must keep from
this one, what it can drop, and where things are. These are `/smart-compact`'s three parts,
Keep, Drop and Say where, and the handoff holds pointers, not copies: anything the next
session can read from a file is named by its path, never restated.

This file is meant to work as plain text too, followed by a session whose plugin does not
have the command yet. So it takes no arguments, names no plugin path and needs no granted
tools. If the user said what the handoff is for, take that from the conversation.

**Run every command alone**: one `Bash` call per command, never chained with `&&`, `;` or
a pipe, so each one's failure is seen. Run `git` in the repository as `git <subcommand>`,
never `git -C <path>`: a permission matches the plain form only, so `git -C <path> status`
is refused where `git status` is granted.

## 1. Put on disk what belongs there

A handoff carries only what has no home on disk. Look through the session for work that
the plan does not record yet: a question answered but not logged as `> **Q:**` and
`> **A:**`, a finding not written as a `> **Note:**`, a subgoal finished but not flipped.
A standing rule the user gave belongs in memory or the project's instruction file. Propose
each edit, and make it only once the user confirms. What is left goes in the handoff.

## 2. Gather

- **Branch and state.** Run `git branch --show-current`, then `git status --short`, then
  `git log --oneline -1`.
- **The plan.** Take it from the latest `locate-plan.sh` report in this session, which
  `/hitl-step` and `/step` print in their Step 1: `plan:`, `next:` and `goal-file:`, and
  the open subgoals from that report or a later `check-plan-index.sh` report. The revision
  is the plan's `**Revision**:` line. If no such report is in the session, do not search
  for the plan: write the branch, and the plan's name, which is the branch with each `/`
  replaced by `-`, and say that `/workflow-coding:hitl-step` (or `/step`) resolves it.
- **In flight.** What no file holds: a question put to the user and not answered; a
  decision under discussion, with its options; a run or measurement under way, and where
  its output lands; the last tool error, if it is unresolved; each subagent that ran, with
  its result in one line; and what to do next, in order.

## 3. Draft

```markdown
# Session handoff — <branch>

**Written**: <YYYY-MM-DD>, at the end of <what the session was doing>.
**Read by**: the next session. Read this whole file before anything else, and say in a
few lines what you took from it.

## Keep

- Branch `<branch>` at `<short sha>`: <clean, or what is uncommitted>.
- Revision `<label>`; goal <NN> — <title>, `<goal-file>`, now `<marker>`.
- Open subgoals: <each, by its text>.
- Pending: <each unanswered question or confirmation, with its options>.
- <an unresolved tool error; a run under way; a subagent's one-line result>
- Do next, in order: <the steps>.

## Drop

<What the next session should not reload or re-derive: the contents of any file named
below, plans included; subagent reports in full; the bodies of commands already run; work
finished and recorded, in a commit, a merged PR or a `[x]`.>

## Where things are

- `<path>` — <what it holds, in a few words>
```

- **Keep** holds only facts no file holds. A fact a file holds goes under **Where things
  are**, as the path and a few words.
- Leave out a Keep line with nothing to say, rather than writing "none".
- Name the session's transcript in **Written** only if its path is in the conversation.

## 4. Write — CONFIRM FIRST

1. If `tmp/session-handoff.md` exists, the last handoff was never dealt with. Show it, and
   ask whether to replace it.
2. Run `git check-ignore tmp/session-handoff.md`. If it prints nothing, git does not
   ignore the file: say so, since a handoff is not meant to be committed, and ask before
   going on.
3. Show the draft, and write it to `tmp/session-handoff.md` once the user confirms. Do not
   commit it.

## 5. Report

- The path written, and its line count.
- How the next session finds it. It reads the handoff first only if the project's
  instruction file tells it to. If none does, say so, and suggest opening the next
  session with: "Read `tmp/session-handoff.md` before anything else."
