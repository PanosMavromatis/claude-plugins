# agents-docs test suite

These are the tests for the agent-docs pair in `plugins/workflow-coding/`:

- `scripts/build-agents-md.sh`, which builds each `AGENTS.override.md` from the Codex
  reviewer's guide;
- `scripts/check-agents-md.sh`, which checks the pair is in sync and lints the hand-authored
  `AGENTS.md` files;
- `hooks/protect-agent-docs.py`, which blocks a direct edit of a generated
  `AGENTS.override.md`.

They live here, outside the plugin, so they don't ship with it. The behaviour they test is
R2 subgoal 7's, settled in goals 01–03 of the `refactor-agents-override-pair` branch plan,
and the suite's shape in its goal 04. The check runs the build it sits beside, so the suite
tests the three together: run it after a change to any of them.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/lp-suite          # outside this repository, as dev/locate-plan/ requires
python3 -I dev/agents-docs/suite.py            # 43 cases, twice under each Bash or python3 found (~20 s)
python3 -I dev/agents-docs/suite.py --mutants  # 45 mutants, every one must be caught (~3 min)
```

`--mutants` runs the suite on each mutant once, under the first shell and `python3` found,
and stops it at its first failure (`--first`): a mutant needs only one. Run whole, the 45
took 15 minutes; stopped at the first, 3.

`-v` prints each output. `--plugin PATH` tests another copy, which must hold `scripts/` and
`hooks/` as the plugin does. `/opt/homebrew/bin/bash` and `/opt/homebrew/bin/python3` are
skipped if absent. Only BSD userland has been tested: `ad12-wc-padded` is caught because BSD
`wc` pads its count, so on GNU it would survive.

- **The fixtures** are ten small repositories under `$LOCATE_PLAN_WORK/ad`, rebuilt on every
  run.
  - `pair`: the §4.3 layout, with guides for the root, `ui` and `a/b`, the pair committed in
    sync, and hand-authored `AGENTS.md` and `CLAUDE.md` files. Beside the guides are
    directories that build nothing: `plan/`, `kernel/`, `ui/plan/`, `svc/docs-sync/`, a
    `svc/codex-review/` with no guide, and `old/codex-review-v1/`.
  - `new`, `drift` and `missing`: the same with no pair yet, with `ui`'s edited by hand,
    and with the root's and `ui`'s absent.
  - `lints`: a root `AGENTS.md` of 201 lines with no final newline and seven dated lines,
    among near misses (`1999-12-31`, `2026-10`, `2026/10/14`); `ops/AGENTS.md` with exactly
    five; and an untracked `svc/AGENTS.md`. To be ignored: a gitignored `vendor/AGENTS.md`,
    dated guides, `ui/MY-AGENTS.md`, and a tracked `old/AGENTS.md` deleted from the
    working tree.
  - `at200`: a root `AGENTS.md` of exactly 200 lines, and one warning elsewhere.
  - `mixed`: the pair beside dispatcher-layout sources; `dispatcher`: those sources alone;
    `empty`: `docs/agents/` with no guide; `nodocs`: no `docs/agents/`.
- **A build** runs on a fresh copy of its fixture, `$LOCATE_PLAN_WORK/ad-run`. It must
  print a `wrote` line for each guide in order, leave each `AGENTS.override.md` as the
  header and its guide's bytes, and change no other file; a second run must print the same
  and change nothing. With `DST_DIR` set, the tree must not change at all.
- **A check** is graded on its exit status, the exact `warning:` lines, its drift and
  missing lines, and its last line. It must leave the fixture untouched and remove its
  temporary directory. A `mktemp` first on `PATH` logs each directory it makes: macOS's
  `mktemp` prefers `_CS_DARWIN_USER_TEMP_DIR` to `TMPDIR`, so an empty `TMPDIR` proves
  nothing there.
- **The hook** gets JSON on stdin, run as `hooks.json` runs it, the file itself by its
  shebang, with `CLAUDE_PROJECT_DIR` set and the working directory outside the project,
  except in `h21`, which unsets it. It is graded on its exit status and its exact stderr,
  and must print nothing on stdout.
- **Every run is repeated**: twice under each Bash for the scripts, and twice under each
  `python3` for the hook. Each is put first on `PATH`, so the check's call to the build
  and the hook's shebang find it, and every run must print the same thing.
- **The static checks** look for Bash 3.2 hazards in the two scripts: Bash 4 features,
  `grep \|`, and heredocs or here-strings. Unlike the plan scripts' suites, they allow
  `mktemp` and redirects, which the build and the check use by design.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the two scripts and the hook. Each patch names its file
  relative to the plugin's root. A patch that no longer applies is reported as `STALE`.
  Re-anchor it, or drop it if its rule has gone. A mutant must be caught by the rule it
  breaks, not by a crash it causes on the way: check the `FAIL` line each one prints.
  `ad33-temp-left` is caught only by the `mktemp` log, which is what it is for.

`c08` pins one behaviour that may change. In the mixed layout the check passes the build's
warnings about dispatcher-layout sources through on stderr, but counts only its own lints,
so its last line reads "in sync" with no count. `/agents-docs-migrate`, R2 subgoal 9,
removes those sources; if the count should include them, change the case with the script.
