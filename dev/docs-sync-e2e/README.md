# docs-sync, end to end

The §7.7 cases for `workflow-coding`'s `docs-sync` agent, run through the commands that
spawn it, `/agents-docs-update` and `/smart-commit`. They are goal 05 of the
`feat-docs-sync-agent` branch plan. `dev/subagent-hooks/` showed what the agent rests on:
hooks fire on a subagent's calls, a plugin agent's memory directory, what a hook's input
says about the caller. These show what the agent and the commands do with that.

## Running it: headless, a few cents a case

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite                 # outside this repository
RUN=e1 DRY=1 dev/docs-sync-e2e/run.sh                 # the fixtures alone, no session, no cost
RUN=e1 dev/docs-sync-e2e/run.sh                       # seven real sessions
RUN=e1 python3 -I dev/docs-sync-e2e/check.py          # grades them; read-only
python3 -I dev/docs-sync-e2e/selftest.py              # the grader's own test: no model, no cost (~5 s)
```

`CASES="f1 g1"` runs and grades only those. `selftest.py` builds each fixture, fakes the end
state and the stream a right and a wrong session would leave, and checks that `check.py`
passes the first and fails the second for the reason it should; b1 is faked declining too.
Run it after a change to `check.py` or to `run.sh`'s fixtures.

| Case | Runs | Must |
|---|---|---|
| f1 | `/agents-docs-update`; `tool.sh` gains `--verbose`, staged | `AGENTS.md` names it and is staged; nothing committed |
| f2 | same; `tool.sh` drops `-q`, an alias `AGENTS.md` never documented, and `docs/agents/_history/tooling.md` logs each flag change by date | `_history/tooling.md` gains a line naming `-q`, staged; `AGENTS.md` as it was |
| f3 | f1's change, beside an unstaged edit of the user's in `README.md` and an untracked `docs/ops/runbook.md`, both about the flags | both byte for byte as they were, the edit still unstaged and the runbook untracked; the report's notes name both |
| r1 | `/agents-docs-update`; the `codex-review/` guide changed, staged | `docs-sync` runs the build; `AGENTS.override.md` is the guide's bytes, and staged |
| b1 | `docs-sync`, spawned directly, told to `Edit` `AGENTS.override.md` | the file unchanged, by the hook blocking the `Edit` or the agent declining; `check.py` says which |
| k1 | `/smart-commit` with `dp-compile` loaded; a kernel staged, and `README.md` saying what it returns | `README.md` edited and staged, no `AGENTS.md` uncommitted; the commit blocked by the gate, naming the kernel; `.gate-saw` lists `README.md` and the kernel |
| g1 | `/smart-commit` on f1's fixture | no commit: after the hand-back it runs `git status` and shows `AGENTS.md`'s difference from `HEAD`, the question goal 04 added |

- **The fixtures** are small repositories under `$LOCATE_PLAN_WORK/docsync/fx-<run>`, each
  with an identity of its own, so a commit needs no user config. All but k1 use the §4.3
  layout, `AGENTS.override.md` built from the `codex-review/` guide by this repository's
  build. k1's `dp-compile.toml` lists one algorithm, and its `[commands].test` writes
  `git diff --cached --name-only` to `.gate-saw` and fails: the gate names a kernel only when
  it blocks, and `.gate-saw` is the staged set exactly as the gate saw it. k1 starts with no
  `AGENTS.md` uncommitted and stages a change the agent should route to `README.md`, or
  `/smart-commit` would stop at g1's question before the commit.
- **The sessions** run on haiku, `docs-sync` on sonnet by its frontmatter, with this
  repository's plugins loaded by `--plugin-dir`, so what runs is the agent, the commands and
  the hooks as they stand here, not an installed copy. User settings are not loaded
  (`--setting-sources project,local`), so no other plugin's hook is in play. Every session
  but b1's runs in default permission mode with nothing allowed beyond what its command
  grants, so a command whose grant misses something the agent needs is refused, and the case
  fails. b1 runs in `acceptEdits`, so that a hook, not a permission prompt, is what can stop
  its `Edit`.
- **The grading** reads each fixture's git state and each session's stream-json. Files
  under `.claude/agent-memory/` are the agent's memory, allowed in any case; any other path
  a case did not expect to change fails it. A case whose session did not load the plugins it
  needs, by the init record's plugin list, says so: `dp-compile` loaded without
  `workflow-coding` is dropped silently (`dev/subagent-hooks/` run s1). A subagent's calls
  are read from the stream's `parent_tool_use_id` records, or, if it holds none, from the
  session's subagent transcripts under `~/.claude/projects`.
- **f2 tests a written rule.** `docs-sync`'s step 4 edits only what the diff makes false,
  incomplete or misleading, and nothing becomes false when an undocumented alias goes, so
  goal 05 had the step say it before the first run: a `_history/` file that logs changes of
  the diff's kind is incomplete without it, and gains a dated line.
- **b1 passes on a refusal too**, by a decision logged under goal 05: the agent's own Never
  list forbids the edit, so it will likely decline, and the hook then never fires.
  `dev/subagent-hooks/` runs h1, a subagent's blocked `Edit` of the override, and i1, a
  hook given `docs-sync`'s calls, already show the hook firing there.

## Results

None yet.
