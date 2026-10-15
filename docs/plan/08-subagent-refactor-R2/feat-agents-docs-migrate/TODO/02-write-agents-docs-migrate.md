# 02 — Write /agents-docs-migrate

**Goal**: [ ]

- [ ] The command tells the three states apart, (a) a legacy `CLAUDE.md`, (b) the dispatcher layout, (c) already migrated, by a script with `problem:`/`fix:` diagnostics, and a suite under `dev/` with mutants tests it.
- [ ] On (a) or (b) it spawns `docs-classifier`, and a table that leaves a section out or places one twice is caught before Checkpoint 1.
- [ ] Checkpoint 1 shows the destination table, and nothing is written before the user approves it.
- [ ] The command writes `AGENTS.md`, the guides and `_history/` by moving text verbatim, and Checkpoint 2 shows each file it wrote and every paragraph to be dropped, in full, with the ADR or plan it duplicates.
- [ ] Before the destructive step is offered, a script checks every paragraph of every source: each is found verbatim in a written destination, or lies in a row dropped with a reason. Any paragraph that is neither is named, and the destructive step is not offered. The suite has a case with one paragraph left out.
- [ ] Each monorepo component is a target, as `/agents-docs-init` handles them, and each `codex.md` becomes `docs/agents/[<path>/]codex-review/AGENTS.md`, from which `build-agents-md.sh` rebuilds `AGENTS.override.md`.
- [ ] On (c) the command says the repository is migrated and writes nothing; whether an `AGENTS.md` over 200 lines, §4.1's third input, is offered the classification is decided and recorded here.
