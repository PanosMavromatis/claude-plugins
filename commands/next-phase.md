---
description: "Advance an algorithm to the next implementation phase"
---

# /next-phase

Advance a single algorithm to the next implementation phase.

## Argument handling

`/next-phase` works on exactly one algorithm at a time.

**If no argument is provided**, stop immediately and ask the user:
> "Which algorithm would you like to advance? Please provide its name (e.g. `needleman_wunsch` or "Needleman-Wunsch")."
Do not attempt to infer or guess — wait for an explicit answer.

**If an argument is provided**, normalise it:
1. Strip leading/trailing whitespace.
2. Convert to lowercase.
3. Replace spaces, hyphens, and other separators with underscores.
   - Examples: `"Needleman-Wunsch"` → `needleman_wunsch`, `"smith waterman"` → `smith_waterman`
4. Look up the resulting name as a directory under `src/tokalign/algorithms/`.

**If the normalised name does not match any existing directory**:
- Compute the edit distance (or Levenshtein distance) between the normalised name and each directory name in `src/tokalign/algorithms/`.
- If exactly one candidate has an edit distance ≤ 3 (a plausible typo), ask:
  > "I couldn't find `<name>`. Did you mean `<candidate>`? (yes/no)"
  If the user confirms, proceed with the candidate. If not, ask them to enter the name again.
- If no candidate is within edit distance 3, tell the user:
  > "I couldn't find an algorithm named `<name>`. Here are the algorithms available: `<list>`. Please enter the name again."
  Wait for a new answer and repeat the lookup.

## Behavior

@references/phase-detection.md

1. Resolve the algorithm name (see above) and confirm the directory `src/tokalign/algorithms/<name>/` exists.
2. Apply the phase-detection logic above to determine the **effective phase**.
3. If the current phase is failing (tests fail or formalization not approved), stop and tell the user what needs to be fixed before advancing.
4. **Handle stale artifacts.** If the effective phase is earlier than the nominal phase (i.e., a prerequisite was updated after a downstream file was generated), target the first stale artifact for regeneration — not the next missing file. For example, if `FORMALIZATION.md` was modified after `_python.py`, the effective phase is 0 and the task is to regenerate `_python.py`, not to write `_cython.pyx`.
5. Route to the appropriate skill based on the effective phase:
   - Phase 0 → Phase 1: invoke `algorithm-prototype` skill.
   - Phase 1 → Phase 2: invoke `cython-translation` skill.
   - Phase 2 → Phase 3: invoke `gpu-parallelization` skill.
   - Phase 3 with no stale artifacts: report "This algorithm is fully implemented across all backends." and stop.
