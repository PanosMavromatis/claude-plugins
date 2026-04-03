---
name: algorithm-formalize
description: >
  Use this skill when the user wants to formalize an alignment algorithm before
  implementation. Trigger when the user says "formalize," "pseudocode," "write up
  the algorithm," "prepare for implementation," or runs `/new-algorithm`. Also
  trigger on algorithm names (Needleman-Wunsch, Smith-Waterman, Hirschberg, Gotoh,
  Altschul, banded alignment, etc.) when no `FORMALIZATION.md` or `_python.py`
  exists for that algorithm in `src/tokalign/algorithms/<n>/`. Do NOT trigger
  if `_python.py` already exists — at that point, Phase 1 has started and this
  skill's window has closed.
---

# Algorithm Formalization Skill

## Context

This skill implements Phase 0 of the algorithm lifecycle: producing a
language-agnostic pseudocode rendering of an alignment algorithm before any Python
code is written. The formalization separates "did we understand the algorithm?"
from "did we implement it correctly?" and creates a version-control checkpoint
that can be reverted to if the Python prototype goes sideways.

The output is `FORMALIZATION.md`, written to the algorithm's directory at
`src/tokalign/algorithms/<n>/FORMALIZATION.md`. This file is committed as a
standalone stage gate before implementation begins.

### Downstream coupling

`FORMALIZATION.md` is not just a review artifact — it is the **specification**
that Phase 1 (`algorithm-prototype`) translates from. The translation from
formalization to Python is tight and nearly mechanical: every function in the
pseudocode becomes a Python function, the recurrence block maps to the inner
loop body, the traceback procedure becomes a separate function. Structural
deviations in Phase 1 require explicit justification.

This means the formalization must be precise, complete, and correct. Gaps or
ambiguities in the pseudocode become bugs in the implementation.

### Living document

`FORMALIZATION.md` is a living document. When edge cases are discovered during
any later phase (implementation, testing, code review, Cython translation), they
are **folded back into the formalization** rather than handled only in code. This
keeps the formalization as the single authoritative specification of the
algorithm's behavior across all backends.

## Prerequisites

Before proceeding, verify ALL of the following:

1. **Source material is available.** The user must have provided a paper (PDF),
   a URL to an online resource, or a detailed description of the algorithm. If
   no source material is present, stop and ask for it. Do not attempt to
   formalize from memory or general knowledge alone.

2. **The algorithm directory state is correct.** Either:
   - The directory `src/tokalign/algorithms/<n>/` does not exist yet (create it), OR
   - It exists but contains neither `FORMALIZATION.md` nor `_python.py`.
   If `_python.py` already exists, this skill's window has closed — do not proceed.

3. **You have read `_types.py`.** Before writing any pseudocode, read
   `src/tokalign/_types.py` in full to understand `Alphabet`, `ScoringMatrix`,
   and `AlignmentResult`. The formalization must target these types.

## Instructions

### Step 1: Read the source material

Read the provided source material in full. Do not skim. If the source is a paper,
read the algorithm description, the recurrence relations, the pseudocode (if any),
and the examples. Pay attention to:

- The DP recurrence and its base cases
- How the traceback is defined (implicit vs. explicit)
- What assumptions the paper makes about the alphabet, scoring, and gap penalties
- Whether the algorithm is global, local, or semi-global
- Time and space complexity

### Step 2: Identify embedded assumptions

Identify assumptions in the paper's presentation that conflict with tokalign's
model. Common ones to watch for:

- **Single-character symbols.** Many papers assume symbols are single characters
  (amino acids, nucleotides). tokalign uses multi-character string tokens. The
  formalization must use integer-indexed sequences, not character-based ones.
- **Specific scoring matrices.** Papers may reference BLOSUM, PAM, or other
  biological matrices. The formalization must use a generic 2D score matrix
  accessed by integer indices.
- **Fixed alphabet sizes.** Some papers assume |Σ| = 4 (DNA) or |Σ| = 20
  (protein). The formalization must work with arbitrary alphabet sizes.
- **Linear gap penalties.** tokalign uses affine gap penalties (`gap_open` +
  `gap_extend`). If the source uses linear penalties, the formalization must
  present the affine generalization.
- **Similarity vs. distance.** Some papers define the DP recurrence with max
  (similarity) and some with min (distance). Normalize to max (similarity),
  since that is what `ScoringMatrix.score()` returns.
- **Implicit traceback.** Papers often say "follow the arrows back" without
  defining a traceback data structure. The formalization must make traceback
  explicit.

### Step 3: Capture the source pseudocode (when present)

