# Pseudocode Conventions — Dynamic Programming Algorithms

This document defines the notation standard for the formalizations the
`algorithm-formalize` skill produces. It is about notation only: what the pseudocode
must *say* about a given algorithm is the repository's business, stated in the manifest's
`[project].invariants`.

These conventions are specific to **dynamic programming algorithms**, which is the family
this plugin exists for. If an algorithm does not fit the DP mould (divide-and-conquer,
heuristic search, sampling methods), notify the user immediately. The appropriate response is either:

- Custom instructions provided in the Claude Code session for that specific
  algorithm, or
- A new conventions document (`pseudocode-conventions-<FAMILY>.md`) tailored to
  that algorithm family.

Do not force a non-DP algorithm into this template.

---

## Design Principles

1. **Language-agnostic.** The pseudocode must be translatable to Python, Rust,
   Haskell, C/C++, or any other language without carrying idioms from any of them.
   No list comprehensions, no pattern matching syntax, no pointer arithmetic,
   no generator expressions.

2. **Math-flavored.** Prefer mathematical notation over programming notation.
   The reader should feel like they are reading a textbook algorithm description,
   not source code in a language with the keywords stripped out.

3. **DP recurrences are mathematical.** The core recurrence relation is expressed
   as a mathematical formula, not as nested conditionals in procedural code. This
   matches how papers present DP algorithms and makes verification against the
   source material straightforward.

4. **Procedural scaffolding surrounds the math.** Initialization, iteration order,
   backtrace, and output construction are expressed in procedural pseudocode. The
   recurrence itself is a formula embedded within this scaffolding.

5. **Integer indexing is baked in; nothing else is.** The pseudocode operates on
   pre-encoded integer inputs, and the recurrence indexes arrays by integer throughout.
   That is a property of the computational model rather than an implementation detail,
   and it is what makes the compiled and parallel phases transliterations. **What those
   arrays contain and which parameters exist are the algorithm family's**, not this
   document's — a score matrix and gap penalties belong to one family, transition and
   emission parameters to another.

---

## General Notation

### Assignment and comparison

| Operation | Notation | NOT this |
|-----------|----------|----------|
| Assignment | `x ← 5` | `x = 5`, `x := 5` |
| Equality test | `x = y` | `x == y` |
| Inequality | `x ≠ y` | `x != y` |
| Less/greater | `x < y`, `x ≤ y`, `x > y`, `x ≥ y` | `x <= y`, `x >= y` |

### Arithmetic

| Operation | Notation |
|-----------|----------|
| Standard | `+`, `-`, `×`, `/` |
| Integer division | `⌊a / b⌋` |
| Modulo | `a mod b` |
| Negation | `-x` |
| Absolute value | `|x|` |
| Maximum | `max(a, b)` or `max(a, b, c)` |
| Minimum | `min(a, b)` |

### Control flow

**Conditionals:**

```
if <condition> then
    <body>
else if <condition> then
    <body>
else
    <body>
end if
```

**Bounded loops:**

```
for i ← 0 to n - 1 do
    <body>
end for
```

The range is **inclusive on both ends**: `for i ← 0 to n - 1` iterates
i = 0, 1, 2, ..., n - 1. To iterate in reverse:

```
for i ← n - 1 downto 0 do
    <body>
end for
```

**Conditional loops:**

```
while <condition> do
    <body>
end while
```

### Functions

```
function ALIGN(a, b, S, g_o, g_e)
    Input:  a — integer array of length m (encoded sequence A)
            b — integer array of length n (encoded sequence B)
            S — score matrix, 2D array of reals, size |Σ| × |Σ|
            g_o — real (gap opening penalty, negative)
            g_e — real (gap extension penalty, negative)
    Output: AlignmentResult containing score, aligned index sequences,
            and backtrace matrix

    <body>

    return <result>
end function
```

**Input/Output blocks are mandatory.** Every function begins with a declaration
of its inputs (with types and brief descriptions) and its output. This is not
a comment — it is part of the pseudocode structure.

### Early return and special values

| Concept | Notation |
|---------|----------|
| Return | `return <value>` |
| Negative infinity | `-∞` |
| Positive infinity | `+∞` |
| Undefined / not set | `NIL` |

---

## Data Structure Notation

### Arrays

- **1D array creation:** `A ← new array of size n, initialized to 0`
- **Access:** `A[i]` (0-based indexing)
- **Length:** `|A|` or `length(A)`

### Matrices (2D arrays)

