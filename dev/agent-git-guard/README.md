# guard-agent-git.py test suite

These are the tests for `plugins/workflow-coding/hooks/guard-agent-git.py`, the `PreToolUse`
hook on `Bash` that holds this plugin's agents to the few commands they need, and for
`hooks/fail-closed.sh`, the wrapper `hooks.json` runs it and `protect-agent-docs.py` through.
They live here, outside the plugin, so they don't ship with it. Both were settled in goal 03a
of the `feat-docs-sync-agent` branch plan.

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
python3 -I dev/agent-git-guard/suite.py            # 157 cases, twice under each python3 found (~20 s)
python3 -I dev/agent-git-guard/suite.py --mutants  # 85 mutants, every one must be caught (~2.5 min)
```

`-v` prints each case's stderr. `--hook PATH` tests another copy, with `fail-closed.sh` and
`hooks.json` beside it. `--mutants` runs the suite on each mutant once, under the first
`python3` found, up to its first failure. Every case runs `hooks.json`'s command for its
matcher under `/bin/sh`, as Claude Code does, so each goes through the wrapper.

- **The rule: an allowlist.** For a call whose `agent_type` starts with `workflow-coding:`,
  a Bash command passes only if it is one simple command and one of these:
  - `git status`, `diff`, `log`, `show`, `rev-parse` or `ls-files`, with no global option
    (`-c`, `-C`, `--git-dir`, `--work-tree`, `-p` and the rest: config is code, and the
    others move what `git add` stages) and none of `--output`, `--ext-diff` or
    `--textconv`, with which an allowed subcommand writes any file or runs a program;
  - `git add` of named files, each one a file the agents may write;
  - `gh pr list` or `gh pr view`;
  - the plugin's own `scripts/build-agents-md.sh`, beside the hook, by any path that
    resolves to it, with no arguments.

  Anything else is refused, exit 2, with a message naming what. Every call from the main
  session, or from another plugin's or the user's agent, passes.
- **One simple command** has none of `` ; & | < > ( ) { } $ ` \ * ? [ ~ `` or a newline, and
  nothing before its first word, which must be exactly `git`, `gh` or the build script: no
  assignment (`GIT_DIR=`, `GIT_CONFIG_COUNT=`, `PAGER=`), no wrapper (`env`, `timeout`,
  `sudo`), no path (`/usr/bin/git`) and no other case (`GIT`, which runs git on macOS's
  case-insensitive filesystem). Globs are refused because bash expands them before git sees
  them, and `~` because `~+` is the working directory.
- **Why an allowlist.** The first version parsed each command to find the `git` in it, as
  `dp-compile`'s gate does. Security reviews of its commit and push, and the
  `plugin-dev:plugin-validator` agent, gave 43 shapes bash runs as git; after a round of
  hardening, 28 still passed: wrappers and their options, shell keywords and braces,
  environment variables that set config, `GIT`, `cd` before `git add`, a shell reading
  stdin. Each fix left the next. The allowlist refuses what it does not know, which also
  stops the agent running a script it has written.
- **`git add` must name files.** An option such as `-A`, `-u`, `--all` or `-p`, no path, a
  magic pathspec (`:/`) or a directory under the call's `cwd` is refused: each would stage
  what the agent did not edit, the user's unstaged work among it, for `/smart-commit` to
  commit and push. Git reads `..` as text, so `AGENTS.md/..` and `nowhere/..` are `.`, and
  `docs/x.md/..` is `docs`, though `os.path.isdir` says none is a directory; each stages the
  user's files, so a path is normalised before the check. Each must then be a file the
  agent may write, by `protect-agent-docs.py`'s rule: Markdown, never `CLAUDE.md` or
  `CLAUDE.local.md`, under `.claude/` only its own memory. A name is read as a Windows
  filesystem reads it, so `CLAUDE.md.` and `src/app.py:x.md` are refused; `.claude`'s 8.3
  name, `CLAUDE~1`, never reaches the rule, since `~` is shell syntax. The older checks still
  matter for Markdown paths: an exclusion alone, `:!docs/x.md`, stages everything else, and
  a directory may be named `dir.md`.
- **The seam.** `WORKFLOW_CODING_GUARDED_AGENTS`, a comma-separated list of agent types,
  replaces the set guarded, so a headless case can guard a `general-purpose` stand-in, which
  will try a commit when told to, where `docs-sync` refuses by its instructions.
- **The wrapper fails closed.** Claude Code blocks a call only when a hook exits 2; any other
  status is a non-blocking error and the call runs, so a hook that crashed, or whose
  `python3` could not start (127), would let every call through. `fail-closed.sh` passes a
  hook's exits 0 and 2 through, and on any other refuses the call if its input names a
  guarded agent: an `agent_type` starting `workflow-coding:`, or any while the seam is set.
  The main session's calls get the hook's own status back. It matches the input with
  `grep`, since `python3` may be what failed, and refuses if `grep` fails too.
- **The cases.** `g` what the agents may run, `docs-sync`'s own commands first, and the build
  script by its path, through a symlink and relative to the input's `cwd`; `r` what they may
  not: subcommands off the list, every kind of global option, the options that write or run,
  every `git add` that stages more than named files or a file the agents may not write,
  `CLAUDE.md`, code, `.claude/` and another agent's memory among them, each shell character
  where it comes
  first, and every first word but the three, among them the reviews' and the validator's
  examples; `o` the calls left alone; `s` the seam; `e` malformed input, a JSON value that
  is not an object included; `m` the message in full; `w` the wrapper, with a `python3` that
  cannot start or a `grep` that fails first on `PATH`, or a hook that crashes, for this
  plugin's agent, the main session, another agent and the seam, the input as compact JSON
  too, a command that only mentions `"agent_type"`, and `hooks.json`'s command for
  `Write|Edit|MultiEdit`. The input's `cwd` is a working tree
  with a `docs/` directory, while the hook runs elsewhere, so a hook judging directories by
  its own working directory fails.
- **What it does not guard.** What the user's own shell or git config makes of `git`, an
  alias or a function. The agents' `Write` and `Edit` are `protect-agent-docs.py`'s, which
  holds them to documentation and out of `.git/` (`dev/agents-docs/`).
- **The headless case** is in `dev/grant-lifetime/`: under `/grant-probe:spawn`, with the
  seam naming `general-purpose`, the stand-in's `git commit` must be refused by this hook,
  and `/grant-probe:direct`'s commit must land. Its check looks for the message's
  "may not run \`", which every refusal keeps.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the plugin's `hooks/`. Each patch names its file relative to
  the plugin's root: `gg01`–`gg57` and `gg74`–`gg85` the hook, `gg58`–`gg71` the wrapper,
  `gg72` and `gg73` `hooks.json`. A patch that no longer applies is reported as `STALE`. A mutant must be caught by the
  rule it breaks, not by a crash it causes on the way: check the `FAIL` line each one prints.
  Each shell character has its own mutant, caught by the case where it comes first.
