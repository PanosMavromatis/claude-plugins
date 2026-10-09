# `scripts/locate-plan.sh` — specification

The contract for the deterministic plan resolver that replaces `agents/plan-locator.md` in
Step 1 of `/step` and `/hitl-step`. Goal 6 of this branch plan settled it (the Q&A sits
under that goal); goal 7 implements against it, and every diagnostic and warning below gets
a fixture case there. The script resolves by the same five rungs as the agent and returns
the same report, with four keys added, so Step 1's contract barely changes.

## Why a script

Resolution is a set of rules: globs, header checks, prefix filters. The agent suite showed
that a model running such rules can return a plausible but wrong plan, and that the step
command's `next:` check cannot see it, because that check confirms a line, not a
resolution. A script applies the rules the same way every time, and where the repository
breaks a convention it can rely on, it neither guesses nor fails silently: it returns
`result: error` with a `problem:` and a `fix:`, which the command relays to the user.

## Usage

```
locate-plan.sh <TODO.md|DO.md> [--goal <line>] [--branch <name>] [--] [path]
```

- **Model** (required): the filename the calling command drives, called **F** below.
  `TODO.md` for `/hitl-step`, `DO.md` for `/step`. The other one is called **F′**.
- **path** (optional): the path token from the command's arguments. `--` ends options, for
  a path beginning with `-`.
- **`--goal <line>`**: a line number. The command finds an item the user named out of order
  (with `Grep`) and passes its line; free text never reaches the script.
- **`--branch <name>`**: overrides the current branch, for fixtures and for re-runs with
  corrected inputs. Without it the script runs `git symbolic-ref --short -q HEAD`, which
  prints nothing on a detached HEAD and, unlike `git branch --show-current`, works on git
  before 2.22. `--branch ''` means detached.

Usage errors (exit 2, message on stderr, no report): no model, or a model other than
`TODO.md`/`DO.md`; an unknown option; more than one path; a `--goal` that is not a positive
integer; an option missing its value.

## Report

Always these sixteen keys, in this order, one per line, `—` when empty. Every path is
relative to the repository root and none starts with `/`.

```
result:     found | ask | none | error
rung:       1–5 | —
plan:       the resolved file
kind:       branch | revision-master | legacy-master | root-file
layout:     per-goal | legacy
status:     the **Status** value
lines:      the plan's line count
next:       path:line <the line, verbatim>
goal-file:  the selected goal's file (per-goal only)
subgoals:   path:line, one item per line
blocked:    path:line, one item per line
candidates: path, one item per line (ask only)
warnings:   one per line
problem:    which convention broke, and where (error only)
fix:        the command or edit that repairs it (error only)
message:    one sentence for the user
```

A key with several items puts the first on the key line and each further one on its own
continuation line, indented two spaces. Comma-separated values are not used, because a
branch name, and so a plan path, may contain a comma.

Relative to the agent's report: `stop` is gone (folded into `error`, E1); `goal-file:`,
`warnings:`, `problem:` and `fix:` are new; `lines:` is given for every plan, since it
costs a script nothing.

## Resolution — stop at the first rung that yields a result

**Rung 1 — path.** Only if a path was given; nothing here ever falls through to rung 2,
since a typo must never run another plan.

- Try the path relative to the repository root, then relative to `docs/plan/`. If both
  exist, use the repository-relative one (W9). An absolute path is accepted if it lies
  inside the repository; otherwise E3.
- A file is used whatever its name, so `_F` archives are reachable. A file named F′ is used
  with W7.
- A directory means F inside it; none there → E2.
- A file carrying `**Layout**: revisions` is the root index, not a plan: follow it exactly
  as rung 3 does, report `rung: 1`, and add W10. Where rung 3 would fall through to rung
  4, rung 1 cannot, and returns E14.
- Nothing at either reading → E1.

**Rung 2 — branch plan.** Skipped, with W4, when the branch is empty.

- The plan name is the branch with `/` flattened to `-`.
- `find docs/plan -type f -name F`, keeping matches whose parent directory's basename equals
  the plan name exactly, sorted with `LC_ALL=C`. This matches the flat location too.
- One → found. Several → `ask` with every path: one is a stale copy.
- None → look for the plan name with F′. Found → E4. Otherwise rung 3.
- A resolved plan stamped `merged` is used, with W3.

**Rung 3 — master plan.**

