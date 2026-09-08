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
4. Look up the resulting name in the manifest's `[algorithms]` table.

**If the normalised name does not match any existing directory**:
- Compute the edit distance between the normalised name and each key in `[algorithms]`.
- If exactly one candidate has an edit distance ≤ 3 (a plausible typo), ask:
  > "I couldn't find `<name>`. Did you mean `<candidate>`? (yes/no)"
  If the user confirms, report on that algorithm. If not, ask them to enter the name again.
- If no candidate is within edit distance 3, tell the user:
  > "I couldn't find an algorithm named `<name>`. Here are the algorithms available: `<list>`. Please enter the name again."
  Wait for a new answer and repeat the lookup.

**If no argument is provided**, ask the user:
> "No algorithm name was provided. Should I report on all implemented algorithms? (yes/no)"
- If yes, run the report for every key in the manifest's `[algorithms]` table.
- If no, ask which specific algorithm they want to check and wait for an answer.

## The manifest comes first

@references/manifest.md

Resolve every path, command and algorithm name through the manifest above. If the
repository has no `dp-compile.toml`, stop and say so with the template — do not
proceed against an assumed layout.

## Phase detection

@references/phase-detection.md

Apply the phase-detection logic above to each algorithm being checked.

## Report format

Produce a clear, concise status report for each algorithm checked.

**Report the artifacts, not a single phase number.** The nominal phase is one line of the
report rather than its conclusion: under recorded provenance the artifacts form a graph,
and for an algorithm whose formalization was recovered from its kernel there is no single
number that says both what exists and what is trustworthy. A table of five rows says both
without having to choose.

- Algorithm name, and the path each declared phase resolves to.
- **Nominal phase** — the highest-numbered declared phase whose file exists.
- **One row per declared phase**, with its state from the phase-detection step: `absent`,
  `fresh`, `stale`, or `blocked`. For a `stale` row, name the source whose change made it
  stale. For a `blocked` row, name the stale ancestor it is waiting on.
- Phases the manifest **does not declare**, listed once as not applicable to this
  repository. An omitted `cuda` is a decision, and a report that simply stops at 3 without
  saying so reads like an unfinished algorithm.
- **Test status for `fresh` backends only** — pass / fail / not run. Say explicitly that
  stale and blocked backends were not tested, and why: their source may disagree with what
  they were derived from, so a pass and a failure are equally uninformative.
- **Any oracle the manifest declares that the suite does not exercise**, named. It is the
  only check in the repository that is not downstream of code written here, so an unused
  one is the difference between a suite that verifies the algorithm and one that verifies
  its own internal consistency.
- Any provenance header that was missing, with the file named — the mtime fallback is in
  use for that file and the report is where that becomes visible.
- For phase 0: whether the formalization has been reviewed and approved, and **which
  entrance produced it** — forward from source material (`Derived from` empty) or recovered
  from the phase-1 kernel (`Derived from` naming it). The two carry different weight: a
  recovered document was read off the code it now governs, so a reader deciding how far to
  trust it needs to know which one is in front of them.

After the report, **stop**. Do not suggest running `/next-phase`, do not offer to continue implementation, and do not speculate about what should happen next.
