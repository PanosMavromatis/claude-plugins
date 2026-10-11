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
- [ ] `references/subdividing.md` and `agents/plan-drafter.md`
  - [ ] Written with plugin-dev's `agent-development`, checked by `plugin-validator`
- [ ] `/master-plan <label> [spec]`, with `--dry-run <path>`; `/open-revision` is its alias
- [ ] `/close-revision` stamps, keeping the legacy path; `/file-plans` is legacy-only
- [ ] Verify end to end: the user runs it, I grade
