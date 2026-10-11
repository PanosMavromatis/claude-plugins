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
- [ ] Rename the plugin to `workflow-coding` and release `0.10.0`
  - [ ] Inventory every live reference, and separate it from the records that keep the old name
  - [ ] `git mv` the plugin directory; `plugin.json` (name, `version` `0.10.0`) and `marketplace.json`
  - [ ] Command and agent names, both READMEs and `CLAUDE.md`s, the hook messages
  - [ ] `dev/`: `build.py`'s plugin path, `check.py`, the `run.sh` prompts
- [ ] Move `dp-compile` to the new name and release `0.4.1`
  - [ ] `"dependencies"`, its `/workflow-claude:*` references, `commands/references/workflow-claude.md` → `workflow-coding.md`
- [ ] Add the one-step install line, and update the expected validate warnings
  - [ ] The plugin README gains the one-step `/plugin install` line
  - [ ] The plugin `CLAUDE.md`'s expected-validate-warnings entry drops the name warning
- [ ] Pass the suites and a full e2e run, then switch `settings.json` last
  - [ ] The six script suites pass, with the propose-revision and close-revision mutants
  - [ ] A full e2e run, run by the user, has 0 failing
  - [ ] No live `workflow-claude` reference remains outside the records
  - [ ] `.claude/settings.json` switches to `workflow-coding@mavromatis-ai-labs` in the last commit before the merge
