# docs/plan-convention

**Status**: active
**Created**: 2026-10-11
**Subgoal**: revision 06-subagent-refactor-R1 — rewrite the plan-convention sections of the plugin's `CLAUDE.md` and README

## Tasks

- [x] Re-locate each drift item in today's files, and verify the claims before rewording
  > **Note:** The drift list, at the line numbers of `88bd365` (★ = not on the master-plan list).
  > `CLAUDE.md`: 3, 5, 7 ★ "this repository" and "What this repo is" describe a standalone
  > repo, and "every artifact is a Markdown command"; 15 "restricts"; 27-35, 41-42, 55-81
  > `/open-revision` writing a section, `/file-plans` and the filing sweep, the cut into
  > `_DO.md`, "run `/file-plans` first"; 36, 53, 85 "always flat"; 91 `locate-plan.sh` serves
  > only the step commands (also `/smart-merge` and `/master-plan` now); 103, 201 the stamp's
  > readers name `/file-plans`; 107, 113 `Grep` lookups and "`Grep` is allow-listed";
  > 113 the split paragraph; 158, 160 ★ "loaded … via `claude --plugin-dir`" and the hook's
  > firing "signals a `--plugin-dir` launch", which a marketplace install also fires (the
  > hook's docstring, `remind-disable-commit-commands.py:7-8`, says the same); 202 "Six
  > commands", where nine run a bundled script (`agents-docs-build`, `agents-docs-check`,
  > `new-branch`, `step`, `hitl-step`, `smart-merge`, `master-plan`, `close-revision`, and
  > `open-revision` through its alias); ★ nowhere describes the revisions index, a revision's
  > `_TODO.md`, the per-goal layout or `check-plan-index.sh`. README: 7-9 no `agents/` or
  > `references/`, `locate-plan.sh` for the step commands only; 140-172 the `/open-revision`
  > lifecycle, a loop diagram without `/master-plan`, the filing sweep; 176 "always flat; the
  > filing sweep moves it"; 212-220 the close into `_DO.md`, "Run `/file-plans` first";
  > 229 `Grep`; 230 `docs/git/<branch>.md`. `new-branch.md`: no `argument-hint`.
  > **Note:** `claude plugin validate plugins/workflow-claude` passes with two warnings and one
  > advice. The name "reads as one of Anthropic's own": the rename subgoal answers it. A
  > plugin-root `CLAUDE.md` "is not loaded as project context": expected, since it guides
  > work on the plugin here, where a nested `CLAUDE.md` loads; agreed-plan §4.3 replaces it.
  > No line installs the plugin: one does, at README 32-33, in the CLI form and wrapped, so
  > a line match misses it; the one-step `/plugin install` line waits for the rename, which
  > changes the name in it.
  - [x] Whether `allowed-tools` grants or restricts, from the Claude Code docs
    > **Note:** It grants. The skills docs: "grants permission for the listed tools during the
    > turn that invokes the skill … It does not restrict which tools are available: every tool
    > remains callable, and your permission settings still govern tools that are not listed."
    > Command files take the same frontmatter. Deny and ask rules still override it.
    > **Note:** The grant also "clears when you send your next message". A command's writes
    > that follow a confirmation reply run in a later turn, outside it, which would explain
    > prompts on writes a command allow-lists, and means omitting a destructive verb gates
    > less than `CLAUDE.md:205` says. Documented, not measured here: for the R2 list, not
    > this rewrite.
  - [x] The branch-doc path: `docs/git/<flattened>.md` as practised, or `docs/git/<branch>.md` as the e2e has it
    > **Note:** `new-branch.md:81` and `smart-merge.md:52,129` say `docs/git/<branch-name>.md`,
    > which reads as nested, and the e2e (`check.py:137`) expects nested and passes. This
    > repository has 6 nested docs, the earliest, and 19 flattened (`git log --full-history`;
    > without it, history simplification hides every merged branch's doc).
    > **Q:** Which branch-doc path should the commands, e2e and docs settle on?
    > **A:** Flattened, `docs/git/<flattened>.md`, like the plan directory. `/new-branch` and
    > `/smart-merge` say so explicitly, `/smart-merge` also checks the nested path so an
    > in-flight branch still finds its doc, and `check.py` moves to the flattened name.
- [x] Rewrite the plan-convention, lifecycle and artifact sections of `plugins/workflow-claude/CLAUDE.md`
  > **Done:** The plan convention now describes the revisions and legacy layouts and per-goal
  > branch plans; the lifecycle runs `/master-plan` → `/close-revision` (stamp or extract),
  > with `/file-plans` gone and filing folded into the legacy close; `allowed-tools` grants;
  > lookups go through the scripts; the script-backed commands are named, not counted. The
  > hook's docstring no longer ties its firing to `--plugin-dir`.
  > **Note:** Every new claim was checked against today's files: placement in
  > `propose-branch-plan.sh`'s header, the archive's `_$MODEL` name in `close-revision.sh:173`,
  > all six plan scripts sourcing `lib/plan-rules.sh`, each with a suite in `dev/`, and the
  > library's anchored backlink match (`plan-rules.sh:385`).
  - [x] "Do not reintroduce the split" gains the §4.2 distinction: a revision's file is located, not read whole, and a goal file is read whole because it is the unit
- [x] Rewrite the README: "What's in here" with `agents/` and `references/`, `/master-plan` in the loop diagram, and the lifecycle without `/file-plans`
  > **Done:** "What's in here" lists `agents/` and `references/` and says which command runs
  > each plan script; the lifecycle opens with `/master-plan` and closes by stamp or
  > extraction, in the same diagram as `CLAUDE.md`; "The filing sweep" became "Where plans
  > live", with an example revisions tree and the legacy close's filing; the branch doc is
  > the flattened name, and lookups go through the scripts.
- [x] `/new-branch`: drop "always flat", settle the branch-doc path, add an `argument-hint`
  > **Done:** The branch doc is `docs/git/<flattened-branch>.md` in `/new-branch` (steps 6, 8,
  > 9) and `/smart-merge`, whose step 2 falls back to the unflattened path earlier versions
  > wrote and step 4 removes whichever it found; `check.py` expects the flattened name; and
  > `/new-branch` has `argument-hint: "[<type>/<slug>] [purpose]"`.
  > **Note:** "Always flat" was already gone from `new-branch.md`: `feat-per-goal-layout`
  > rewrote that paragraph (line 111) when the revision directory became a placement; only
  > the docs still said it, fixed in goals 2 and 3.
- [x] Check the rewritten prose against the commands and scripts it describes
  > **Note:** Form checks pass. The Step 1 lockstep `sed` diff from `CLAUDE.md` is empty over 65
  > extracted lines. A reference check (scratchpad `check_refs.py`) finds every `/command`,
  > script and plugin path the two docs name, and reports all three faults planted in a
  > scratch copy (a removed command, a missing script, an unknown command).
  > **Note:** A sonnet reviewer ran the scripts on fixtures against every added claim and found
  > none false; of its four overstatements, three were right (a standalone branch under an
  > index goes flat, so "its subgoals' branch plans"; the drafter reads the root plan whole,
  > so "no command reads … whole to find its line"; "the plan scripts are read-only") and
  > one half right: the 1.x promise is sourced, at `docs/plan/TODO.md:23`, but the plugin did
  > not say whose decision it is, so it now cites it.
  > **Note:** The root README's line 91 said each plugin's `CLAUDE.md` lists the validate
  > warnings it expects; `dp-compile`'s did (lines 117-118), this one did not. It now has the
  > entry, from the goal 1 run.
  > **Q:** Re-run the per-goal e2e before merge, to confirm a real `/new-branch` writes
  > `docs/git/<flattened>.md` and `/smart-merge` removes it?
  > **A:** Yes, before merge.
  - [x] The per-goal e2e passes on this branch's plugin (the user runs `run.sh`)
    > **Result:** Run `r7` (`LOCATE_PLAN_WORK=/tmp/lp-suite`, scenarios e1, e3, e4, e5, from
    > the working tree with goal 5's rewordings uncommitted): every check passed, 0 failing,
    > 10 sessions, $4.42. `/new-branch` wrote `docs/git/feat-plan-dirs.md` and `/smart-merge`
    > deleted that path, seen in the `r1m` fixture's log, not only in `check.py`. Each merge's
    > one denial is the documented `rm /tmp/pr-body-<branch>.md` gate.
