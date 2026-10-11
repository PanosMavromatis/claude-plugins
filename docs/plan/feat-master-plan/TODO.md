# feat/master-plan

**Status**: active
**Created**: 2026-10-10
**Subgoal**: revision 06-subagent-refactor-R1 — `/master-plan`, `plan-drafter` and `subdividing.md`

## Tasks

- [x] Measure what the revision lifecycle does today, in the legacy and revisions layouts
  > **Done:** All three lifecycle scripts know only the legacy layout and misbehave on a
  > revisions index, and the reopen guard never matches a closed revision.
  - [x] What `open-revision.sh`, `close-revision.sh` and `file-plans.sh` read and write
    > **Note:** All three read only the root plan, taking `DO.md` before `TODO.md` with no
    > model argument, and know only the legacy layout. On this repo they work:
    > `close-revision.sh 06-subagent-refactor-R1` refuses on its three open items, and
    > `file-plans.sh` proposes filing R1's five merged plans (it skips `workflow-claude/`,
    > whose `DO.md` is stamped merged). `open-revision.sh` refuses on an existing
    > `## Subgoals — revision <label>` heading or `docs/plan/<label>`, and proposes a
    > section before `## Closed revisions`.
    > **Note:** On a revisions index none of them does the right thing. The scratch repo
    > had `[~] 07-rev` and `[x] 05-old`, each with a `_TODO.md`, a merged `feat-first/`
    > inside `07-rev/`, and a merged standalone `fix-flat/`. `open-revision.sh 08-new`
    > proposes appending a legacy `## Subgoals — revision 08-new` section to the index.
    > `close-revision.sh` refuses both labels with "no section", the open one included.
    > `file-plans.sh` files nothing and skips `fix-flat` for "no backlink", which is right,
    > since there is nothing to file. Only `locate-plan.sh` reads `_TODO.md`'s `**Status**:`,
    > and it accepts `open` and `closed…`; the index line's `[~]` or `[x]` decides what is open.
  - [x] Reproduce the reopen-guard miss on a closed revision
    > **Note:** Reproduced. `open-revision.sh 02-mcp-github-access` proposes reopening a
    > revision the master plan lists as closed, at line 125. The guard greps
    > `revision <label> — closed`, but `/close-revision` writes `**Revision <label>** —
    > closed`, or `**Revision <label>** — <subtitle> — closed` (line 126), so it never
    > matches. `05-subagent-refactor-R0` is refused only by the directory check;
    > revisions 02–04 pass that check because their directories moved under
    > `docs/plan/workflow-claude/`. The fix must match `- **Revision <label>**` as a whole
    > label, subtitle or not: the closing `**` ends the label, so `05-x` does not match
    > `05-x-2`. Under a revisions index, any `## Revisions` line for the label means the
    > label is taken.
- [x] The reopen guard matches `**Revision <label>** — closed`, with a test
  > **Done:** `open-revision.sh` matches whole labels, literally: a closed revision is a
  > line starting `- **Revision <label>**` and a section is the heading alone or with
  > `: <subtitle>`. It reads CRLF, fails with exit 3 if `awk` fails, and checks closed
  > before the directory, so a closed revision is refused for that reason. This repo's
  > `02-mcp-github-access` is now refused at line 125. `dev/open-revision/`: 15 cases
  > (~6 s), which the old script fails 9 of, and 9 mutants (~21 s), each caught by the
  > case aimed at it.
  > **Note:** The heading check has the same flaw the other way: it is a substring
  > `grep -F`, so `open-revision.sh 07-rev` is refused when only `07-rev-2` has a section.
  > `close-revision.sh` already matches headings whole (`$0 == h || index($0, h ":") == 1`).
  > **Q:** Scope and test: (A) fix both legacy checks, the closed index matching a line that
  > starts `- **Revision <label>**` (subtitle or not) and the heading matched whole, with
  > literal `awk` comparisons; leave the revisions-index refusals to goal 4's script, which
  > can share the matcher through `lib/plan-rules.sh`; test it in a new `dev/open-revision/`
  > suite with mutants, which goals 4 and 5 extend; (B) as A, and teach `open-revision.sh`
  > the revisions index now; or (C) as A, with the cases in an existing suite?
  > **A:** A.
  > **Note:** `dev/check-plan-index/README.md` said 33 cases and 18 mutants; measured 39
  > and 24, and corrected here. The other suite READMEs' mutant counts match their
  > `mutants/` directories.
