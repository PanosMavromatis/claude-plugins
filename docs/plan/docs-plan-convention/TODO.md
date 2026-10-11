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
- [ ] Rewrite the README: "What's in here" with `agents/` and `references/`, `/master-plan` in the loop diagram, and the lifecycle without `/file-plans`
- [ ] `/new-branch`: drop "always flat", settle the branch-doc path, add an `argument-hint`
- [ ] Check the rewritten prose against the commands and scripts it describes
