# chore/measure-context

**Status**: active
**Created**: 2026-10-08
**Subgoal**: revision 05-subagent-refactor-R0 — add `dev/measure-context.sh` and record its baseline

## Tasks

- [x] Write `dev/measure-context.sh`: read-only, takes a repository path, and reports
      the five measurements in bytes and ≈ tokens (bytes / 4)
  > **Done:** written and tested on the reference clone (left with 0 changes), on this
  > repository, and on two scratch fixtures: a path with spaces, a parenthesised import,
  > imports in inline and fenced code (skipped), an email address (not an import), an
  > import cycle (each file once), a `paths:`-scoped rule (excluded), an always-on rule
  > (included), an empty `docs/agents/`. Bash 3.2-safe: arrays guarded under `set -u`.
  > **Note:** what each command "reads whole" is a table in the script, because a script
  > cannot parse a command's prose; a command that stops reading a file whole has to be
  > taken off that table, or the report overstates.
  > **Note:** a `DO.md`/`TODO.md` below `docs/plan/` carrying a `## Subgoals` heading is
  > counted as a moved master plan, not a branch plan — otherwise this repository's
  > `docs/plan/workflow-claude/DO.md` was its "largest branch plan".
  > **Note:** **the script measures the main session only.** A subagent re-reads what it
  > is handed and carries its own prompt, so the refactor can shrink this report while
  > total usage stays flat or rises. Total cost is judged separately (`/cost`, the usage
  > page, `/context` for the live breakdown); this script answers "how much does the
  > conversation the user is steering hold", which is the number that drives
  > compaction and attention.
- [x] Run it on `tmp/pfsmgraph` at `5e8ad6e` and reproduce the working plan's §1
      numbers; any gap is a script bug or a §1 error, and gets resolved, not averaged
  > **Done:** five gaps, each traced to one side being wrong. Script bug (fixed): the
  > log-entry count matched markers quoted inside sentences; anchoring it to line start
  > reproduces §1 exactly (539 Note, 277 Q, 272 A, 228 Done). §1 errors (corrected in the
  > working plan): `claude.md` is 10,067 bytes and was never 10,064 in any commit; "48
  > branch plans" was every `.md` under `docs/plan/` — 41 branch plans, 5 archives, the
  > master plan, `DEFERRED.md`; plans run 3.6–63 KB with a 15.9 KB median, not 18–63 KB;
  > `/agents-docs-update` reads ≈ 55k tokens (README 8.6 KB, `docs/agents` 180.5 KB,
  > `docs/ops` 30.5 KB), not ≈ 50k. Everything else matched to the byte: session start,
  > the five command bodies, the largest plan and archive.
  > **Note:** the reference clone was read through `git -C` and absolute paths only, and
  > reports 0 changes afterwards.
- [ ] Record the baseline under goal 3 in the root master plan
