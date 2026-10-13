# 04 — Check every command that grants git states the rule

**Goal**: [x]
> **Done:** `dev/command-phrasing/` holds the check, a 35-case suite and 13 mutants, all killed; the plugin passes, and the root `README.md` and the plugin's `CLAUDE.md` name it.
> **Q:** What shape should the check take under `dev/`: `dev/command-phrasing/` with `check.py`, a `suite.py` whose cases include, for each command that grants `git`, each half removed in turn, and `--mutants` patching `check.py`, as every other suite does (A); the check and its cases without mutants (B); or one self-testing file (C)?
> **A:** A.

- [x] A script under `dev/` lists every command whose `allowed-tools` grants a `Bash(git …)` entry, and fails any whose text does not state both halves of the rule, naming the command and the half it lacks
  > **Note:** `dev/command-phrasing/check.py`, read-only: a command grants `git` when its frontmatter's `allowed-tools`, on the key's line or listed beneath it, holds `Bash(git `; it must carry "never `git -C <path>`" and "every command alone" in its body, each whole on one line. It prints `ok`, `skip` (grants no git) or `FAIL <command> lacks: <phrases>` for each, and exits 0, 1, or 2 on a missing path or no command files, so a miss is never silent. On the plugin: 11 `ok`, 5 `skip`.
- [x] It passes on the plugin, and a case or mutant, in the shape of the other `dev/` suites, shows it failing, naming the command, when one command's statement is removed
  > **Note:** `suite.py`, 35 cases, ~1 s: 11 fixture cases each aimed at one rule, the plugin by default and as copied, and 22 generated from the plugin, each removing one phrase from one command that grants `git` and requiring exactly that `FAIL` line. The suite finds those commands by its own reading of the frontmatter, not `check.py`'s, so a new one gets its two cases with no edit. `--mutants`: 13 patches to `check.py`, all killed, each by the case aimed at it, ~2 s. The runner places the copy beside a `plugins` link so its default still reaches the commands; otherwise every mutant would fail `p00` for the wrong reason.
- [x] The root `README.md` lists it with the other suites
  > **Note:** After the `export-session` block, with its three commands. The plugin's `CLAUDE.md` also names it now, where goal 03 said the phrases are kept whole "so a check can find it".
