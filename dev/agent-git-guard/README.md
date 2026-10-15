# guard-agent-git.py test suite

These are the tests for `plugins/workflow-coding/hooks/guard-agent-git.py`, the `PreToolUse`
hook on `Bash` that keeps this plugin's agents to the `git` and `gh` subcommands they need.
They live here, outside the plugin, so they don't ship with it. The hook was settled in goal
03a of the `feat-docs-sync-agent` branch plan.

Why it exists: a command's `allowed-tools` grant reaches every agent it spawns
(`dev/grant-lifetime/` run `a1`), so under `/smart-commit`, which grants `git commit`,
`git push` and `git tag`, an agent such as `docs-sync` could commit, push or tag with only
its instructions to stop it. A call carries the calling agent's `agent_type` in the hook's
input, a plugin agent's being its namespaced name (`dev/subagent-hooks/` run `i1`), and the
main session's none, so the hook can refuse this plugin's agents and leave the main session
alone.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite              # outside this repository
python3 -I dev/agent-git-guard/suite.py            # 76 cases, twice under each python3 found (~10 s)
python3 -I dev/agent-git-guard/suite.py --mutants  # 33 mutants, every one must be caught (~1 min)
```

`-v` prints each case's stderr. `--hook PATH` tests another copy. `--mutants` runs the
suite on each mutant once, under the first `python3` found, up to its first failure.

- **The rule.** For a call whose `agent_type` starts with `workflow-coding:`, `git` may run
  only `status`, `diff`, `add`, `log`, `show`, `rev-parse` and `ls-files`, and `gh` only
  `pr list` and `pr view`; any other `git` or `gh` subcommand is refused, exit 2, with a
  message naming it. Everything else in Bash passes, and so does every call from the main
  session or from another plugin's or the user's agent.
- **`git add` must name files.** An option such as `-A`, `-u`, `--all` or `-p`, no path,
  `.`, a glob, a magic pathspec (`:/`) or a directory under the call's `cwd` (or its
  `git -C` path) is refused: each would stage what the agent did not edit, the user's
  unstaged work among it, for `/smart-commit` to commit and push.
- **The seam.** `WORKFLOW_CODING_GUARDED_AGENTS`, a comma-separated list of agent types,
  replaces the set guarded, so a headless case can guard a `general-purpose` stand-in, which
  will try a commit when told to, where `docs-sync` refuses by its instructions.
- **The cases.** `g` what the agents may run, the build script and `find` included; `r` what
  they may not, among them `git -C <path> commit`, `GIT_DIR=. git commit`, `env -i git push`,
  `/usr/bin/git commit`, a commit after `&&`, `;`, `|`, `&` or a newline, `bash -c '…'` and
  `( … )`, and every `git add` that stages more than named files; `o` the calls left alone;
  `s` the seam; `e` malformed input; `m` the message in full. The input's `cwd` is a working
  tree with a `docs/` directory, while the hook runs elsewhere, so a hook judging directories
  by its own working directory fails.
- **What it does not guard.** A git call hidden in an alias, a script or `eval` passes: the
  hook guards against an agent's mistake, not its evasion.
- **The headless case** is in `dev/grant-lifetime/`: under `/grant-probe:spawn`, with the
  seam naming `general-purpose`, the stand-in's `git commit` must be refused by this hook,
  and `/grant-probe:direct`'s commit must land.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the hook. Each patch names its file relative to the plugin's
  root. A patch that no longer applies is reported as `STALE`. A mutant must be caught by the
  rule it breaks, not by a crash it causes on the way: check the `FAIL` line each one prints.
