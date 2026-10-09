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
- [ ] Run it on `tmp/pfsmgraph` at `5e8ad6e` and reproduce the working plan's §1
      numbers; any gap is a script bug or a §1 error, and gets resolved, not averaged
- [ ] Record the baseline under goal 3 in the root master plan