- [x] `references/subdividing.md` and `agents/plan-drafter.md`
  > **Done:** `agents/plan-drafter.md`, the plugin's first shipped agent (`opus`, `Read,
  > Grep, Glob`, magenta; description 321 characters, body 2,322), returns `## Draft`,
  > `## Left out` and `## Questions` and never writes. `references/subdividing.md` (4,195
  > characters) holds the agreed plan's §4.5 rules with their reasons, the version field,
  > and the exact `_TODO.md` form, which matches what the scripts read.
  > **Note:** The agreed plan's §4.1 row gives `opus`, `Read, Grep, Glob, Bash(git log:*)`.
  > `feat-plan-locator`'s probe found a Bash pattern in a plugin agent's `tools:` is not
  > enforced (it grants all of Bash), which is why `plan-locator` shipped without Bash.
  > **Q:** Tools and context: (A) `Read, Grep, Glob`, no Bash (`/master-plan` passes the
  > spec, the root index and the previous revision), `model: opus`, and the consumer's
  > `CLAUDE.md` kept, since the agent runs once per revision and project conventions are
  > the judgement it is for; (B) as A with `omitClaudeMd: true`; or (C) the §4.1 row as
  > written, `Bash(git log:*)` granting all of Bash?
  > **A:** A.
  - [x] Written with plugin-dev's `agent-development`, checked by `plugin-validator`
    > **Note:** plugin-dev's `validate-agent.sh` (the scratch copy with its `set -e`
    > counter fixed) passes with the one expected warning, no `<example>` blocks; a first
    > draft also warned that the body did not open "You are". `claude plugin validate`
    > passes with the three items it gave before this branch: the plugin name, the root
    > `CLAUDE.md`, and no install line in the README.
    > **Note:** `plugin-validator` passed with no critical issue. Its findings, each
    > checked against the files: four were fixed here (name the `~~~markdown` fence; put
    > the more-than-eight split in `## Questions`; `subdividing.md` said the body "only
    > points here"; settled decisions are plain bullets, since `SUBGOALS_AWK` counts any
    > indent-0 `- [ ] ` line as a subgoal). `/master-plan` not existing yet is goal 4.
    > `close-revision.md`'s `argument-hint: "<revision-number>"` is goal 5. The README's
    > "What's in here" (no `agents/`, `references/`, or three of the seven plan scripts),
    > the plugin `CLAUDE.md:7` ("every artifact is a Markdown command") and `/new-branch`'s
    > missing `argument-hint` go to the plan-convention subgoal, recorded there in the
    > master plan. `Bash(find:*)` and `Bash(cat:*)` in four commands' `allowed-tools`
    > match destructive forms; that goes to R2, with the "run alone" follow-up. The
    > `**Spec**:` path stays: it records provenance and no command resolves it.
