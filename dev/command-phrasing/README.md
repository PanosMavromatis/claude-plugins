# Command phrasing check

`check.py` checks that every `workflow-coding` command whose `allowed-tools` grants `git`
says how to phrase a command so `allowed-tools` matches it: the two fixed phrases the
plugin's `CLAUDE.md` names under "Scoped `allowed-tools`", ``never `git -C <path>` `` and
`every command alone`, each whole on one line of the command's body. `allowed-tools`
matches the plain, single command, so a session that runs `git -C <path> status`, or
chains `git log …; grep …`, is refused what its command grants. The reasoning, and the
end-to-end runs that found those refusals, are in the `fix-command-phrasing` branch plan.
It lives here, outside the plugin, so it doesn't ship with it.

## Running it: no model, no cost

```bash
python3 -I dev/command-phrasing/check.py                   # the plugin's commands (~0.1 s)
python3 -I dev/command-phrasing/suite.py                   # 35 cases (~1 s)
python3 -I dev/command-phrasing/suite.py --mutants         # 13 mutants, every one must be caught (~2 s)
```

Run `check.py` after editing a command's `allowed-tools` or the text that states the rule.
It exits 0 when every command granting `git` carries both phrases, 1 naming each command
and the phrase it lacks, and 2 when given a path that does not exist or no command files.
Given files or directories, it checks those instead. `--script PATH` makes the suite test
another copy. Each case works in its own temporary directory, so nothing is written in
the repository. Only macOS has been tested.

- **A command grants `git`** when the `allowed-tools` key in its frontmatter holds a
  `Bash(git …)` entry, on the key's line or in a list beneath it (`f08`). `git` named only
  in the body grants nothing (`f03`), nor does a file with no frontmatter (`f06`). A
  command that grants none is listed as skipped (`f02`), so a miss is never silent.
- **The phrases are matched in the body, line by line.** One in the frontmatter does not
  count (`f07`), and one split across two lines fails (`f04`): the plugin's `CLAUDE.md`
  asks for each to be kept whole on one line so a check like this one can find it.
- **Every failing command is named**, with the phrases it lacks (`f05`).
- **`f09`, `f10`**: no command files to check, or a path that does not exist, exits 2
  rather than reporting nothing failing. **`f11`** checks one file given by name.
- **`p00`, `p01`**: the plugin's commands pass, as found by default and as copied.
- **`<command>/C`, `<command>/alone`** are generated from the plugin: for each command that
  grants `git`, by the suite's own reading of the frontmatter, each phrase is removed in
  turn from a copy, and the check must fail naming that command and that phrase, and no
  other. A new command that grants `git` gets its two cases with no edit here.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of `check.py`, placed where its default still reaches the
  plugin's commands. Each patch names its file relative to `dev/command-phrasing/`. A
  patch that no longer applies is reported as `STALE`: re-anchor it, or drop it if its
  rule has gone. A mutant must be caught by the fixture case aimed at its rule, which run
  before the plugin's, so check the `FAIL` line each one prints. `m01`, `m02` drop a
  phrase; `m03` reads grants from the body; `m04` and `m05` find a phrase in the
  frontmatter or across lines; `m06`, `m07`, `m11` stop at the first failure, exit 0, or
  stop naming the phrase; `m08`, `m09` miss a listed grant or crash with no frontmatter;
  `m10`, `m12`, `m13` pass an empty directory, lose the default, or skip silently.
