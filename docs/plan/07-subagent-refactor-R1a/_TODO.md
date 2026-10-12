# Revision 07-subagent-refactor-R1a

**Status**: open
**Version**: workflow-coding 0.10.1
**Opened**: 2026-10-12
**Spec**: the R1→R1a session handoff (`tmp/session-handoff-r1-r1a.md`, untracked, kept locally), section "Revision R1a — settled, do not reopen"; conversation (2026-10-12)

## Preamble

R1a adds two session commands to `workflow-coding`. `/workflow-coding:session-handoff` writes a temporary handoff document. `/workflow-coding:session-export-full` exports a session's full JSONL log, because `/export` loses everything before a compaction. R1a also fixes a SIGPIPE failure in `scripts/close-revision.sh` 0.10.0, which made closing R1 fail at random with exit 3. All of this ships as `workflow-coding` 0.10.1. The handoff is built with `/smart-compact`'s three parts (Keep / Drop / Say where) so that R2 can reuse it.

R1a does not decide how the handoff couples with `/smart-compact`. R2 decides that by measurement, and R2 keeps 0.11.0. At the end of R1a the session dogfoods the handoff: it follows the command's text by instruction, because the 0.10.0 driver cannot run the new command.

Opening R1a converted the root plan, `docs/plan/TODO.md`, from a legacy plan into a revisions index. The agreed plan gave that flip to R2 step 0; it happened one revision early, so R2 step 0 keeps only what remains.

## Settled decisions