If the source material contains pseudocode, reproduce it verbatim for inclusion
in the "Source Pseudocode" section of `FORMALIZATION.md`. Include the citation
(paper title, figure/algorithm number, page).

This reproduction serves the human reviewer: they can compare the paper's
formulation against the tokalign rendering side by side without opening the
paper separately. The source pseudocode is a **reference snapshot**, not a
starting point for transformation.

If the source material does not contain pseudocode (e.g., the algorithm is
described only in prose, or the source is a conversational description from
the user), skip this step and omit the "Source Pseudocode" section from the
output.

### Step 4: Render the tokalign pseudocode

**Always produce a fresh rendering.** Do not transform the paper's pseudocode
into tokalign's notation. Instead, work from the paper's full algorithmic
description (prose, recurrences, examples, proofs) and render a new pseudocode
in the project's conventions.

This is true even when the paper's pseudocode is well-structured and appears
close to tokalign's model. A fresh rendering ensures the formalization is
authored in tokalign's voice and conventions, and prevents the agent from
inheriting structural choices from the paper that may not serve tokalign's
architecture.

Render the algorithm using the conventions defined in
`references/pseudocode-conventions-DP.md`. The pseudocode must reflect
tokalign's patterns:

- **Inputs are pre-encoded.** The pseudocode operates on integer arrays
  (post-`Alphabet.encode_pair()`), a 2D score matrix accessed by integer
  indices, and gap penalty parameters (`gap_open`, `gap_extend`).
- **The DP recurrence uses integer indices** and `S[a[i], b[j]]`, never
  string symbols.
- **Outputs** are the DP matrix, the traceback matrix (if applicable), the
  optimal score, and the aligned index sequences (pre-decode).
- **The encode/decode boundary is noted but is NOT part of the pseudocode.**
  The pseudocode covers the computation between encode and decode. A brief
  note at the top states that encoding and decoding happen at the caller
  boundary.

### Step 5: Write the header block

Every `FORMALIZATION.md` begins with a metadata header:

```markdown
# <Algorithm Name>

## Metadata

| Field | Value |
|-------|-------|
| Source | <paper title, authors, year, DOI or URL> |
| Alignment type | <global / local / semi-global> |
| Gap model | <linear / affine> |
| Time complexity | <O(...)> |
| Space complexity | <O(...)> |
| Optimality | <optimal / heuristic / approximate> |
| Algorithm-specific params | <list any params beyond the standard signature> |
```

### Step 6: Write the adaptations section

Document every adaptation from the source material's presentation to tokalign's
model. This section is mandatory even if the adaptations seem trivial.

```markdown
## Adaptations from Source

1. <What was changed and why>
2. <What was changed and why>
...
```

The trivial adaptations are documentation. The non-trivial ones are where bugs
hide during implementation.

### Step 7: Assemble and write `FORMALIZATION.md`

Write the complete file to `src/tokalign/algorithms/<n>/FORMALIZATION.md`.
The file structure is:

1. **Metadata** (Step 5) — header block with algorithm properties
2. **Adaptations from Source** (Step 6) — every change from the paper's model
3. **Source Pseudocode** (Step 3) — verbatim reproduction from the paper, with
   citation. *Omit this section if the source contains no pseudocode.*
4. **Definitions** — all matrix names, variables, and symbolic constants
5. **Recurrence** — boxed recurrence block per conventions
6. **Base Cases** — initialization
7. **Iteration Order** — procedural loop structure
8. **Traceback** — traceback procedure as a separate function
9. **Test Cases** — language-agnostic test specifications as input/expected-output
   pairs (see "Test cases" below)
10. **Notes** — observations, implementation considerations, and open questions

### Step 8: Hard stop

**Do not proceed to Python implementation.** Present the formalization to the
user for review. Explicitly say:

> "Review the formalization and the adaptations from the source material.
> When satisfied, commit it and run `/next-phase <n>` to begin the
> Python prototype."

Do not create `_python.py`, test files, registry entries, or any other
implementation artifacts. That is the `algorithm-prototype` skill's job,
and it reads the committed `FORMALIZATION.md` as its specification.

## Test cases

The formalization includes a **Test Cases** section: a language-agnostic
specification of input/expected-output pairs that any implementation must
satisfy. This is not test code — it is a behavioral specification expressed
as data, independent of any testing framework.

Test case specifications follow this format in `FORMALIZATION.md`:

```markdown
## Test Cases

### TC-01: Identical sequences

    Input:  a = [1, 2, 3], b = [1, 2, 3]
            S = identity matrix (match = 2.0, mismatch = -1.0)
            g_o = -5.0, g_e = -1.0
    Expect: score = 6.0
            aligned_a = [1, 2, 3]
            aligned_b = [1, 2, 3]
            no gaps in either sequence

### TC-02: Completely disjoint sequences
    ...
```

