# 02 — Sweep the other plan scripts and lib for early-exit readers

**Goal**: [x]
> **Done:** Swept the other seven scripts and lib/plan-rules.sh. Outside close-revision.sh, no pipe reader stops before EOF, so no code changed.

- [x] Inventory every pipe in `scripts/*.sh` and `scripts/lib/plan-rules.sh` whose reader can stop before EOF: an awk `exit` (single- or multi-line), `head`, `grep -q`/`-m`, `sed …q`, or `read` in an `if`/`while`
  > **Note:** No other script has a pipe reader that stops before EOF; close-revision.sh's five were the only ones. Each pipe's reader is `sort` (build-agents-md.sh:63, check-agents-md.sh:58, locate-plan.sh:280 and :287, propose-branch-plan.sh:126, plan-rules.sh:88, :186 and :439), `tr` (build-agents-md.sh:99), or an awk with no `exit` (check-plan-index.sh:212 and :220, locate-plan.sh:217 and :381, propose-branch-plan.sh:83, :167 and :203, propose-merge-record.sh:104 and :203, plan-rules.sh:101). propose-revision.sh has no pipe. Nothing uses `head`, `grep -q`/`-m` or `sed …q`, and the only `read` loops, in the two AGENTS.md scripts, read a process substitution to EOF with no `break`.
- [x] Fix each with goal 01's pattern, or note why it is safe (a file argument, a here-string, or `exit` only in `END`)
  > **Note:** Nothing to fix, so goal 01's pattern stays in close-revision.sh alone. Every awk that exits early reads a file argument, so there is no writer to kill: propose-merge-record.sh:136 and :148, plan-rules.sh:95, :150, :170, :511 and :515. plan-rules.sh:326 (`GOALERR`) exits only in `END`, after EOF.
  > **Note:** Wrong for two callers. plan-rules.sh:511 and :515 do take a file argument, but close-revision.sh:277 and :282 pass /dev/stdin, the pipe from src. Fixed in goal 01a.
- [x] Name each script changed, for goal 04's large-input cases
  > **Note:** None. Goal 02 changed no script, so goal 04's "large-input case in the suite of each script that goal 02 changes" has nothing to cover.
