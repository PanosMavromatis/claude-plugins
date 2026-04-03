# FORMALIZATION.md Template

Use this template when creating a new algorithm formalization. Copy it to
`src/tokalign/algorithms/<n>/FORMALIZATION.md` and fill in each section.

Sections marked *optional* may be omitted when they do not apply. All other
sections are mandatory.

---

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

## Adaptations from Source

1. <what was changed, why, and what the source originally assumed>
2. ...

## Source Pseudocode

*Optional — include only if the source material contains pseudocode.*

<Reproduce the source's pseudocode verbatim here with citation (paper title,
figure/algorithm number, page). This is a reference snapshot for the human
reviewer — not a starting point for transformation.>

## Definitions

<Define all matrix names, variables, and symbolic constants used in the
pseudocode below. For example:

- M[i, j] — optimal alignment score ending with a match/mismatch at (i, j)
- X[i, j] — optimal score ending with a gap in sequence B at (i, j)
- Y[i, j] — optimal score ending with a gap in sequence A at (i, j)
- S — score matrix, 2D array of reals, size |Σ| × |Σ|
- a — integer array of length m (encoded sequence A)
- b — integer array of length n (encoded sequence B)
- g_o — gap opening penalty (negative)
- g_e — gap extension penalty (negative)
- T — traceback matrix of Direction values>

## Recurrence

**Boundary note.** This pseudocode operates on pre-encoded integer sequences.
The caller is responsible for encoding string symbols to integers via
`Alphabet.encode_pair()` before invocation and decoding the aligned integer
sequences back to strings via `Alphabet.decode()` after return. No string
operations occur within this pseudocode.

<Boxed recurrence block per pseudocode-conventions-DP.md.>

## Base Cases

<Base case initialization using compact single-line notation where appropriate.>

## Iteration Order

<Procedural loop structure showing the order in which cells are computed.>

## Traceback

<Traceback procedure as a separate function, using the conventions from
pseudocode-conventions-DP.md. Must define explicit traceback data structures
— do not use "follow the arrows back.">

## Test Cases

<Language-agnostic test specifications as input/expected-output pairs.
Format:

### TC-01: <descriptive name>

    Input:  a = [...], b = [...]
            S = <scoring description>
            g_o = ..., g_e = ...
    Expect: score = ...
            aligned_a = [...]
            aligned_b = [...]
            <additional properties>

Required minimum coverage (see SKILL.md for details):
- Standard cases: identical, partially overlapping, completely disjoint
- Boundary cases: empty inputs, single elements, asymmetric lengths
- Gap behavior: gaps at start, end, middle; multiple gaps
- Scoring edge cases: dominant gap penalties, degenerate matrices
- Algorithm-specific cases: features unique to this algorithm

Precision levels:
- Exact: when the correct output is unambiguous
- Property-based: when multiple correct outputs exist
- Relational: when testing relationships between runs>

## Notes

<Observations, implementation considerations, and open questions.
This section is a living record — items discovered during later phases
are folded back here in separate commits.>