- No `docs/plan/F` → rung 4, adding W8 if `docs/plan/F′` exists.
- `docs/plan/F` with `**Layout**: revisions` is the root index. Parse its `## Revisions`
  section (E5 if absent). Every indent-0 list item there must be a revision line (E6). Take
  the `[~]` lines; each needs `docs/plan/<label>/_F` (E7, checked for all of them before
  anything is returned). One → found, `kind: revision-master`. Several → `ask` with their
  `_F` paths. None → rung 4.
- Otherwise it is a legacy master plan → found, `kind: legacy-master`.

**Rung 4 — glob.** `find docs/plan -type f -name F`, minus `docs/plan/F`, sorted with
`LC_ALL=C`. Partition by status: **merged** only if the first `^\*\*Status\*\*:` line
anywhere in the file has a value beginning `merged`; everything else, no line included, is
**active** (W1 per unstamped plan). This is the rule `file-plans.sh` applies, and the two
readers must agree.

- One active → found. Several active → `ask`, with the number of merged plans hidden in
  `message`. Only merged → `ask` with those, saying all are merged; never pick one. None at
  all → rung 5.

**Rung 5 — root file.** `F` at the repository root → found, `plan: F`, `kind: root-file`,
W5. Otherwise `result: none`, `rung: —`.

## Reading the resolved plan

- **Fences.** Lines inside a fenced code block (between lines whose first non-blank
  characters are three backticks) are never items.
- **Item lines.** An item is `- [m] ` with m one of the five markers ` ~x!-`. An indent-0
  line that looks like one but has another marker (`- [X]`, `- [/]`) is ignored with W6.
- **`status:`** the first `**Status**:` value, trimmed. Known values: `active`, `merged…`,
  `open`, `closed…`; anything else is W2. A branch plan with no status line gets W1.
- **`kind:`** by rung: 2 and 4 → `branch`; 3 → `legacy-master` or `revision-master`;
  5 → `root-file`. For rung 1, by path: `docs/plan/F` → `legacy-master`;
  `docs/plan/<dir>/_F` → `revision-master`; `F` at the root → `root-file`; else `branch`.
- **`layout:`** `per-goal` if the plan has `**Layout**: per-goal`, otherwise `legacy`.
  `**Layout**: legacy` is accepted explicitly. Any other value, `revisions` on a file other
  than `docs/plan/F`, or `per-goal` on `docs/plan/F`, is E8.
- **TODO model.** `next:` is the first indent-0 `[~]`, else the first indent-0 `[ ]`.
  `subgoals:` is every indented item line, any marker, after it and before the next indent-0
  item or `## ` heading; all markers, because Step 4's parent rule reads `[x]` and `[-]` too.
- **DO model.** `next:` is the first `[ ]` at any indent; `subgoals: —`.
- **Both models.** `blocked:` lists indent-0 `[!]` lines. `--goal <line>` replaces the
  selection; that line must exist and be an item (indent-0 for the TODO model), else E12.
  Nothing open → `next: —`, and `message` says every item is closed.
- **Per-goal layout.** The plan is an index. Every indent-0 item must read
  `- [m] NN …` with NN matching `[0-9]+[a-z]?` (a split goal is `03a`) — E9 otherwise.
  Selection runs on the index, so `next:` names the index line. The goal file is the single
  match of `<plan dir>/<F without .md>/NN-*.md`: none → E10; several → E11. `goal-file:`
  names it, and `subgoals:` lists every item line in it, at any indent, outside fences. If
  its `**Goal**:` marker differs from the index line's, add W11: the goal file is the source
  of truth (working plan, D2).

## Diagnostics — `result: error`, exit 1

Each names the file and line where one exists. When a rung finds several violations
(two `[~]` revisions with no `_F`, say), all are listed on continuation lines.

