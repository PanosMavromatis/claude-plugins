# Pseudocode Conventions — Dynamic Programming Algorithms

This document defines the notation standard for algorithm formalizations in the
`tokalign` project. It governs the content of `FORMALIZATION.md` files produced
by the `algorithm-formalize` skill.

These conventions are specific to **dynamic programming algorithms** — the primary
algorithm family in tokalign's initial scope. If an algorithm does not fit the DP
mold (e.g., divide-and-conquer, heuristic search, probabilistic methods), notify
the user immediately. The appropriate response is either:

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
   traceback, and output construction are expressed in procedural pseudocode. The
   recurrence itself is a formula embedded within this scaffolding.

5. **tokalign patterns are baked in.** The pseudocode assumes integer-indexed
   sequences, a 2D score matrix accessed by integer indices, and affine gap
   penalties. These are not implementation details — they are the computational
   model.

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
            and traceback matrix

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
    traceback : matrix
end record
```

Use `record` for structured types. Field access uses dot notation: `result.score`.

### Enumerations (traceback directions)

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
            record traceback[i, j] ← direction of the maximizing term
        end for
    end for
```

This is where the pseudocode transitions from mathematical to procedural. The
recurrence block defines *what* is computed; the iteration order defines *when*.

### Traceback

Traceback is expressed as a separate procedure, not inlined into the main
function. This matches the conceptual separation (forward pass computes scores,
backward pass recovers the alignment) and will map cleanly to separate functions
in implementation.

```
function TRACEBACK(T, a, b, i_start, j_start)
    Input:  T — traceback matrix of Direction values
            a — integer array (encoded sequence A)
            b — integer array (encoded sequence B)
            i_start — starting row index for traceback
            j_start — starting column index for traceback
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

### Traceback with affine gaps

For affine gap models with multiple DP matrices, the traceback must track which
matrix the current cell belongs to. Use a state variable:

```
state ← M    — current matrix (one of M, X, Y)
```

The traceback procedure switches on `(state, T[state, i, j])` pairs to determine
both the move direction and the matrix transition.

---

## tokalign-Specific Conventions

### The encode/decode boundary

Every `FORMALIZATION.md` must include a brief note at the top of the pseudocode
stating:

> **Boundary note.** This pseudocode operates on pre-encoded integer sequences.
> The caller is responsible for encoding string symbols to integers via
> `Alphabet.encode_pair()` before invocation and decoding the aligned integer
> sequences back to strings via `Alphabet.decode()` after return. No string
> operations occur within this pseudocode.

This is not part of the algorithm — it is a framing statement that anchors the
pseudocode in tokalign's architecture.

### Score matrix access

Always write `S[a[i], b[j]]` — the score for the symbols at positions i and j,
looked up by their integer indices in the score matrix. Never write
`S["alpha", "beta"]` or `score(sym_a, sym_b)`.

### Gap penalty parameters

Use `g_o` (gap open, negative value) and `g_e` (gap extend, negative value).
The affine gap cost for a gap of length k is: `g_o + k × g_e`.

If the source algorithm uses linear gap penalties, the formalization should
present the affine generalization and note in the Adaptations section:
"Source uses linear gap penalty d. Generalized to affine: g_o + k × g_e.
Linear is recoverable by setting g_o = 0, g_e = d."

### Output specification

The function's Output declaration must list:

- `score` — the optimal alignment score (real)
- `aligned_a`, `aligned_b` — integer arrays with GAP_INDEX at gap positions
- `traceback` — the traceback matrix (or matrices, for affine models)

The traceback is included in the output even if the caller doesn't always need it,
because downstream visualization depends on it.

---

## FORMALIZATION.md Template

Every formalization follows the structure defined in
[`formalization-template.md`](formalization-template.md). Copy the template
to `src/tokalign/algorithms/<n>/FORMALIZATION.md` and fill in each section.

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
