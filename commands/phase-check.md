---
description: "Report the implementation phase and staleness status of one or all algorithms"
---

# /phase-check

Report the implementation status of one algorithm, or all algorithms. This is a **reporting command only** — it checks, reports, and exits. It never initiates or suggests continuing implementation.

## Argument handling

**If an argument is provided**, normalise it and resolve it to an algorithm directory:
1. Strip leading/trailing whitespace.
2. Convert to lowercase.
3. Replace spaces, hyphens, and other separators with underscores.
   - Examples: `"Needleman-Wunsch"` → `needleman_wunsch`, `"smith waterman"` → `smith_waterman`
4. Look up the resulting name as a directory under `src/tokalign/algorithms/`.

**If the normalised name does not match any existing directory**:
- Compute the edit distance between the normalised name and each directory under `src/tokalign/algorithms/`.
- If exactly one candidate has an edit distance ≤ 3 (a plausible typo), ask:
  > "I couldn't find `<name>`. Did you mean `<candidate>`? (yes/no)"
  If the user confirms, report on that algorithm. If not, ask them to enter the name again.
- If no candidate is within edit distance 3, tell the user:
  > "I couldn't find an algorithm named `<name>`. Here are the algorithms available: `<list>`. Please enter the name again."
  Wait for a new answer and repeat the lookup.

**If no argument is provided**, ask the user:
> "No algorithm name was provided. Should I report on all implemented algorithms? (yes/no)"
- If yes, run the report for every directory found under `src/tokalign/algorithms/`.
- If no, ask which specific algorithm they want to check and wait for an answer.

## Phase detection

@references/phase-detection.md

Apply the phase-detection logic above to each algorithm being checked.

## Report format

Produce a clear, concise status report for each algorithm checked. Include:
- Algorithm name and directory path.
- Effective phase (e.g. "Phase 1 — Python backend").
- Whether the effective phase differs from the file-existence phase and why (i.e., which file is stale and which prerequisite was modified more recently).
- For each present, non-stale backend: test status (pass / fail / not run).
- For Phase 0: whether the formalization has been reviewed and approved.

After the report, **stop**. Do not suggest running `/next-phase`, do not offer to continue implementation, and do not speculate about what should happen next.