| # | Rung | `problem:` | `fix:` |
|---|---|---|---|
| E1 | 1 | nothing exists at `<path>`; both readings named | check the path, or omit it to resolve by branch |
| E2 | 1 | `<dir>/` holds no F | name the file; if `<dir>/F′` exists, say it belongs to the other command |
| E3 | 1 | `<path>` lies outside the repository | give a path inside it, relative to its root |
| E4 | 2 | the branch plan exists only as `<…>/<name>/F′` | run the other command (`/step` ↔ `/hitl-step`) |
| E5 | 3 | `docs/plan/F` declares `**Layout**: revisions` but has no `## Revisions` | add the section, or remove the header |
| E6 | 3 | `docs/plan/F:<n>` is not a revision line: `<line>` | write it as `- [~] <label> — <note>` |
| E7 | 3 | revision `<label>` is open at `docs/plan/F:<n>` but `docs/plan/<label>/_F` is missing (and `_F′` exists, if it does) | restore it (`git log -- docs/plan/<label>/`), or mark line `<n>` `[x]` if it has closed |
| E8 | any | `<file>:<n>` has `**Layout**: <v>`, which is unknown here | use `revisions` on `docs/plan/F` only, `per-goal` or `legacy` elsewhere |
| E9 | read | `<index>:<n>` has no goal number: `<line>` | write it as `- [m] NN — <goal>` |
| E10 | read | goal `NN` has no file matching `<dir>/NN-*.md` | create it, or correct the number on `<index>:<n>` |
| E11 | read | goal `NN` matches several files (listed) | remove or renumber the stale copy |
| E12 | read | `--goal <line>` is past the end of `<plan>`, or not an item | pass the line of an item |
| E13 | — | not inside a git repository | run from the repository |
| E14 | 1 | `<path>` is the root index and no revision in it is `[~]` | name a plan file, or mark the open revision `[~]` |
| E15 | any | `<file>` cannot be read, or `<dir>/` cannot be entered or listed | `chmod u+r <file>` / `chmod u+rx <dir>` |

E15 is checked before every read, and also up front for every directory under
`docs/plan/` once rung 1 has not answered. A plan inside an unreadable directory would
otherwise be missing, without notice, from rung 2's duplicate check and from rung 4. At
rung 1, a path whose directory cannot be entered is E15, never E3.

A revision label in a revision line follows `open-revision.sh`'s rule: non-empty, no space
or `/`, not starting with `#` or `-`.

## Warnings — valid but suspicious

The command shows them and carries on.

| # | When |
|---|---|
| W1 | a branch plan, resolved or a candidate, has no `**Status**:` line, so counts as active |
| W2 | a status value is not one of `active`, `merged…`, `open`, `closed…` |
| W3 | the resolved branch plan is stamped `merged`: the branch was probably reopened |
| W4 | detached HEAD (a rebase, a bisect, a CI checkout): rung 2 skipped |
| W5 | the plan is a root-level F: plans belong under `docs/plan/` (`git mv F docs/plan/F`) |
| W6 | `<file>:<n>` looks like an item but its marker is unknown, so it was ignored |
| W7 | the explicit path names F′, the other command's model |
| W8 | no `docs/plan/F`, but `docs/plan/F′` exists: the master plan uses the other model |
| W9 | the path also resolves under `docs/plan/`; the repository-relative one was used |
| W10 | the explicit path was the root index, followed as rung 3 would |
| W11 | the index marker on `<index>:<n>` disagrees with the goal file's `**Goal**:` |

## Exit codes

| Code | Meaning | The command |
|---|---|---|
| 0 | report printed; `result:` is `found`, `ask` or `none` | acts on `result:` |
| 1 | report printed; `result: error` | relays `problem:` and `fix:`, and stops |
| 2 | usage error; message on stderr, no report | relays stderr, and stops |
| 3 | a tool (`awk`, `find`, `git`, `cd`) failed in a way the rules cannot explain; message on stderr, no report | relays stderr, and stops |
| other, or no `result:` line | the script failed | relays stderr, and stops |

## Guarantees

- **Fails loudly.** `set -e` does not apply inside a function used as a condition, nor
  to a command substitution in a condition, a `case` word or `[ ]`, so nothing relies on
  it. Every file is checked readable before it is read (E15), every tool's status is
  checked where it runs, and an unexplained failure exits 3. An empty value from a failed
  read is never taken as an answer: goal 11 found four places where one was.
- **Read-only.** Writes nothing, temporary files included. Runs only
  `git rev-parse --show-toplevel` and `git symbolic-ref --short -q HEAD`, then `cd`s to the
  root, so it works from any subdirectory.
- **Deterministic.** The same tree and arguments give byte-identical output: every listing
  sorted with `LC_ALL=C`, no clock, no randomness, no environment beyond the arguments and
  the working tree.
- **Portable.** Bash 3.2 and BSD or GNU userlands: no `globstar`, associative arrays,
  `mapfile` or `${v,,}`; matching in `awk`, never `grep` with `\|`; `wc` output trimmed;
  `set -euo pipefail`. The style is `open-revision.sh`'s.
- **Self-checking.** Every rule a convention imposes is either applied or reported; a
  branch of the logic that cannot decide returns an error, never a default.

## Edge rules, each with a fixture case in goal 7

Both came from the `plugin-validator` pass under goal 5.

- An empty branch (detached HEAD) skips rung 2, with W4, instead of globbing
  `docs/plan/**//F`.
- No `docs/plan/F` at rung 3 falls through to rung 4.
