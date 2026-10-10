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
- [ ] The reopen guard matches `**Revision <label>** — closed`, with a test
- [ ] `references/subdividing.md` and `agents/plan-drafter.md`
  - [ ] Written with plugin-dev's `agent-development`, checked by `plugin-validator`
- [ ] `/master-plan <label> [spec]`, with `--dry-run <path>`; `/open-revision` is its alias
- [ ] `/close-revision` stamps, keeping the legacy path; `/file-plans` is legacy-only
- [ ] Verify end to end: the user runs it, I grade
