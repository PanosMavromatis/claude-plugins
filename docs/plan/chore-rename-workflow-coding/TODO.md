# chore/rename-workflow-coding

**Status**: active
**Created**: 2026-10-11
**Subgoal**: revision 06-subagent-refactor-R1 — rename `workflow-claude` to `workflow-coding`, and release `0.10.0` in the same PR

## Tasks

- [x] Ignore Python bytecode repo-wide, as its own commit
  > **Note:** An oversight, not a choice: `2670b6f` (2026-10-08) consolidated the plugin
  > `.gitignore`s into the root but kept the bytecode rules in `dp-compile`, whose hook was
  > then the only Python. The repo now tracks Python in `plugins/workflow-claude/hooks/` and
  > 13 files under `dev/`. It went unseen because `python3 -I x.py` caches only imported
  > modules, and no `dev/` script imports another: the one stray cache came from a `py_compile`.
  - [x] `__pycache__/` and `*.py[cod]` move to the root `.gitignore`; `plugins/dp-compile/.gitignore` is removed
    > **Result:** `git check-ignore -v` matches `.gitignore:29` for bytecode under `dev/` and
    > `plugins/dp-compile/`; nothing referenced the removed file.
- [x] Rename the plugin to `workflow-coding` and release `0.10.0`
  > **Q:** `docs/plan/workflow-claude/`, the plugin's archived history that the root plan's
  > Closed revisions and the propose-revision fixture point into: rename it, or keep it?
  > **A:** Keep the name. It records the plugin under the name it had, and no pointer moves.
  > **Q:** `_meta/plugin-conflict-report.md` (dated 2026-06-25, 40 references, quotes the old
  > hook source): rewrite it, or treat it as a record?
  > **A:** A record, with one note under its header saying the plugin was renamed
  > `workflow-coding` at 0.10.0 and the report predates it.
  > **Q:** `dev/locate-plan/trial/`, the finished 246-session trial: leave it, or update it?
  > **A:** Update its scripts' paths and prompts so it would still run; leave
  > `trial-evidence.json` untouched as data.
  > **Q:** Should the live docs mention the old name?
  > **A:** Yes: one line each in the plugin README and the root README, "Renamed from
  > `workflow-claude` at 0.10.0." The final reference check allows exactly those.
  - [x] Inventory every live reference, and separate it from the records that keep the old name
    > **Note:** Measured 2026-10-11: 68 files and 280 lines name `workflow-claude`, plus the
    > 34 paths under the plugin directory; no spelling variants. Live: the plugin (13 files,
    > 40 lines, without the `_meta` report), `dp-compile` (15 files, 56 lines, plus renaming
    > `references/workflow-claude.md`), `dev/` (23 files, 60 lines, less two record lines:
    > `trial-evidence.json:8503` and the fixture at `propose-revision/suite.py:60`),
    > `marketplace.json` and the root README (11 lines), and `.claude/settings.json`, which
    > goes last. Records: `docs/plan/**` and the conflict report. Three things break with no
    > error message if missed: the `Skill(workflow-claude:…)` grants in `allowed-tools`;
    > `dp-compile`'s presence check, which looks for the `workflow-claude:` namespace in its
    > tool list; and the hashed `p/<hash>/workflow-claude` paths, which must agree across
    > `build.py`, `check.py` and `run.sh`, and across the trial's three scripts.
  - [x] `git mv` the plugin directory; `plugin.json` (name, `version` `0.10.0`) and `marketplace.json`
    > **Note:** `marketplace.json` also names the plugin in `dp-compile`'s description ("depends
    > on workflow-claude"), so that line moved here rather than in the `dp-compile` goal.
  - [x] Command and agent names, both READMEs and `CLAUDE.md`s, the hook messages
    > **Result:** 51 references in 13 files, by a substitution that skips the record path
    > `docs/plan/workflow-claude/` (kept at `CLAUDE.md:80`); the "Renamed from" lines and the
    > conflict report's note added. The hook parses, and run where `commit-commands` is enabled
    > it names `workflow-coding` in both `systemMessage` and `additionalContext`.
  - [x] `dev/`: `build.py`'s plugin path, `check.py`, the `run.sh` prompts
    > **Result:** 59 references in 22 files, `trial-evidence.json` excluded. The six suites pass
    > at their full counts (83, 39, 32, 37, 72, 58); the harness and trial scripts parse
    > (`ast`, `bash -n`); the doc-reference check finds 0 problems. What remains is
    > `dp-compile`, `.claude/settings.json`, and the kept records and lines.