- **Creation:** `M ← new matrix of size (m + 1) × (n + 1), initialized to 0`
- **Access:** `M[i, j]` (comma-separated indices, not `M[i][j]`)
- **Dimensions:** `rows(M)`, `cols(M)`

The comma notation `M[i, j]` is deliberate — it is the standard mathematical
convention and avoids suggesting row-then-column pointer chasing, which is a
C/Python implementation detail.

### Records (structured return values)

```
record AlignmentResult
    score : real
    aligned_a : integer array
    aligned_b : integer array
    backtrace : matrix
end record
```

Use `record` for structured types. Field access uses dot notation: `result.score`.

### Enumerations (backtrace directions)

```
enum Direction
    DIAG    — match or mismatch (diagonal move)
    UP      — gap in sequence B (vertical move)
    LEFT    — gap in sequence A (horizontal move)
end enum
```

For affine gap models with multiple matrices, extend as needed:

```
enum Direction
    DIAG        — match/mismatch from M matrix
    UP_OPEN     — gap opening in B (transition M → Y)
    UP_EXTEND   — gap extension in B (stay in Y)
    LEFT_OPEN   — gap opening in A (transition M → X)
    LEFT_EXTEND — gap extension in A (stay in X)
end enum
```

---

## DP-Specific Notation

### Recurrence relations

