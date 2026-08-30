# feat/file-plans-command

**Status**: active
**Created**: 2026-08-30
**Subgoal**: Automate the plan-filing sweep

## Tasks

- [x] Write `scripts/file-plans.sh`: build the branch→revision map from the master plan's backlinks and enclosing headings, find plan directories sitting flat under `docs/plan/` that carry a `merged` stamp, and print the proposed `git mv` for each. Read-only — it must never move anything. Handle `DO.md` and `TODO.md` masters, and a repo with neither.
  > **Done:** `scripts/file-plans.sh` builds the branch→revision map from the master plan's backlinks and their enclosing headings, finds plan directories sitting flat under `docs/plan/` carrying a `merged` stamp, and prints the proposed `git mv`. Read-only throughout. Handles a `TODO.md` master, no master, and no `docs/plan/` at all. The backlink pattern is anchored to `^[[:space:]]*` — without it, prose that merely mentions `> **Branch:**` matches, and the master plan's own explanation of this mechanism does exactly that.
- [x] Make the two unplaceable cases explicit in the script's output: no backlink, and a heading with no revision number. Report them as skipped with the reason, and exit non-zero only on real errors, not on having nothing to do.
  > **Done:** Both underivable cases print a `skip` line naming the plan and the reason — no backlink, or a heading with no revision number. Exit is 0 for 'nothing to do' and reserved non-zero for real errors, so a hook or CI can distinguish 'clean' from 'broken'. Unmerged and unstamped plans are skipped silently, since they are simply still in flight.
- [x] Test the script against this repo's actual state and against synthetic edge cases — a plan with no backlink, a revision-1 heading, an already-filed plan, an active (unmerged) plan.
  > **Done:** Nine cases exercised in throwaway repos — normal file, no backlink, heading without a revision number, active plan, unstamped plan, already-filed plan, a prose decoy mentioning the backlink syntax, no master plan, no `docs/plan/`, and a `TODO.md` master. All correct. One test initially proved nothing: `rm` prompted interactively and left the file in place, so the 'no master plan' case was actually running against a master plan that still existed — the same interactive-`rm` trap that hung this project's very first cycle. Re-run with a clean fixture.
- [x] Write `commands/file-plans.md` with frontmatter following the `/agents-docs-build` precedent: script in `allowed-tools`, `git mv` deliberately omitted. The command runs the script, presents the proposal, confirms, executes, and commits on a branch.
  > **Done:** `commands/file-plans.md` follows the `/agents-docs-build` precedent — the script in `allowed-tools` via `${CLAUDE_PLUGIN_ROOT}`, with `Bash(git mv:*)` deliberately omitted so the harness prompt is a second gate, and a Guidelines bullet saying so is not drift. Six steps: propose, explain the skips, branch, execute verbatim, commit, report. It stops on a failed `git mv` rather than continuing, since a partial sweep is harder to reason about than a failed one.
- [x] Update README and `CLAUDE.md`: the filing sweep becomes `/file-plans`, with the derivation kept as the explanation of how it works rather than as the instruction.
  > **Done:** README gained a `/file-plans` command-table row and the sweep section now says to run it, keeping the `awk` as the explanation of how it works rather than the instruction. `CLAUDE.md` documents the script/command split, why the script stays read-only, and why the `^[[:space:]]*` anchor is load-bearing.


> **Dogfooded:** the command was run against this repo as the final check and filed its own two predecessors (`docs-settled-workflow`, `fix-plan-pointer-identity`) into `rev-3/`. Re-running immediately after reports "nothing to do", so it is idempotent, and both moved plans still resolve by name.