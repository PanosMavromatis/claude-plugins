---
name: algorithm-formalize
description: >
  Use this skill when the user wants to formalize a dynamic-programming algorithm
  before implementation. Trigger when the user says "formalize," "pseudocode,"
  "write up the algorithm," "prepare for implementation," or runs `/new-algorithm`.
  Also trigger on the name of a DP algorithm (Needleman-Wunsch, Smith-Waterman,
  Hirschberg, Gotoh, Viterbi, Baum-Welch, forward-backward, banded alignment, etc.)
  when neither its formalization nor its phase-1 file exists at the paths the
  manifest's `[phases]` templates give for it. Do NOT trigger if the phase-1 file
  already exists — at that point phase 1 has started and this skill's window has
  closed.
---

# Algorithm Formalization Skill

## Context

This skill implements the `formalization` stage of the algorithm lifecycle:
producing a language-agnostic pseudocode rendering of a dynamic-programming
algorithm before any Python code is written. The formalization separates "did we
understand the algorithm?" from "did we implement it correctly?" and creates a
version-control checkpoint that can be reverted to if the Python prototype goes
sideways.

The output is written to the path the manifest's `[phases].formalization`
template gives for this algorithm. It is committed as a standalone stage gate
before implementation begins.

**Read the manifest's `[project].invariants` documents before writing a line of
pseudocode.** They state what a kernel in this repository must satisfy, and they
exist precisely because those rules are not discoverable from the source material
or from the surrounding code. A formalization that contradicts one of them is
wrong in a way no later phase will catch, because every later phase translates
from it faithfully.

### Downstream coupling

`FORMALIZATION.md` is not just a review artifact — it is the **specification**
that Phase 1 (`algorithm-prototype`) translates from. The translation from
formalization to Python is tight and nearly mechanical: every function in the
pseudocode becomes a Python function, the recurrence block maps to the inner
loop body, the backtrace procedure becomes a separate function. Structural
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

2. **Neither the formalization nor the phase-1 file exists yet**, at the paths
   the manifest's `[phases]` templates give for this algorithm. If the phase-1
   file already exists, this skill's forward window has closed — do not proceed.
   *(An existing implementation with no formalization is not this skill's job
   either; it is the reverse entrance, which recovers a formalization from code.)*

3. **You have read the repository's own vocabulary.** Before writing any
   pseudocode, read the manifest's `[project].encoder` documents, which define how
   symbols map to integers, and enough of an existing algorithm to see the shape
   the repository writes to — its entry point, its parameter object, its result
   type. **The plugin knows none of these and must not assume them.** Read them
   from the code, and where the repository has no algorithm yet, ask rather than
   invent.

## Instructions

### Step 1: Read the source material

Read the provided source material in full. Do not skim. If the source is a paper,
read the algorithm description, the recurrence relations, the pseudocode (if any),
and the examples. Pay attention to:

- The DP recurrence and its base cases
- How the backtrace is defined (implicit vs. explicit)
- **What is being optimised, and in which direction** — a maximised similarity, a
  minimised cost, a maximised probability, a minimised description length. This is the
  single most consequential thing to get right; see Step 2.
- What the source assumes about its symbols, its parameters, and its scoring
- The variant being described, where the family has variants (global / local /
  semi-global for alignment; decode / forward / posterior for an HMM)
- Time and space complexity

### Step 2: Identify embedded assumptions

**A source states its recurrence under assumptions its authors never had to name**,
because within their field those assumptions are simply how things are. Those unnamed
assumptions are exactly what the formalization must surface: they are invisible in the
source, they do not survive contact with a different repository, and they become bugs
that read like correct code. Finding them is most of this step's value.

Three generalise across every family:

- **The objective and its direction.** Some sources maximise (a similarity, a
  probability); some minimise (a distance, a cost, a description length). **Record what
  this algorithm optimises and in which direction, and do not normalise it to anything.**
  An earlier version of this skill said to normalise everything to max, which is a
  correct instruction for one family and a catastrophe for another: an HMM decode
  accumulating `-log2(p)` is minimising a *description length in bits*, which grows as
  the probability falls, so a port that reaches for `max` inverts every comparison. Worse,
  such a source's own naming may hide it — a variable suffixed as a probability may hold
  bits. State the semiring explicitly: max-plus, min-plus, max-product, and so on.
- **Implicit backtrace.** Sources routinely say "follow the arrows back" without defining
  a data structure. The formalization must define the backtrace array explicitly, say what
  its values mean, and give the procedure that reads it.
