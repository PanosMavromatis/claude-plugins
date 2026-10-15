# 02 — Write /agents-docs-migrate

**Goal**: [ ]

- [ ] The command tells the three states apart, (a) a legacy `CLAUDE.md`, (b) the dispatcher layout, (c) already migrated, by a script with `problem:`/`fix:` diagnostics, and a suite under `dev/` with mutants tests it.
- [ ] On (a) or (b) it spawns `docs-classifier`, and a table that leaves a section out or places one twice is caught before Checkpoint 1. The script also flags by rule every obsolete drop, every guide outside the agent's list, every dated line bound for `AGENTS.md` and every line over 2,000 characters.
  > **Note:** In goal 01's run c1, Claude Code ran the `Agent` call in the background unasked, and its report came in a later message rather than in the tool result: the command must wait for the hand-back before Checkpoint 1, as `/smart-commit`'s step 1 does.
  > **Note:** The script reads a single-line row `<file>:<n>` as `<n>-<n>` (goal 01, Q7), and any other source form fails it.
- [ ] Checkpoint 1 shows the destination table, with each target's `AGENTS.md` size in lines and in ≈ tokens by `/memory-check`'s estimate, warning above §4.3's ≈ 5k, and nothing is written before the user approves it.
  > **Note:** On pfsmgraph, goal 01's run c2 named 8 guides with no reader yet across 27 rows. Checkpoint 1 groups the rule flags by guide, one decision per new guide, rather than putting each row to the user.
- [ ] The command writes `AGENTS.md`, the guides and `_history/` by moving text verbatim, and Checkpoint 2 shows each file it wrote and every paragraph to be dropped, in full, with the ADR or plan it duplicates.
- [ ] Before the destructive step is offered, a script checks every paragraph of every source: each is found verbatim in a written destination, or lies in a row dropped with a reason. Any paragraph that is neither is named, and the destructive step is not offered. The suite has a case with one paragraph left out.
- [ ] Each monorepo component is a target, as `/agents-docs-init` handles them, and each `codex.md` becomes `docs/agents/[<path>/]codex-review/AGENTS.md`, from which `build-agents-md.sh` rebuilds `AGENTS.override.md`.
- [ ] On (c) the command says the repository is migrated and writes nothing; whether an `AGENTS.md` over 200 lines, §4.1's third input, is offered the classification is decided and recorded here.
