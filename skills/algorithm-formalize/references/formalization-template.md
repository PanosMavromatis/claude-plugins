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
has no backtrace", "the parallel decomposition is undetermined" and "there is no oracle"
are answers, and silence is not.**

---

# <Algorithm Name>

## Metadata

| Field | Value |
|-------|-------|
| Source | <forward: paper title, authors, year, DOI or URL. Reverse: the phase-1 file this was recovered from, by path and commit, plus the legacy implementation it was ported from and any written account of it> |
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

*Reverse entrance: retitle this section **Deviations from the legacy source**.*

**Forward** — every assumption the source left unnamed, and what was done about it.
Mandatory even when the adaptations look trivial: the trivial ones are documentation, and
the non-trivial ones are where bugs hide during implementation.

1. <what the source assumed, what this repository requires, and how the gap was closed>
2. ...

**Reverse** — every place the phase-1 implementation behaves differently from what it was
ported from, **and every place it deliberately does not**. A convention matched on purpose
leaves no trace in a diff, in the code, or in the tests, so its absence here is what a
later cleanup undoes. `skills/algorithm-recover/references/deviation-taxonomy.md` (from the plugin root)
sets out the
kinds and what each does to the document.

The recurrence above states **this repository's** behaviour, not the legacy source's.
Where a port deliberately fixed a defect, the fix is the specification and the original's
behaviour is recorded here — writing the original's into the recurrence would specify the
bug and make every later phase reproduce it.

## Source Pseudocode

*Optional — include only if the source material contains pseudocode. Reverse entrance:
retitle this section **Source Implementation** and quote the legacy source instead.*

Reproduce it verbatim, with a citation — title, figure or algorithm number, page for a
paper; file and line range for an implementation. This is a **reference snapshot for the
human reviewer**, so they can compare the source against this rendering without opening
the source. It is not a starting point for transformation: the rendering below is written
fresh from the source's full description.

Omit the section when there is nothing to snapshot — a purely conversational source
forward, or a recovery whose legacy implementation is not present in the repository. In
the reverse case say so in `Notes`, since the rendering then had no second text to be
checked against.

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

## Differential oracles

*"None" is a complete answer, and the commonest one — a formalization written from a paper
usually has no oracle. Say it in one line rather than omitting the heading.*

An **oracle** is a set of outputs produced by something other than the code in this
repository — almost always the legacy implementation a kernel was ported from, which left
its results beside its inputs. It is the only evidence about this algorithm that is not
downstream of code written here, which is what makes it worth a section of its own.

The manifest's `[algorithms.<name>].oracles` lists *where the files are*, because that is
layout and the plugin resolves it. This section records *what they mean*, which the
manifest cannot: it is read by a human deciding whether the comparison proves anything.

For each oracle, state:

1. **What produced it**, and when — the implementation, its version or commit, and the
   parameters it ran under. An oracle whose producer is unidentified is a file of numbers.
2. **Which inputs it pairs with.** An output is not a differential test on its own; the
   test is the pairing, so the inputs must be recorded and tracked beside the outputs. If
   the inputs are absent, say so — the oracle is then unusable and the section should say
   why it is being kept anyway, if it is.
3. **Whether the comparison is an equality check.** Frequently it is not: where the port
   deliberately fixed a defect in its source, the oracle is *wrong* exactly where the fix
   bites, and the two are expected to disagree there.
4. **Where they disagree, pinned exactly** — which cases, which positions, how many out of
   how many, and the reason, cross-referenced to the deviations section.

> **Pin the divergence; never widen the assertion to cover it.** "Agrees at 1268 of 1269
> positions, differing only at position 0, because the seeding defect was fixed" is a
> statement a test can enforce and a reviewer can check. "Mostly agrees" is a statement
> that silently accepts the *next* divergence too, which is the one nobody intended.

5. **Which TC-XX carries the comparison**, so the specification and the oracle are joined
   in both directions.

## Test Cases

Language-agnostic input/expected-output pairs that any implementation must satisfy. Not
test code — a behavioural specification expressed as data, independent of any framework.

*Reverse entrance: every case also records its **provenance** — `oracle` (an output the
legacy implementation produced), `extracted` (from an existing test), or `constructed`
(written now, from the recurrence). A case extracted from a passing test is one the
implementation already satisfies, so a reader must be able to tell a specified behaviour
from a ratified one.*

### TC-01: <descriptive name>

    Input:  <inputs, as integer arrays and parameter values>
    Expect: <expected outputs and properties>

Each case states its **precision level**, and they are not interchangeable:

- **Exact** — the correct output is unambiguous: a specific value, a specific path.
- **Property-based** — several outputs are equally correct, so assert the value plus the
  structural properties that must hold.
- **Relational** — the test compares two runs rather than checking one: symmetry,
  monotonicity in a parameter, or **agreement with a differential oracle**.

A differential case is relational rather than exact because the document cannot carry the
outputs: a corpus-sized oracle is thousands of values, and pasting them in would make the
specification a copy of a file that already exists. What the case states instead is the
*relation* — this implementation, run over those inputs, against that file, agreeing
everywhere except where the `Differential oracles` section says it will not.

Required minimum coverage, adapted to the family:

- **Standard**: inputs that agree completely, partially, and not at all
- **Boundary**: empty input, both inputs empty, single-element input, badly asymmetric lengths
- **Structural**: whatever the family's optimal solution can contain that a naive one cannot
- **Parameter edge cases**: parameters that dominate the objective, and degenerate ones
- **Differential**: one case per oracle the `Differential oracles` section records, stated
  relationally, including the pinned divergence where the comparison is not an equality
  check. **Where an oracle exists this case is not optional**, and it is the only case in
  the suite whose expected values were not produced by this repository.
- **Ties**: at least one case where two predecessors are exactly equal, exercising the
  tie-breaking rule. **Learned or measured parameters rarely tie**, so a suite drawn only
  from real data can pass while the rule is wrong — construct the tie deliberately.
- **Algorithm-specific**: cases from the source's own examples, adapted to this
  repository's encoding

## Notes

Observations, implementation considerations, and open questions. A living record: items
discovered during later phases are folded back here in separate commits.