- **Index conventions and off-by-one geometry.** Sources differ over 0- and 1-based
  indexing, and some families have a genuine asymmetry the reader must not smooth away —
  a path over *N* observations may visit *N+1* states, and a matrix may carry a boundary
  row that is not a data position.

The rest are family-specific. Two worked instances:

**Sequence alignment.** Papers assume single-character symbols (amino acids,
nucleotides) where a repository may use multi-character tokens, so the pseudocode must
be integer-indexed rather than character-based. They reference specific substitution
matrices (BLOSUM, PAM) where the formalization needs a generic score matrix read by
integer index. They assume a fixed alphabet size, |Σ| = 4 or 20, where it must be
arbitrary. And they often use linear gap penalties where the repository's model is
affine, so the formalization presents the affine generalisation.

**Hidden Markov models.** The literature is almost uniformly *state-emission* — a symbol
emitted by the state, parameterised `B[state, symbol]`. A repository may be
*arc-emission*, emitting while crossing a transition, parameterised by source state,
destination state and symbol. Every textbook and every library is the other formulation,
so this is the assumption most likely to be lost in translation, and it changes the
recurrence rather than just the notation — the emission factor depends on both endpoints
and so cannot be hoisted out of the inner loop.

**Where the manifest's `[project].invariants` documents state a rule, the rule wins.**
The source is evidence about the algorithm; the invariants are the repository's decisions
about it, and a source cannot overrule them by not having heard of them.

### Step 3: Capture the source pseudocode (when present)

If the source material contains pseudocode, reproduce it verbatim for inclusion
in the "Source Pseudocode" section of `FORMALIZATION.md`. Include the citation
(paper title, figure/algorithm number, page).

This reproduction serves the human reviewer: they can compare the source's
formulation against this repository's rendering side by side, without opening the
source separately. The source pseudocode is a **reference snapshot**, not a
starting point for transformation.

If the source material does not contain pseudocode (e.g., the algorithm is
described only in prose, or the source is a conversational description from
the user), skip this step and omit the "Source Pseudocode" section from the
output.

### Step 4: Render the pseudocode

**Always produce a fresh rendering.** Do not transform the source's pseudocode into
this repository's notation. Work instead from the source's full algorithmic description
— prose, recurrences, examples, proofs — and render new pseudocode in the repository's
conventions.

This holds even when the source's pseudocode is well structured and looks close to what
is wanted. A fresh rendering keeps the formalization in the repository's voice, and stops
structural choices being inherited from a source that was solving a different problem.

Render using the conventions in `references/pseudocode-conventions-DP.md`. Three
properties are required of the pseudocode whatever the family:

- **Inputs are pre-encoded, and the encode/decode boundary is *not* part of the
  pseudocode.** Symbols become integers before the recurrence begins and are decoded
  after it ends; the pseudocode covers only what happens in between, with a note at the
  top saying so. This is what makes the later compiled and GPU phases mechanical
  transliterations rather than rewrites — they never touch a string type.
- **The recurrence is written over integer indices**, never over symbols.
- **Outputs are stated explicitly** — the DP array, the backtrace array where one
  exists, the optimal value, and the recovered path or sequence in its pre-decode form.

What those arrays and parameters *are* is family-specific and comes from Step 2. For
alignment: two encoded sequences, a score matrix read by integer index, gap parameters.
For an HMM decode: encoded observations, initial-state parameters, transition
parameters, emission parameters.

### Step 5: Write the header block

**The structure is defined in `references/formalization-template.md`, which is canonical.
Do not restate it here or reinvent it.** Open the template, copy its body, and fill in the
metadata table it defines. What follows is the reasoning behind the rows that are easiest
to fill in badly.

Four of these rows carry more weight than their length suggests.

**`Derived from`** is the provenance record, and it is what decides staleness: this
document is stale when the recorded hash no longer matches the current hash of the file
at that path. Compute the hash over the file with its own `Derived from` row excluded, so
that re-stamping a file never invalidates what depends on it. The row also records
*direction*: a formalization written from a source paper derives from nothing in the
repository and leaves it empty, while one recovered from an existing implementation names
that implementation — which is why editing the kernel then correctly marks the document
stale, and not the reverse.

**`Objective`** exists because normalising it away is a real and expensive mistake; see
Step 2.

