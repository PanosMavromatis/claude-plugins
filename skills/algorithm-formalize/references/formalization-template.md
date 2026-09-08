# Formalization template

**This file is the canonical definition of a formalization's structure.** The
`algorithm-formalize` skill explains *why* several of these sections carry the weight
they do; this file defines *what* they are. When the two appear to disagree, this one is
the form and the skill is the reasoning — but they should not disagree, and a change to
one is a change to both.

Copy the body below to the path the manifest's `[phases].formalization` template gives
for the algorithm, and fill in each section.

Sections marked *optional* may be omitted where they do not apply. Every other section is
mandatory, including the ones a particular algorithm answers briefly — **"this recurrence
has no backtrace" and "the parallel decomposition is undetermined" are answers, and
silence is not.**

---

# <Algorithm Name>

## Metadata

| Field | Value |
|-------|-------|
| Source | <paper title, authors, year, DOI or URL; or the implementation this was recovered from> |
| Derived from | <path> `sha256:`<hash> |
| Family | <sequence alignment / hidden Markov model / edit distance / ...> |
| Variant | <the family's variant, where it has them — global / local / semi-global; decode / forward / posterior> |
| Objective | <what is optimised, in which direction, and in which semiring> |
| Parallel decomposition | <one line; "undetermined" is legitimate. See the section below.> |
| Time complexity | <O(...)> |
| Space complexity | <O(...)> |
| Optimality | <optimal / heuristic / approximate> |
| Algorithm-specific params | <any parameters beyond this repository's usual signature> |

**`Derived from`** is the provenance record that decides staleness. It names the file this
document was written from and the SHA-256 of that file's contents, computed with the
file's own `dp-compile` provenance line excluded. This document is stale when the recorded
hash no longer matches. Leave it empty for a formalization written from an external source
— it then derives from nothing in the repository, and nothing in the repository can make
it stale.

**`Objective`** states what is optimised and in which direction — and is **never**
converted to a house convention. "Maximise total similarity (max-plus)" and "minimise
description length in bits (min-plus)" are both correct answers; normalising either into
the other inverts every comparison in the recurrence.

## Adaptations from Source

Every assumption the source left unnamed, and what was done about it. Mandatory even when
the adaptations look trivial — the trivial ones are documentation, and the non-trivial
ones are where bugs hide during implementation.

1. <what the source assumed, what this repository requires, and how the gap was closed>
2. ...

## Source Pseudocode

*Optional — include only if the source material contains pseudocode.*

Reproduce it verbatim, with a citation (title, figure or algorithm number, page). This is
a **reference snapshot for the human reviewer**, so they can compare the source against
this rendering without opening the source. It is not a starting point for transformation:
the rendering below is written fresh from the source's full description.

## Definitions

Every array, variable and symbolic constant used below, with its shape and what it means.

## Recurrence

**Boundary note.** State here that the pseudocode operates on pre-encoded integer inputs,
that encoding and decoding happen at the caller's boundary, and that no symbol operations
occur below. This is not part of the algorithm; it is the framing that makes the compiled
and parallel phases transliterations rather than rewrites.

<The recurrence, per `pseudocode-conventions-DP.md`.>

## Base Cases

<Initialization, including any boundary row or column that is not a data position.>

## Iteration Order

<The order in which cells are computed, as a procedural loop structure.>

## Backtrace

<The backtrace procedure, as a separate function, with the backtrace array's values
defined explicitly. "Follow the arrows back" is not a procedure. Where the algorithm
genuinely produces no backtrace, say so here in one line rather than omitting the
section.>

## Parallel decomposition

*Consumed by the CPU-parallel phase, which is where an assumption here becomes a race
rather than an error.*

State which cells may be computed concurrently and **why their dependencies permit it** —
the argument matters more than the name. Where it is not yet settled, write
"undetermined" and say what would settle it. That is a legitimate answer and a far better
one than a guess.

Do not assume every recurrence decomposes the same way. A two-dimensional matrix whose
cells depend on their neighbours has anti-diagonals that are mutually independent. A
recurrence that is one-dimensional over time with dense coupling between states has no
anti-diagonals at all, and decomposes — if at all — over something else entirely, such as
the states within one timestep, a batch of independent sequences, or an associative scan
over time.

**Any tie-breaking rule belongs here as well as in the recurrence.** Where more than one
predecessor can reach the same optimum, the choice between them is *contract*: two
correct backends that break ties differently will disagree, and the suite meant to prove
their equivalence will fail on a difference neither of them got wrong.

## Test Cases

Language-agnostic input/expected-output pairs that any implementation must satisfy. Not
test code — a behavioural specification expressed as data, independent of any framework.

### TC-01: <descriptive name>

    Input:  <inputs, as integer arrays and parameter values>
    Expect: <expected outputs and properties>

Each case states its **precision level**, and they are not interchangeable:

- **Exact** — the correct output is unambiguous: a specific value, a specific path.
- **Property-based** — several outputs are equally correct, so assert the value plus the
  structural properties that must hold.
- **Relational** — the test compares two runs rather than checking one: symmetry, or
  monotonicity in a parameter.

Required minimum coverage, adapted to the family:

- **Standard**: inputs that agree completely, partially, and not at all
- **Boundary**: empty input, both inputs empty, single-element input, badly asymmetric lengths
- **Structural**: whatever the family's optimal solution can contain that a naive one cannot
- **Parameter edge cases**: parameters that dominate the objective, and degenerate ones
- **Ties**: at least one case where two predecessors are exactly equal, exercising the
  tie-breaking rule. **Learned or measured parameters rarely tie**, so a suite drawn only
  from real data can pass while the rule is wrong — construct the tie deliberately.
- **Algorithm-specific**: cases from the source's own examples, adapted to this
  repository's encoding

## Notes

Observations, implementation considerations, and open questions. A living record: items
discovered during later phases are folded back here in separate commits.
