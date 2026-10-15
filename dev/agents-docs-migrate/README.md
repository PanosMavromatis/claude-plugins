# migrate-agents-docs.py test suite

These are the tests for `plugins/workflow-coding/scripts/migrate-agents-docs.py`, the script
behind `/agents-docs-migrate`: it finds what a repository's agent instructions are, checks
`docs-classifier`'s table, moves each row's lines, and checks the moves before anything is
deleted. They live here, outside the plugin, so they don't ship with it. Its design was settled
in goal 02 of the `feat-agents-docs-migrate` branch plan, where each decision is logged.

So far the suite covers the two read-only modes: `detect`, which finds the targets and their
state, and `check`, which checks the table and reports what `apply` would write.

## Running it: no model, no cost

```bash
export LOCATE_PLAN_WORK=/tmp/adm-suite                  # outside this repository: each fixture is a git repository
python3 -I dev/agents-docs-migrate/suite.py             # 45 cases, twice under each python3 found
python3 -I dev/agents-docs-migrate/suite.py --mutants   # 57 mutants, every one must be caught
```

`-v` prints each report. `--plugin PATH` tests the script under another plugin root.
`/opt/homebrew/bin/python3` is skipped if absent.

- **The fixtures** are small repositories under `$LOCATE_PLAN_WORK/adm`, rebuilt on every
  run, mostly untracked, since `detect` reads git's list of tracked and untracked files:
  - one per state and kind: a legacy `CLAUDE.md`; the dispatcher layout, with its generated
    `AGENTS.md`; migrated, with no `CLAUDE.md`, the `@AGENTS.md` shim or `@./AGENTS.md`;
  - sizes at each side of the marks, 200 and 201 lines, ≈5,000 and ≈5,001 tokens;
  - what is not a target: no instructions at all, and a `CLAUDE.md` of comments alone;
  - what is odd but safe: a dispatcher `CLAUDE.md` with no sources, and a generated
    `AGENTS.md` whose sources are gone;
  - what stops a migration: prose beside the dispatcher's sources, and a `codex.md` beside the
    `codex-review/AGENTS.md` it would become;
  - `monorepo`, partly committed: a dispatcher root, a dispatcher component two levels down,
    a migrated component and a legacy one, with guides and `_history/` to be ignored, and
    `codex-only`, a component found only by its `docs/agents/` source;
  - `local`, whose `CLAUDE.local.md` files are gitignored, as they usually are, and must still
    be reported, and `ignored`, whose vendored `CLAUDE.md` must not be a target.

  Three cases run where `detect` must refuse: from a subdirectory, outside any repository, and
  with no mode.
- **`check`'s fixtures** each come with a `docs-classifier` reply, written under
  `$LOCATE_PLAN_WORK/adm/replies/`, and with what `apply` would write from it, written out by
  hand, from which the expected sizes are computed:
  - `lx`, a legacy `CLAUDE.md`: a link a new folder must rewrite, with its anchor; an obsolete
    sentence; a dated paragraph; a paragraph an ADR carries word for word, at 100%; a new guide;
    and two em dashes, so that its size in bytes and in characters differ;
  - `dx`, the dispatcher layout: a generated `AGENTS.md` to replace, a `codex.md` whose link
    moves down a folder, a link to `claude.md`, which is deleted, an existing `_history/` file
    to append to, a line of 2,001 characters, a dated row bound for `AGENTS.md`, and a drop
    whose ADR has its words in another order, 0% by five-word sequences;
  - `mx`, two targets, whose component guide is pointed at from the component's `AGENTS.md`;
  - `px`, a row with no heading whose `what` cell is an instruction: its pointer line is the
    path alone, since `AGENTS.md` takes no agent's words.

  Sixteen variants of `lx`'s reply each break one rule: the frame, the header, a missing row,
  an overlap, five cells, a misnamed source, a range past the end, rows out of order, a bad
  destination, a missing or short drop file, a guide of no target, a bad flag. Two more run
  `check` where `detect` cannot migrate, and one names a reply that is not there.
- **Each report is checked whole**, line for line, against the expected report, with its exit
  status, the same output across runs and pythons, and the fixture's files left as they were.
- **`mutants/`** holds one unified diff per mutant, each one exact substitution, applied fresh
  with fuzz 0 to a copy of the script. Each patch names its file relative to the plugin's root.
  A patch that no longer applies is reported as `STALE`: re-anchor it, or drop it if its rule
  has gone. A mutant must be caught by the rule it breaks: check the `FAIL` line each one
  prints. `adm27-component-cut` survived until `codex-only` named a component no `CLAUDE.md`
  could find, `adm57-size-in-chars` until `lx` had two em dashes rather than one, since 2 bytes
  × 3 / 7 can round to no token, and `adm44-share-by-words` would survive any ADR that shared
  no words with its drop. A weaker four-cell rule cannot fail but by a crash, so
  `adm32-cells-from-pipes` breaks the cell parser instead.