- [x] Move `dp-compile` to the new name and release `0.4.1`
  > **Q:** Should `dp-compile` 0.4.1's presence check also accept the old `workflow-claude:`
  > namespace during the transition, until R5 migrates the consumers?
  > **A:** No, the one new name. Accepting both would hide a half-migrated consumer that
  > loads both plugins.
  > **Note:** So a consumer updates `dp-compile` to 0.4.1 only as part of migrating to
  > `workflow-coding` (R5, `tmp/plugin-migration-runbook.md`). Updated alone, beside an
  > installed `workflow-claude` 0.9.0, its dependency pulls in `workflow-coding` and every
  > command loads twice under two namespaces.
  - [x] `"dependencies"`, its `/workflow-claude:*` references, `commands/references/workflow-claude.md` → `workflow-coding.md`
    > **Result:** 58 references in 15 files after a `git mv` of the reference file; `version`
    > `0.4.1`, in `plugin.json` and the example manifest at `CLAUDE.md:101`. All 13
    > `@references/` imports resolve, the smoke test's 22 expected paths exist, the
    > dependency is listed in `marketplace.json`, and no old name is left in `dp-compile`.
- [x] Add the one-step install line, and update the expected validate warnings
  > **Note:** "One step" is the validator's own template, from its 2026-10-08 advice:
  > `/plugin install <name> --marketplace <owner>/<repo>`, on Claude Code 2.1.275 or later. The
  > same run gave `dp-compile`'s README the same advice, which nothing had tracked.
  > **Q:** Should `dp-compile`'s README get the matching line in this goal, since it is in
  > this PR at 0.4.1 anyway?
  > **A:** Yes.
  - [x] The plugin README gains the one-step `/plugin install` line
    > **Result:** `/plugin install workflow-coding --marketplace PanosMavromatis/claude-plugins`,
    > after the two-step CLI form; and `dp-compile`'s README gains
    > `/plugin install dp-compile --marketplace PanosMavromatis/claude-plugins`, which brings
    > `workflow-coding` as its dependency.
  - [x] The plugin `CLAUDE.md`'s expected-validate-warnings entry drops the name warning
    > **Result:** The user ran `claude plugin validate` on both plugins, 2026-10-11.
    > `workflow-coding`: one warning, the plugin-root `CLAUDE.md`; the name warning and the
    > install advice are gone, and the entry now says one. `dp-compile`: four warnings, the
    > root `CLAUDE.md` and the three `commands/references/` fragments without frontmatter,
    > exactly the four its `CLAUDE.md:117` already expects; its install advice is gone too.
    > **Note:** `dp-compile`'s `CLAUDE.md:119` still says "the repo root and the plugin root
    > are the same directory", untrue since it joined the marketplace as `plugins/dp-compile/`;
    > its conclusion holds. Left for the R2 handoff, as outside the rename.
- [x] Pass the suites and a full e2e run, then switch `settings.json` last
  > **Q:** r8 has 2 failing checks, both "no permission denials" and neither from the rename;
  > a rerun of e5 and m2 (r8b) clears e5 but m2 is denied a different call. How should the
  > e2e subgoal close?
  > **A:** Accept, and note it for R2 where `/master-plan` is next exercised: a sub-bullet
  > under R2 step 0 in `tmp/subagent-refactor-plan.md`.
  - [x] The six script suites pass, with the propose-revision and close-revision mutants
    > **Result:** All six at their full counts from the renamed tree (83, 39, 32, 37, 72, 58
    > passing), and every mutant killed: propose-revision 36 of 36, close-revision 40 of 40.
    > Run back to back, the two mutant suites exceed a 600 s tool timeout; run them alone.
  - [x] A full e2e run, run by the user, has 0 failing
    > **Result:** r8, all 10 scenarios and 16 sessions, $6.71 (the estimate from r6 + r7
    > was $6.80): every functional check passes; 2 fail "no permission denials", e5 and m2,
    > each a `git -C <cwd>` call that `allowed-tools` prefixes cannot match. r8b, e5 and m2
    > alone, $0.88: e5 passes clean; m2 is denied a shell `grep` at an invented
    > `skills/master-plan/references/` path, its main session checking the drafter's draft.
    > Neither traces to the rename: `hitl-step.md` is a pure rename, and `master-plan.md`'s
    > one changed line, the drafter's `subagent_type`, is what m1 checks and passes. m2's
    > denials (0 in r6, 1 in r8, 1 in r8b) go to R2 step 0.
  - [x] No live `workflow-claude` reference remains outside the records
    > **Result:** Rerun after the `settings.json` switch, `git grep workflow-claude` outside
    > `docs/plan/` and `docs/git/` finds only the allowed: the two "Renamed from" lines
    > (`README.md:17`, the plugin README's line 5), the record path at `CLAUDE.md:80` and in
    > the fixture `propose-revision/suite.py:60`, `trial-evidence.json:8503`, and the
    > conflict report's 40.
  - [x] `.claude/settings.json` switches to `workflow-coding@mavromatis-ai-labs` in the last commit before the merge
