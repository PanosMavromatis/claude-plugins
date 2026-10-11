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
- [ ] Add the one-step install line, and update the expected validate warnings
  - [ ] The plugin README gains the one-step `/plugin install` line
  - [ ] The plugin `CLAUDE.md`'s expected-validate-warnings entry drops the name warning
- [ ] Pass the suites and a full e2e run, then switch `settings.json` last
  - [ ] The six script suites pass, with the propose-revision and close-revision mutants
  - [ ] A full e2e run, run by the user, has 0 failing
  - [ ] No live `workflow-claude` reference remains outside the records
  - [ ] `.claude/settings.json` switches to `workflow-coding@mavromatis-ai-labs` in the last commit before the merge