The DP recurrence is the heart of every alignment algorithm. Express it as a
**mathematical formula block**, visually separated from procedural code:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   M[i, j] = max { M[i-1, j-1] + S[a[i], b[j]],        │
│                  { X[i-1, j-1] + S[a[i], b[j]],        │
│                  { Y[i-1, j-1] + S[a[i], b[j]]  }      │
│                                                         │
│   X[i, j] = max { M[i-1, j] + g_o,                     │
│                  { X[i-1, j] + g_e          }           │
│                                                         │
│   Y[i, j] = max { M[i, j-1] + g_o,                     │
│                  { Y[i, j-1] + g_e          }           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Rules for recurrence blocks:**

1. **Box them.** Use the `┌─┐ │ │ └─┘` border to visually distinguish the
   mathematical core from procedural scaffolding.
2. **Use curly-brace grouping** for `max` and `min` over multiple alternatives.
   Each alternative on its own line, aligned.
3. **Name the matrices.** Use single uppercase letters (M, X, Y, D, etc.) with
   clear definitions stated before the recurrence block.
4. **Index the sequences with array notation.** Write `a[i]` to mean "the i-th
   element of encoded sequence a," then use `S[a[i], b[j]]` for the score lookup.
5. **Keep gap penalties symbolic.** Use `g_o` for gap_open and `g_e` for
   gap_extend. Do not substitute numeric values.

### Base cases

Base cases immediately follow the recurrence block, in a clearly labeled section:

```
Base cases:
    M[0, 0] ← 0
    M[i, 0] ← g_o + i × g_e    for i ← 1 to m
    M[0, j] ← g_o + j × g_e    for j ← 1 to n
    X[i, 0] ← -∞               for i ← 0 to m
    Y[0, j] ← -∞               for j ← 0 to n
```

Use the compact `for` notation on a single line when the base case is a simple
fill along a row or column.

### Iteration order

State the iteration order explicitly after the base cases:

```
Iteration order:
    for i ← 1 to m do
        for j ← 1 to n do
            compute M[i, j], X[i, j], Y[i, j] per recurrence above
            record backtrace[i, j] ← direction of the maximizing term
        end for
    end for
```

This is where the pseudocode transitions from mathematical to procedural. The
recurrence block defines *what* is computed; the iteration order defines *when*.

### Backtrace

Backtrace is expressed as a separate procedure, not inlined into the main
function. This matches the conceptual separation (forward pass computes scores,
backward pass recovers the alignment) and will map cleanly to separate functions
in implementation.

```
function TRACEBACK(T, a, b, i_start, j_start)
    Input:  T — backtrace matrix of Direction values
            a — integer array (encoded sequence A)
            b — integer array (encoded sequence B)
            i_start — starting row index for backtrace
            j_start — starting column index for backtrace
    Output: (aligned_a, aligned_b) — pair of integer arrays with
            GAP inserted at gap positions

    aligned_a ← empty list
    aligned_b ← empty list
    i ← i_start
    j ← j_start

    while i > 0 or j > 0 do
        if T[i, j] = DIAG then
            prepend a[i] to aligned_a
            prepend b[j] to aligned_b
            i ← i - 1
            j ← j - 1
        else if T[i, j] = UP then
            prepend a[i] to aligned_a
            prepend GAP to aligned_b
            i ← i - 1
        else if T[i, j] = LEFT then
            prepend GAP to aligned_a
            prepend b[j] to aligned_b
            j ← j - 1
        end if
    end while

    return (aligned_a, aligned_b)
end function
```

**GAP** is a symbolic gap sentinel meaning "this position is a gap." The
formalization does not prescribe how it is represented in memory — Phase 1
maps it to `alphabet.gap_index` (an integer) at implementation time.

### Backtrace with affine gaps

For affine gap models with multiple DP matrices, the backtrace must track which
matrix the current cell belongs to. Use a state variable:

```
state ← M    — current matrix (one of M, X, Y)
```

The backtrace procedure switches on `(state, T[state, i, j])` pairs to determine
both the move direction and the matrix transition.

---

## A note on "backtrace" versus "traceback"

These conventions say **backtrace** for the array of predecessor choices and the procedure
that walks it. The sequence-alignment literature usually says *traceback*, and a worked
example drawn from that literature is left in its own vocabulary rather than corrected.

The generic term is deliberately the other one: in a plugin whose subject is Python code,
"traceback" already means an exception's stack trace, so an instruction to "check the
traceback" is ambiguous in exactly the situation where precision matters most.

## The encode/decode boundary — required of every formalization

Every formalization states, at the top of its Recurrence section, that the pseudocode
operates on pre-encoded integer inputs and that encoding and decoding happen at the
caller's boundary:

> **Boundary note.** This pseudocode operates on pre-encoded integer inputs. The caller
> encodes symbols to integers before invocation and decodes them back afterwards. No
> symbol operations occur within this pseudocode.

This is not part of the algorithm — it is the framing that anchors the pseudocode to a
computational model the later phases can transliterate rather than redesign. It applies in
every repository and to every family, which is why it lives here and not among the
family-specific notation below.

## Family-specific notation — worked examples

The conventions above are universal. What an array *holds* and which parameters exist are
the family's, and a formalization should follow whatever the repository's existing
formalizations already do. Two examples, deliberately dissimilar:

### Sequence alignment

Score-matrix access is written `S[a[i], b[j]]` — the score for the symbols at positions
`i` and `j`, looked up by their integer indices. Never `S["alpha", "beta"]` and never
`score(sym_a, sym_b)`: symbol-level access has no place inside the recurrence.

Gap penalties are named `g_o` (opening) and `g_e` (extension), both negative, and the
affine model is the general case with the linear model as its `g_o = 0` specialisation.

### Hidden Markov models

There is no score matrix and there are no gap penalties. The parameters are an
initial-state vector, a transition array and an emission array, and the notation must
make the emission's *arity* visible, because that is the assumption most often lost in
translation: an arc-emitting model's emission is indexed by source state, destination
state and symbol, `E[i, j, k]`, and cannot be hoisted out of the inner loop because it
depends on both endpoints. A state-emitting model's `B[i, k]` can be, and writing one
where the other is meant changes the recurrence rather than the notation.

Note also the geometry: a path over *N* observations visits *N+1* states, so state arrays
and observation arrays differ in length by one. Say so in Definitions rather than leaving
a reader to infer it from an index bound.

## Output specification

State explicitly what the algorithm returns: the DP array, the backtrace array where one
exists, the optimal value, and the recovered path or sequence in its pre-decode form.

## FORMALIZATION.md Template

Every formalization follows the structure defined in
[`formalization-template.md`](formalization-template.md). Copy the template
to the path the manifest's `[phases].formalization` template gives for the algorithm,
and fill in each section.

The template includes guidance on each section's content and which sections
are optional. The notation used within the template follows the conventions
defined in this document.

---

## Notation Quick Reference

| Concept | Notation |
|---------|----------|
| Assignment | `x ← value` |
| Equality test | `x = y` |
| Array access | `A[i]` |
| Matrix access | `M[i, j]` |
| Score lookup | `S[a[i], b[j]]` |
| Gap open | `g_o` |
| Gap extend | `g_e` |
| Infinity | `-∞`, `+∞` |
| Undefined | `NIL` |
| Gap sentinel | `GAP` |
| Loop (ascending) | `for i ← 0 to n - 1 do ... end for` |
| Loop (descending) | `for i ← n - 1 downto 0 do ... end for` |
| Max over alternatives | `max { ... }` with curly-brace grouping |
| Function | `function NAME(...) ... end function` |
| Record | `record Name ... end record` |
| Enum | `enum Name ... end enum` |
| Recurrence block | Boxed with `┌─┐ │ │ └─┘` border |
| Prepend to list | `prepend x to L` |
| Append to list | `append x to L` |
| List operations | `empty list`, `|L|` for length |