- Label `07-subagent-refactor-R1a`; release `workflow-coding` `0.10.1`; R2 keeps `0.11.0`.
- Two commands: `/workflow-coding:session-handoff` (a temporary handoff document, like the
  R1→R1a handoff) and `/workflow-coding:session-export-full` (`/export` loses everything
  before a compaction; the session's JSONL log keeps it).
- **Coupling with `/smart-compact` is decided in R2, by measurement**, not now. Build the
  handoff in R1a with `/smart-compact`'s three parts (§4.4: Keep / Drop / Say where), so R2
  can reuse it rather than move it. Candidate measure: the next session's reorientation
  cost (Reads and tokens before the first productive action; facts the user restates).
- **Dogfood the handoff one release early:** at the end of R1a the `0.10.0` driver cannot
  run the new command, so the session follows the command's *text*
  (`plugins/workflow-coding/commands/session-handoff.md`) by instruction. The next session
  reads the result through a new root `CLAUDE.md` (none exists today) holding one
  permanent, conditional line: "If `tmp/session-handoff.md` exists, read it before anything
  else …; delete it once the user confirms." `tmp/` is gitignored, so the handoff never
  needs a commit. Consequence for the command's text: read as a plain file it gets no
  `$ARGUMENTS`, no `${CLAUDE_PLUGIN_ROOT}` and no `allowed-tools`, so write it to need none.
- **`/session-export-full` is a script with a suite, plus a thin command** (rule-shaped
  work goes to scripts). Subagent transcripts (`<uuid>/subagents/`) are **optional**.
  Output goes outside the repo. Start from `tmp/export_session.py` (untracked). Measured on
  the R1 session's log (55 MB, 16 compactions, 0.28 s), it had four defects, and three were
  fixed on 2026-10-11 so that session could be exported: double-encoded em dashes, the
  `/compact` instructions never captured (an optional group after a lazy `.*?` matched
  empty), and a title hard-coded to `m2-tier-1a` (now taken from the output filename).
  Still open: a renamed session carries several `custom-title` records in its log (the R1
  session's has two); `<uuid>/custom-title.json` holds the current name, which is how the
  runbook's export command finds the R1 session.
- Session logs are deleted after `cleanupPeriodDays` (believed to default to 30; verify).
- (2026-10-12) Add an R1a subgoal: fix :135/:217/:365, correct the PATH hint, add a >64 KB plan to the close-revision suite; ships in 0.10.1.
- (2026-10-12) The fix sweeps every script under `scripts/`, not only the three measured lines.
- (2026-10-12) The export script stays Python: `scripts/export-session.py`, with its suite at `dev/export-session/`.
- (2026-10-12) Add an R1a subgoal: /new-branch writes per-goal goal files with their subgoals, never stubs; ships in 0.10.1.
- (2026-10-12) The root `CLAUDE.md` also holds the workflow's `# Compact instructions`: the static half of `/smart-compact`'s Compose (§4.4: the Drop list and the Say-where convention), which every compaction reads, auto-compaction included. This amends "one permanent, conditional line" above; the compact instructions are part of the workflow, not a personal preference.

## Subgoals

- [~] 1. The plan scripts survive SIGPIPE: no reader exits before EOF on a pipe and kills its writer (`cat`, or `git show` under `--check`), starting with `close-revision.sh` at `:135`, `:217` and `:365`, and `die`'s hint no longer blames PATH or awk for a writer killed by SIGPIPE.
  Scope: every script under `plugins/workflow-coding/scripts/` and `scripts/lib/`, single- and multi-line awk programs alike, with `lib/plan-rules.sh`'s `die` shared by all of them; `dev/close-revision/suite.py`, its `mutants/` and `README.md`, and the suite of any other script the sweep changes; builds on nothing. Acceptance: `python3 -I dev/close-revision/suite.py` passes, including a new case that closes a plan larger than 64 KB, both the close and its `--check`. `--mutants` catches every mutant. Each other script the sweep changes gets a large-input case in its own suite. Every suite of a script that sources `lib/plan-rules.sh` still passes.
  > **Branch:** fix/plan-scripts-sigpipe
- [ ] 2. `/workflow-coding:session-handoff` writes `tmp/session-handoff.md` in three parts (Keep / Drop / Say where), and its text works when followed as a plain file. A new root `CLAUDE.md` holds the one conditional line that makes the next session read the handoff first and delete it once the user confirms, and the workflow's `# Compact instructions`.
  Scope: `plugins/workflow-coding/commands/session-handoff.md` (new) and `CLAUDE.md` at the repository root (new). It follows `/smart-compact` §4.4 in `tmp/subagent-refactor-plan.md` and is independent of 1. Acceptance: the command file needs no `$ARGUMENTS`, no `${CLAUDE_PLUGIN_ROOT}` and no `allowed-tools`. A session on the 0.10.0 driver, told to follow the file, writes `tmp/session-handoff.md` with the three parts, and a fresh session reads it before anything else through `CLAUDE.md`. `CLAUDE.md` also holds a `# Compact instructions` section with §4.4's Drop list and Say-where convention.
- [ ] 3. `/workflow-coding:session-export-full` exports a session's whole JSONL log, compactions included, through a script with a suite and a thin command. Subagent transcripts are optional, and the output goes outside the repo.
  Scope: `plugins/workflow-coding/scripts/export-session.py`, started from `tmp/export_session.py`; its suite under `dev/export-session/`; `plugins/workflow-coding/commands/session-export-full.md` (new); and verifying the default of `cleanupPeriodDays`. It is independent of 1 and 2. Acceptance: the suite passes, with cases for each of the four measured defects. Em dashes are encoded once. The `/compact` instructions are captured. The title comes from the output filename. A renamed session with several `custom-title` records takes its name from `<uuid>/custom-title.json`. Subagent transcripts appear only when asked for. The command exports a real session to a path outside the repo, and its text states the verified `cleanupPeriodDays` default.
- [ ] 4. Release `workflow-coding` 0.10.1: bump the version and document the two new commands.
  Scope: `plugins/workflow-coding/.claude-plugin/plugin.json`, `README.md`, `plugins/workflow-coding/README.md` and `plugins/workflow-coding/CLAUDE.md` (`.claude-plugin/marketplace.json` carries no version, and `dp-compile` depends on `workflow-coding` unpinned); builds on 1, 2, 3 and 5. Acceptance: `plugin.json` reads 0.10.1. After the merge, the marketplace install loads `workflow-coding` 0.10.1 with `/session-handoff` and `/session-export-full` listed. At the end of R1a, the session writes `tmp/session-handoff.md` by following `commands/session-handoff.md` as text, and the next session reads it first through the root `CLAUDE.md`.
- [ ] 5. `/new-branch` writes each per-goal goal file with its subgoals, never a stub: `propose-branch-plan.sh` reports the master-plan subgoal's `Scope: … Acceptance: …` lines, the command drafts each goal's subgoals from them and the scope discussion, and `locate-plan.sh` warns when the selected goal file has no subgoals.
  Scope: `scripts/propose-branch-plan.sh` (a new `scope:` report key), its suite and spec; `commands/new-branch.md` step 7's per-goal template and a rule never to write a goal file with no subgoals; `scripts/locate-plan.sh` (the warning), its suite and `locate-plan-spec.md`; Step 2 of `/step` and `/hitl-step` (a goal with no subgoals gets them proposed before work starts); the plugin's `CLAUDE.md` on `/new-branch`; and §4.2's "stub goal file" wording in `tmp/subagent-refactor-plan.md`. Independent of 1, 2 and 3. Acceptance: `propose-branch-plan.sh` reports `scope:` with the subgoal's continuation lines, and `—` for a standalone plan, and its suite has a case for each. A branch made from a revision subgoal gets goal files that each hold at least one `- [ ]` subgoal. `locate-plan.sh` warns on a selected goal file with no subgoals, and its suite has a case for it. Every suite of a script that sources `lib/plan-rules.sh` still passes.