Each test case has a short identifier (`TC-01`, `TC-02`, ...), a descriptive
name, concrete inputs using integer-indexed sequences and score matrix
parameters, and concrete expected outputs including the score and alignment
properties.

### Required test cases

Every formalization must include at minimum:

**Standard cases:**
- Identical sequences (perfect match, no gaps)
- Partially overlapping sequences (some matches, some mismatches)
- Completely disjoint sequences (no symbols in common)

**Boundary cases:**
- Empty sequence (one input has length 0)
- Both inputs empty
- Single-element sequences
- One sequence much longer than the other

**Gap behavior:**
- Optimal alignment requires gaps at the start
- Optimal alignment requires gaps at the end
- Optimal alignment requires gaps in the middle
- Multiple gaps in the same alignment

**Scoring edge cases:**
- Gap penalties that dominate match scores (everything gets gapped)
- Very high match scores relative to gap penalties (no gaps preferred)
- Degenerate scoring matrix (all zeros, or all identical values)

**Algorithm-specific cases:**
- Cases that exercise algorithm-specific features (e.g., local vs. global
  behavior, affine vs. linear gap effects, banding constraints)
- Cases drawn from the source paper's examples, if any, adapted to use
  integer indices

### Precision level

Test cases specify expected behavior at the appropriate level of precision:

- **Exact** when the correct output is unambiguous: `score = 6.0`,
  `aligned_a = [1, 2, 3]`.
- **Property-based** when multiple correct outputs exist: `score = 6.0`,
  `no gaps in either sequence`, `all positions are matches`. This is common
  when multiple optimal alignments exist.
- **Relational** when the test validates a relationship:
  `score(a, b) = score(b, a)` (symmetry), or
  `score ≥ score with higher gap penalties`.

### Living specification

Like the pseudocode itself, the Test Cases section is a living document. When
Phase 1 implementation or testing reveals a case that should have been specified,
it is added to `FORMALIZATION.md` in a separate commit. Every backend translates
from the same test specifications.

## What this skill does NOT do

- **No Python, Cython, or Numba code.** Not even "starter" code or "scaffolding."
- **No test code.** Test *specifications* (input/expected-output pairs) belong
  here. Test *implementation* (pytest files, fixtures, assertions) is Phase 1's
  concern.
- **No optimization.** The formalization captures the algorithm as described in
  the source, adapted to tokalign's type system. Optimizations happen later.
- **No registry entries.** The algorithm is not registered until it has a working
  Python implementation.
- **No transformation of source pseudocode.** Even when the paper's pseudocode
  is close to tokalign's model, always render fresh. The human reviewer compares
  the source snapshot against the tokalign rendering.

## Gotchas

- **Papers often present traceback as implicit.** "Follow the arrows back" is not
  a traceback algorithm. The formalization must define a traceback matrix with
  explicit values at each cell (e.g., DIAG, UP, LEFT) and a procedure that reads
  it to produce the aligned sequences.

- **Affine gap penalties require additional DP matrices.** If the source uses
  linear penalties, the formalization should note this and present the affine
  generalization. Typically three matrices are needed: M (match/mismatch),
  X (gap in sequence A), Y (gap in sequence B). The recurrence becomes a
  system of three coupled recurrences.

- **Similarity vs. distance normalization.** The source may minimize edit
  distance while tokalign maximizes alignment score. The formalization must
  normalize to max (similarity). This is not just flipping min→max — the
  recurrence structure and base cases may change.

- **Index conventions vary between papers.** Some papers use 0-based indexing,
  some use 1-based. The formalization should use 0-based indexing (matching
  Python/numpy conventions) and note any conversion from the source's convention.

- **Gaps are a sentinel, not an index.** The formalization uses `GAP` as an
  abstract gap sentinel — it means "this position is a gap" without prescribing
  a representation. The concrete mapping to `alphabet.gap_index` (integer 3 in
  the current `Alphabet` implementation) is Phase 1's responsibility. Do not
  use `GAP_INDEX` or hardcode any specific integer in the formalization.

- **Do not defer to the paper's pseudocode structure.** The fresh rendering
  instruction exists because papers embed structural choices (variable naming,
  loop nesting, traceback approach) that may not fit tokalign's architecture.
  Even if the paper's pseudocode looks "good enough," always render fresh.

- **Edge cases found later must update this file.** If Phase 1 implementation
  or testing reveals an edge case not documented in the formalization, the fix
  is not just a code change — it is an amendment to `FORMALIZATION.md` in a
  separate commit, followed by a code update that matches.