**`Parallel decomposition`** is written here and consumed much later, by the
CPU-parallel phase. State it if the source or the recurrence's structure settles it, and
write "undetermined" if not — **"undetermined" is a legitimate value and far better than
a guess**, because the parallel phase is where an assumed decomposition becomes a race
rather than an error. Not every recurrence admits the same decomposition: a
two-dimensional alignment matrix has anti-diagonals whose cells are mutually independent,
while a recurrence that is one-dimensional over time with dense coupling between states
has no anti-diagonals at all and must be decomposed some other way.

### Step 6: Write the adaptations section

Document every adaptation from the source material's presentation to this
repository's model — every assumption surfaced in Step 2 and what was done about it.
This section is mandatory even if the adaptations seem trivial. The trivial ones are
documentation; the non-trivial ones are where bugs hide during implementation.

```markdown
## Adaptations from Source

1. <What was changed and why>
2. <What was changed and why>
...
```

The trivial adaptations are documentation. The non-trivial ones are where bugs
hide during implementation.

### Step 7: Assemble and write the formalization

Write the complete file to the path the manifest's `[phases].formalization` template
gives for this algorithm, creating any directories it names. **The section order and the
mandatory set are `references/formalization-template.md`'s**, and one rule there is worth
repeating because it is the one most often broken: a section whose answer is short is
still a section. "This recurrence has no backtrace" and "the parallel decomposition is
undetermined" are answers; omitting the heading is not, because a reader then cannot tell
a considered answer from an oversight.

### Step 8: Hard stop

**Do not proceed to Python implementation.** Present the formalization to the
user for review. Explicitly say:

> "Review the formalization and the adaptations from the source material.
> When satisfied, commit it and run `/dp-compile:next-phase <name>` to begin the
> Python prototype."

Create no implementation artifacts of any kind — no phase-1 file, no test file, no
backend-registry entry, no build-manifest line. Those belong to `algorithm-prototype`,
which reads the committed formalization as its specification.

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
- **No optimization.** The formalization captures the algorithm as the source
  describes it, adapted to this repository's model. Optimizations happen later.
- **No backend registration.** An algorithm is not registered until it has a working
  phase-1 implementation.
- **No transformation of source pseudocode.** Even when the source's pseudocode is
  close to what is wanted, always render fresh. The human reviewer compares the source
  snapshot against this repository's rendering.

## Gotchas

- **Papers often present backtrace as implicit.** "Follow the arrows back" is not
  a backtrace algorithm. The formalization must define a backtrace matrix with
  explicit values at each cell (e.g., DIAG, UP, LEFT) and a procedure that reads
  it to produce the aligned sequences.

- **Affine gap penalties require additional DP matrices.** If the source uses
  linear penalties, the formalization should note this and present the affine
  generalization. Typically three matrices are needed: M (match/mismatch),
  X (gap in sequence A), Y (gap in sequence B). The recurrence becomes a
  system of three coupled recurrences.

- **Never normalise the objective's direction.** A source may minimise where the
  repository maximises, or the reverse, and the temptation is to convert one to the
  other so everything reads alike. Do not: record what *this* algorithm optimises, in
  the direction it optimises it, in the `Objective` metadata row. Converting is not
  merely flipping `min` to `max` — the recurrence structure, the base cases and the
  identity element all change with the semiring, and a conversion done silently is
  indistinguishable from a bug. An earlier version of this skill instructed the
  opposite, which was correct for one family and inverted every comparison in another.

- **Index conventions vary between papers.** Some papers use 0-based indexing,
  some use 1-based. The formalization should use 0-based indexing (matching
  Python/numpy conventions) and note any conversion from the source's convention.

- **Reserved symbols are sentinels, not integers.** Where a family needs a symbol
  standing for something other than an observation — a gap, a padding position, an
  unknown token — the formalization names it as an abstract sentinel and says what it
  means. **It never states which integer it is.** The concrete code belongs to the
  repository's encoder, which the manifest's `[project].encoder` documents describe, and
  it is phase 1's job to look it up. This is not a style preference: the numbering does
  change between repositories and has changed within one, so a formalization that
  hardcoded an index would have been silently wrong from the day the encoder was
  renumbered, with no test able to see it.

- **Do not defer to the source's pseudocode structure.** The fresh-rendering
  instruction exists because a source embeds structural choices — variable naming, loop
  nesting, how the backtrace is carried — that suited its own setting and may not suit
  this repository's. Even if the source's pseudocode looks "good enough", always render
  fresh.

- **Edge cases found later must update this file.** If Phase 1 implementation
  or testing reveals an edge case not documented in the formalization, the fix
  is not just a code change — it is an amendment to `FORMALIZATION.md` in a
  separate commit, followed by a code update that matches.