- [x] `/master-plan <label> [spec]`, with `--dry-run <path>`; `/open-revision` is its alias
  > **Done:** `/master-plan` proposes through the new read-only `propose-revision.sh`, drafts
  > through `plan-drafter`, reviews in the main session, writes the root plan from `--render`
  > and the revision from the approved draft, and commits only after `locate-plan.sh` and a
  > re-run of the proposer both read the result. It creates an index, appends to one, or
  > converts a legacy root plan with nothing open; `--dry-run` writes to a directory.
  > `/open-revision` is its alias; `open-revision.sh` and its suite are gone, their matchers in
  > the library and their cases in `dev/propose-revision/` (72 cases, 36 mutants).
  > **Q:** Where do the refusal and the proposal live: (A) a new read-only
  > `scripts/propose-revision.sh <label>` with a `key: value` report, which reads the root
  > plan's layout, refuses a label `## Revisions` lists under any marker or whose
  > `docs/plan/<label>/` exists, proposes the `_TODO.md` path and the index line (or a new
  > index), and shares a whole-label matcher through `lib/plan-rules.sh`, leaving
  > `open-revision.sh` and its suite as the legacy proposer; (B) `open-revision.sh` extended
  > to detect the layout; or (C) no script, the checks in `/master-plan`'s prose?
  > **A:** A.
  > **Note:** A legacy close already writes the new layout's per-revision file:
  > `close-revision.sh` cuts the section to `docs/plan/<label>/_TODO.md` and leaves
  > `- **Revision <label>**[ — <subtitle>] — closed. See \`<path>\`.` (line 78). Only the
  > pointer's shape differs from an index line, and `index_open` accepts any note after ` — `.
  > **Q:** On a legacy root plan: (A) with no open `## Subgoals — revision` section, propose
  > converting it in the same commit (add `**Layout**: revisions`, `## Closed revisions` →
  > `## Revisions`, each pointer → `- [x] <label> — <the rest>`, the new `[~]` line, other
  > lines kept), and with one open, refuse ("close it first, or convert by hand"), with
  > `--dry-run` working in every layout; (B) insert the draft as a legacy section through
  > `open-revision.sh`; or (C) refuse, apart from `--dry-run`?
  > **A:** A.
  > **Note:** This leaves nothing that writes a new legacy section, so Q5 below revises Q1's
  > "leaving `open-revision.sh` and its suite as the legacy proposer".
  > **Note:** R2 step 0 in the agreed plan converts this repo by hand, assuming R1 is still
  > open. Goal 5 closes R1 in legacy form, so R2 can open with `/master-plan` itself, which
  > converts the root plan. Revise step 0 in the R2 handoff.
  > **Q:** `--dry-run <path>`: (A) `<path>` is a directory, created if absent, given the
  > approved `_TODO.md` and, when a real run would change the root plan, the root plan as it
  > would read after; a refusal a real run would hit is reported, not fatal; a path inside
  > `docs/plan/` or an existing file is refused; no branch or commit, writes still confirmed;
  > (B) `<path>` is the one `_TODO.md`, the root change printed, refusals fatal; or (C) the
  > draft only?
  > **A:** A.
  > **Q:** The drafter and the review: (A) spawn `workflow-claude:plan-drafter` with the
  > label, date, model file, spec (a path, or the text), the root plan and the script's
  > `previous:` path; with no spec, ask for purpose, decisions and subgoals and pass those as
  > the spec (`**Spec**: conversation`); show the three sections as returned, edit the draft
  > in the main session, re-spawn only on request; after the write and before the commit,
  > `locate-plan.sh` must report `found` with subgoal 1 as `next:`, or nothing is committed;
  > (B) as A, re-spawning every round; or (C) as A, with no spec drafted in the main session?
  > **A:** A.
  > **Q:** `/open-revision` as an alias: (A) a short command running
  > `Skill(workflow-claude:master-plan)` with its arguments, kept for one revision; the
  > heading and closed-pointer matchers move from `open-revision.sh` into `lib/plan-rules.sh`
  > for `propose-revision.sh`'s legacy path; `open-revision.sh` is deleted and its 15 cases and
  > 9 mutants ported to the new suite; (B) a pure alias, `open-revision.sh` kept unused; or
  > (C) an alias keeping the legacy section path?
  > **A:** A.
  > **Note:** Only `/open-revision` runs `open-revision.sh`. `plugins/dp-compile/README.md`
  > names `/open-revision`, so the command name has to keep working.
  > **Note:** The Claude Code docs, as reported by a docs agent and not checked here: `Agent`
  > needs no permission; `Agent(Name)` rules exist, but the `plugin:agent` form is not
  > documented in them; and the skills page says `allowed-tools` grants rather than restricts,
  > where the plugin `CLAUDE.md` says "restricts". Measured here: `Write` creates missing
  > parent directories, so a dry run needs no `mkdir`.
  > **Q:** `allowed-tools`: (A) `propose-revision.sh` and `locate-plan.sh`; `git status`,
  > `git log`, `git branch --show-current`, `git rev-parse`, `git checkout -b`, `git add`,
  > `git commit`; `Read`, `Write`, `Edit`, `Agent`, `AskUserQuestion`; no `Grep`/`Glob`, no
  > push; (B) as A with `Agent(workflow-claude:plan-drafter)`; or (C) as A with `git push`?
  > **A:** A.
  - [x] The spec, `propose-revision-spec.md`, beside this plan
    > **Note:** `index_open` calls the caller's own `fail`, as it does for
    > `propose-branch-plan.sh` and `propose-merge-record.sh`, so the new script reuses it and
    > reports an index violation in its own ten-line shape.
  - [x] `lib/plan-rules.sh` gains the heading and closed-pointer matchers; the four library suites still pass
    > **Note:** `section_line` and `pointer_line` are `open-revision.sh`'s two `awk` lines
    > unchanged, appended after line 499 so that no existing mutant's hunk moves. A scratch
    > probe passed 14 of 14: whole labels only, `\` and `.` literal, CRLF, exit 3 on an
    > unreadable file. Suites unchanged: `locate-plan` 83 cases, 26 mutants killed plus `n05`
    > equivalent; `check-plan-index` 39 and 24; `propose-branch-plan` 32 and 18;
    > `propose-merge-record` 37 and 18. The header's caller list gains `propose-revision.sh`
    > with the script, in subgoal 3.
  - [x] `scripts/propose-revision.sh` and `dev/propose-revision/`, with `open-revision`'s cases ported and every mutant caught
    > **Note:** `dev/propose-revision/`: 72 cases (~28 s), 36 mutants (~404 s), each killed by
    > the case aimed at its rule. `open-revision`'s `o01`–`o11` and `o15` are `l01`–`l12`, and
    > its nine mutants `v01`–`v09`. The four other library suites' cases are unchanged.
    > **Note:** The mutants found two blind spots in the suite, not the script. A fake `awk`
    > failing every call dies in `check_layout` before a matcher runs, so `l14` and `l15` use
    > one that fails only when `$L` is a heading or a pointer. Python's `text=True` turns
    > `\r\n` into `\n`, so the CRLF render cases could not see a kept carriage return; output
    > is now decoded from bytes.
    > **Note:** On `tmp/pfsmgraph`, read-only, the conversion's diff is exactly the spec's: the
    > header, the heading, four pointers, one line. In a scratch copy, `locate-plan.sh`
    > resolved the converted index at rung 3, `next:` on subgoal 1, and a re-run refused the
    > label as listed: Q4's write check, on a real consumer. On this repository it refuses:
    > line 9 is R1's open section.
    > **Note:** The spec gained what the implementation exposed: `--render`'s report on stderr;
    > dry-run paths resolved through symlinks, with no `.` or `..`; `**Layout**` stacked under
    > `**Status**`, and an existing `**Layout**:` line rewritten, since only the first is read;
    > only pointers under `## Closed revisions` convert, and one that would not is an error;
    > the label refusals read fenced lines, as `open-revision.sh` did, while the open-section
    > check and the conversion skip them.
  - [x] `commands/master-plan.md`, `commands/open-revision.md` as its alias, `open-revision.sh` and `dev/open-revision/` removed, README run lines
    > **Note:** The write check passes the revision file explicitly, rung 1: on a branch with
    > its own plan rung 2 would find that instead, and with two revisions open rung 3 asks.
    > Measured on the converted scratch copy: rung 1 reports `kind: revision-master` with
    > `next:` on subgoal 1. The re-run of `propose-revision.sh` must then refuse the label as
    > listed, which proves the index reads and holds the line.
    > **Note:** `master-plan.md`'s body is 7,493 characters; the alias's is 513, invoking
    > `Skill(workflow-claude:master-plan)` as `/smart-commit` invokes its nested command. The
    > plugin README's `scripts/` line and command table name the new command and script; the
    > rest of the lifecycle prose goes to the plan-convention subgoal, where it is listed.
    > The five library suites' cases are unchanged after the removal.
