# docs/plan-notes-and-interop

**Created**: 2026-09-08
**Base**: main at 59661bc
**Status**: active

## Purpose

Carries this plugin's side of the `dp-compile` revision happening in a sibling repository.
Two unrelated kinds of change share one branch because that is what was decided for the
whole of that work: `workflow-claude`'s own convention routes everything through a PR, and
opening a revision was rejected because a revision's subgoals each spawn a branch, plural,
where this is one branch of documentation edits.

The first change is a real defect in `/hitl-step` and `/step`, found by using them: neither
command documents a way to record a **finding**. The vocabulary they define — `Q`, `A`,
`Blocked`, `Deferred`, `Descoped`, `Done`, `Commit`, `Ran`, `Result` — is entirely about
the state of a *task*, so an observation that is not a task has nowhere to go. In practice
`> **Note:**` is already used for this, including in this repository's own plans, and it is
written down nowhere.

The consequence is not cosmetic. With no category available, an agent reaches for a
checkbox, and a note wearing a checkbox is a promise that something will be done. Worse,
the usual survey of a plan is a top-level `grep -c '^- \[ \]'`, so an indented note is
*simultaneously* invisible to the count and alarming to a reader — it does not appear in
"12 of 31 done" and does appear as seven open items to anyone scrolling. That happened
across two sections of a live plan before anyone noticed.

## Scope

- `/hitl-step`: document `> **Note:**`; show it in the three-tier structure diagram; make
  Step 4's parent-state check mechanical rather than remembered; verify Step 6's
  section-completion claim at every indent.
- `/step`: the same note vocabulary, in its simpler single-tier form.
- `dp-compile` interoperation: a README "Companion plugins" section, conflict-report §4.4,
  and a `CLAUDE.md` section. **All documentation — no functional change was needed**, which
  is the finding rather than an omission. `dp-compile` detects this plugin by reading its
  own tool list, so the dependency runs one way and nothing here implements or maintains
  it. A detection contract was considered on that side and rejected: it would couple both
  plugins forever for a check one can make alone, and would assume hooks fire, which
  depends on the load path.

## Context

- Sibling work: the `dp-compile` plugin revision, planned outside this repository.
- The branch shape (one standalone branch, no revision) was settled there before any edit
  was made here.
- `/file-plans` will report `no backlink` for this plan, which is the designed safe
  outcome for a standalone branch rather than a defect.

## Notes

- Step 4 already forbade flipping a parent to `[x]` while a subgoal is `[ ]`, so the
  protocol was correct and the failure was that the protocol was not run. What the protocol
  lacked was the *category* whose absence produced the malformed lines in the first place.
- The one real coupling to `dp-compile` is **command names**. It names `/smart-commit`,
  `/new-branch`, `/hitl-step`, `/step`, `/smart-merge` and `/agents-docs-update` in its
  prose; renaming any of them breaks it silently, and no test here would notice. That is
  now in `CLAUDE.md` as a cross-repository rename hazard, and it is the opposite of the
  `commit-commands` case, where editing `hooks.json` obliges a conflict-report update in
  the same commit.
- The `awk` check now documented in Step 6 was run against a real plan before being
  written down: zero hits for two sections believed complete, 28 for sections genuinely
  open, and it catches a synthetic `[x]` parent hiding a `[ ]` subgoal that a top-level
  grep misses.
