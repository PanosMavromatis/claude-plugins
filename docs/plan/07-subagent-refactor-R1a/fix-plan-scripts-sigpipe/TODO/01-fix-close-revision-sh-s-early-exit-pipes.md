# 01 — Fix close-revision.sh's early-exit pipes

**Goal**: [x]
> **Note:** close-revision.sh has five pipe readers that exit early, not three: :135, :177 (layout under --check), :194 (stamp's index line), :217 and :365. :236, :248, :260, :285 and :342 read to EOF. Every awk in lib/plan-rules.sh reads a file argument, so it has no writer to kill.

- [x] Inventory every pipe reader in close-revision.sh, and which of them exit before EOF
- [x] Replace each early `exit` with a guard that reads to EOF (`got { next }` / `found { next }`), with the rule stated once above `src()`
- [x] The existing suite passes: 58 of 58
- [x] `--mutants` catches every mutant, and none went stale against the edited lines
  > **Note:** First run after the fix: 40 mutants, 36 killed, 0 survived, 4 stale (c05, c06, c08, c19). Their patches' context was the edited lines (:194 twice, :217, :365). Each was rebased by applying the same one-line mutation to the edited script and taking `diff -u`, so the mutation is unchanged.
  > **Note:** Second run, with the rebased patches: 40 of 40 killed, 0 survived, 0 stale.
