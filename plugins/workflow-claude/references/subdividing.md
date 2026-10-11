# Subdividing a specification into a revision

`/master-plan` gives the `plan-drafter` agent a specification: a design document, pasted
prose, or notes from a conversation. The agent returns a draft revision master plan, which
the user reviews and edits before anything is written. This file holds the rules for that
draft and the reasons for them. The agent body summarises the rules; change them here.

## One subgoal is one branch

- **One subgoal is one branch, one PR, and one independently mergeable change**, with one
  acceptance check a reviewer can run. A subgoal that needs two PRs is two subgoals. Two
  subgoals that cannot merge apart are one.
- **Order by dependency, not by size.** A subgoal that builds on an earlier one names it
  ("builds on 2"). Nothing earlier may need something later.
- **Name what each subgoal touches**: paths, commands, files, modules. Then `/new-branch`'s
  Scope question is already answered when the branch opens.
- **Cross-cutting work is its own last subgoal**: a documentation sweep, the version bump
  and release, an evaluation run. Spread across every subgoal, it is done unevenly and
  reviewed nowhere.
- **More than about eight subgoals is two revisions.** Say so, and say where the split
  falls, in the draft's questions, rather than padding or compressing. This is advice,
  not a gate: the user decides.

## What is carried over, and what is not

- **Settled decisions are copied verbatim** into `## Settled decisions`, because a branch
  must not reopen them and `/hitl-step` has nothing else to point at. Copy the decision,
  not the debate: rejected alternatives stay in the spec. Write each decision as a plain
  `- ` bullet, never a checkbox, even if the spec has one: the plan scripts count every
  `- [ ] ` line at the left margin as a subgoal, whatever heading it sits under.
- **The preamble says why the revision exists and what it does not do**, in the spec's
  terms. Do not supply a motive the spec does not give.
- **Nothing is invented.** A subgoal, decision or version the spec does not support is a
  question for the user, not a guess in the draft.
- **Everything left out is listed, with the reason**: deferred to a later revision, already
  done, out of scope, or not plan material (background, measurements, rationale). A draft
  that silently drops part of a spec is the failure this list makes visible.
- **A previous revision is read for its header only**: its label, so the new ordinal
  follows it, and its `**Version**:`, so version numbers continue from it. Its subgoals
  are finished work, not input.

## The version field

`**Version**:` states the publishable numbers the revision delivers, one per package it
releases: `workflow-coding 1.0.0; dp-compile 0.5.0`. It is a statement, not tooling, and
nothing bumps a version from it. Take the numbers from the spec. If the spec names none
for a package it changes, write `—` and ask. A revision that releases nothing has `—`.

## The form

The draft is the whole of `docs/plan/<label>/_TODO.md`, or `_DO.md` in a project whose
master plan is `DO.md`. The form is the same for both:

~~~markdown
# Revision <label>

**Status**: open
**Version**: <package version; package version, or —>
**Opened**: <YYYY-MM-DD>
**Spec**: <a path, "pasted", or "conversation">

## Preamble

<why this revision exists, and what it does not do>

## Settled decisions

- <a decision, verbatim from the spec>

## Subgoals

- [ ] 1. <what the branch delivers>
  Scope: <what it touches, and what it builds on>. Acceptance: <the check a reviewer runs>.
- [ ] 2. <…>
~~~

- Every subgoal starts at `[ ]`. Later markers, `> **Branch:**` backlinks and
  `> **Done:**` lines are written by `/new-branch`, `/hitl-step` and `/smart-merge`. A
  draft never carries them.
- Subgoals are numbered `1.`, `2.`, … in dependency order. Numbers order subgoals but do
  not identify them, so a subgoal added later takes the next free number.
- The `Scope:` and `Acceptance:` line is indented two spaces, so it continues the item.
- `## Settled decisions` with no decisions says `none`. It is never left out: its absence
  would read as "nothing is settled" when the spec simply settled nothing.
