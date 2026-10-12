# export-session.py test suite

These are the tests for `plugins/workflow-coding/scripts/export-session.py`, which renders
a Claude Code session log (JSONL) as Markdown for `/session-export-full`, compactions
included. They live here, outside the plugin, so they don't ship with it. The reasoning is
in the `feat-session-export-full` branch plan.

## Running it: no model, no cost

```bash
python3 -I dev/export-session/suite.py             # 8 cases (~1 s)
python3 -I dev/export-session/suite.py --mutants   # 5 mutants, every one must be caught (~1 s)
```

`-v` prints each output. `--script PATH` tests another copy. Each case works in its own
temporary directory, so no fixture outlives the run and nothing is written in the
repository. Only macOS has been tested.

- **The fixtures** are session logs written the way Claude Code writes them: one JSON
  record per line, in raw UTF-8, never `\u` escapes. A real log holds thousands of em
  dashes as raw bytes, and that is what makes the encoding cases able to fail.
- **The cases pin three defects measured on 2026-10-11:**
  - `e03`, `e04`: the title is the output file's name, less `.md` and any `-full`, not
    one session's hard-coded name;
  - `e01`: an em dash is written once. It runs under the `en_US.ISO8859-1` locale,
    because under a UTF-8 one a script that leaves the encoding to the locale passes too.
    Reading the log as Latin-1 writes each em dash double-encoded, the 2026-10-11 defect,
    and writing as Latin-1 crashes on the title's em dash. The suite refuses to run if
    that locale is not installed, rather than pass without testing it;
  - `e02`: the instructions given to `/compact` appear under it.
- **`g01`** renders one log holding every kind of record, each block checked byte for
  byte: an operator message with a system reminder stripped, tool actions collapsed,
  replies, a question and its answer, commands with and without arguments, a compaction
  summary, and the records that are skipped: meta, sidechain, malformed, non-message,
  local-command output. **`g02`** renders the same log under Latin-1 and must match.
- **`u01`, `u02`**: a usage error exits 2, says how to call it, and writes nothing.
- **Every run is checked** for its exit code, stderr (empty unless a case names it), the
  summary line's counts, and the output file's bytes.
- **`mutants/`** holds one unified diff per mutant, each an exact substitution, applied
  fresh with fuzz 0 to a copy of the script. Each patch names its file relative to
  `scripts/`. A patch that no longer applies is reported as `STALE`. Re-anchor it, or drop
  it if its rule has gone. A mutant must be caught by the case aimed at its rule: the
  defect cases run first, the title's before the rest, since every output carries a
  title. Check the `FAIL` line each one prints.