- [~] `/close-revision` stamps, keeping the legacy path; `/file-plans` is legacy-only
  > **Note:** `close-revision.sh` passes the heading through `awk -v h=…`, the flaw goal 2
  > fixed in `open-revision.sh`: a backslash in a label is read as an escape, so that
  > revision can never be found to close. Neither it nor `file-plans.sh` has a suite.
  > **Q:** The script: (A) rewrite `close-revision.sh` on the library with a `key: value`
  > report for both layouts: under an index, refuse a label not listed `[~]` or a `_TODO.md`
  > with a `[ ]`, `[~]` or `[!]` subgoal (read by `SUBGOALS_AWK`), else propose the
  > `**Status**` and index lines as line, old and new text; legacy, today's extraction with
  > the section matched by `section_line`; a new `dev/close-revision/` suite with mutants;
  > `argument-hint: "<label>"`; (B) a second script for the index, legacy untouched; or (C)
  > `close-revision.sh` extended in place, its prose report kept?
  > **A:** A.
  > **Q:** `/file-plans` as legacy-only: (A) `file-plans.sh` exits 0 with "nothing to do" on a
  > revisions index (`**Layout**: revisions`, outside fences), `file-plans.md` says it serves
  > legacy root plans for one more revision, and a small `dev/file-plans/` suite checks it;
  > (B) prose only; or (C) a refusal, exit 1?
  > **A:** A.
  > **Q:** (raised by the user) Withdraw `/file-plans` now, and fold its filing into
  > `/close-revision`? This reopens the master plan's settled "Neither is removed".
  > **A:** Yes: keep related refactorings together. Supersedes Q2. The legacy `extract`
  > gains `moves:`, one `git mv` per merged flat plan backlinked inside the section; a
  > backlinked plan not merged, or missing, is a warning and stays flat. The command does
  > the cut, the archive and the moves in one commit. `commands/file-plans.md` and
  > `scripts/file-plans.sh` are removed.
  > **Note:** The agreed plan (§4.2, D-N3) kept `/file-plans` one revision only "as a legacy
  > tool (flat plans created by an older `/new-branch`)". Folded into the close, that job is
  > done at the one moment every plan it would move is final, which also ends the flaw the
  > plugin `CLAUDE.md` records: a revision's last plan could never be filed before its close.
  > The trap, a merged flat plan whose revision already closed, has no instance: pfsmgraph
  > has nothing flat; here, R1's five plans (six with this branch) close with R1, and
  > `workflow-claude/` has no backlink by design. `dp-compile` never names `/file-plans`.
  - [x] The spec, `close-revision-spec.md`, beside this plan
    > **Note:** Twelve report keys; `--render root|archive` for the legacy files and `--check`,
    > which recomputes both layouts' writes, and the moves, from `HEAD` and compares them
    > with the working tree before the commit. The stamp is two `Edit`s at named lines, not
    > a rendered file: a 100-line `_TODO.md` retyped is where a word changes unnoticed.
  - [x] `close-revision.sh` rewritten on the library, with `dev/close-revision/` and every mutant caught
    > **Note:** 446 lines. Every read goes through `src`, the working tree or `HEAD` under
    > `--check`, so a check is the proposal computed against `HEAD`: one set of rules.
    > `dev/close-revision/`: 55 cases (~38 s), 37 mutants (~465 s), each killed by its aimed
    > case; `c05` and `c06` through an exit 3 that is the mutant's own consequence. The
    > `--check` cases write the closed state from the suite's strings, never from `--render`,
    > so a wrong render cannot pass a wrong check. The five other library suites' cases are
    > unchanged.
    > **Note:** Rehearsed on a copy of this repository with R1's three open subgoals marked
    > `[x]`: the proposal moves the same five plans `file-plans.sh` named, warns that
    > `feat-master-plan` is still active, and cuts lines 9-134; after the writes and the moves
    > `--check` verified, and with one word of the archive changed it failed, naming it.
    > `propose-revision.sh` then proposed converting the closed root plan for R2, with R1's
    > archive as `previous:`: the lifecycle composes.
  - [ ] `commands/close-revision.md`: both paths, the moves, `--check` before the commit, `argument-hint: "<label>"`
  - [ ] `/file-plans` removed: its command and script, with the README's command table and `scripts/` line
- [ ] Verify end to end: the user runs it, I grade
