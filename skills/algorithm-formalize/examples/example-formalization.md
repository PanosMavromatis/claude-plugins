> **This is one family's worked instance, not the shape of every formalization.**
> Needleman-Wunsch is sequence alignment, so this example has a score matrix, gap
> penalties and a two-dimensional matrix with anti-diagonals. A formalization for a
> different family will have none of those and is no less complete for it. Read the
> *structure* — which sections exist, how a recurrence is laid out, how a TC-XX case
> states its precision level — and take the vocabulary from your own repository.
>
> The section list here predates the current template: `formalization-template.md` is
> canonical, and adds `Derived from`, `Objective` and a `Parallel decomposition` section
> that this example does not yet carry. It also says *backtrace* where the alignment
> literature, and this example, say *traceback*.

# Simplified Linear-Gap Needleman-Wunsch

## Metadata

| Field | Value |
|-------|-------|
| Source | Needleman, S.B. & Wunsch, C.D. (1970). "A general method applicable to the search for similarities in the amino acid sequence of two proteins." *J. Mol. Biol.* 48(3):443–453 |
| Alignment type | global |
| Gap model | linear |
| Time complexity | O(m × n) |
| Space complexity | O(m × n) |
| Optimality | optimal |
| Algorithm-specific params | none |

## Adaptations from Source

1. **Linear gap penalty only.** The project convention normally requires affine
   generalization (`g_o + k × g_e` with three coupled matrices M, X, Y). This
   example uses a single linear penalty `g` with one matrix `D` for pedagogical
   clarity. The affine generalization is the standard approach for production
   formalizations; this simplified version is recoverable by setting `g_o = 0`
   and `g_e = g`.

2. **Integer-indexed sequences.** The 1970 paper operates on single amino acid
   characters. This formalization uses pre-encoded integer arrays, per the
   encode-at-the-boundary rule every formalization follows.

3. **Generic score matrix.** The paper classifies amino acid pairs by codon
   correspondence. This formalization uses an abstract 2D score matrix `S`
   indexed by integer symbol indices.

4. **Objective preserved as the paper states it.** The paper maximises alignment
   score, and so does this rendering. **Nothing is normalised** — had the source
   minimised a distance, this would record a minimisation, because converting between
   the two changes the recurrence structure, the base cases and the identity element,
   not just an operator.

5. **Explicit traceback matrix.** The paper describes traceback implicitly
   ("recording the origin of the number"). This formalization defines an explicit
   traceback matrix `T` with enumerated direction values and a separate traceback
   procedure.

## Definitions

- `D[i, j]` — optimal alignment score for the first `i` symbols of `a` and the
  first `j` symbols of `b` (real-valued matrix of size (m+1) × (n+1))
- `T[i, j]` — traceback direction at cell (i, j) (Direction-valued matrix of
  size (m+1) × (n+1))
- `S` — score matrix, 2D array of reals, size |Σ| × |Σ|
- `a` — integer array of length `m` (encoded sequence A, 1-indexed: a[1]..a[m])
- `b` — integer array of length `n` (encoded sequence B, 1-indexed: b[1]..b[n])
- `g` — gap penalty (real, typically negative)
- `m` — length of sequence `a`
- `n` — length of sequence `b`
- `GAP` — abstract gap sentinel

```
enum Direction
    NIL     — uninitialized
    DIAG    — match or mismatch (diagonal move)
    UP      — gap in sequence B (vertical move)
    LEFT    — gap in sequence A (horizontal move)
end enum
```

## Recurrence

**Boundary note.** This pseudocode operates on pre-encoded integer sequences.
The caller is responsible for encoding string symbols to integers via
`Alphabet.encode_pair()` before invocation and decoding the aligned integer
sequences back to strings via `Alphabet.decode()` after return. No string
operations occur within this pseudocode.

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   D[i, j] = max { D[i-1, j-1] + S[a[i], b[j]],         │
│                  { D[i-1, j]   + g,                      │
│                  { D[i, j-1]   + g               }       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Tie-breaking rule.** When multiple alternatives achieve the maximum, the
traceback direction is assigned by priority: DIAG > UP > LEFT. That is,
`T[i, j]` is set to DIAG first; it is overwritten by UP only if the UP
alternative is strictly greater; it is overwritten by LEFT only if the LEFT
alternative is strictly greater than the current best.

## Base Cases

```
D[0, 0] ← 0
T[0, 0] ← NIL
D[i, 0] ← i × g       for i ← 1 to m
T[i, 0] ← UP           for i ← 1 to m
D[0, j] ← j × g       for j ← 1 to n
T[0, j] ← LEFT         for j ← 1 to n
```

## Iteration Order

```
function ALIGN(a, b, S, g)
    Input:  a — integer array of length m (encoded sequence A)
            b — integer array of length n (encoded sequence B)
            S — score matrix, 2D array of reals, size |Σ| × |Σ|
            g — real (gap penalty, negative)
    Output: AlignmentResult containing score, aligned index sequences,
            and traceback matrix

    m ← |a|
    n ← |b|
    D ← new matrix of size (m + 1) × (n + 1), initialized to 0
    T ← new matrix of size (m + 1) × (n + 1), initialized to NIL

    // Base cases
    for i ← 1 to m do
        D[i, 0] ← i × g
        T[i, 0] ← UP
    end for
    for j ← 1 to n do
        D[0, j] ← j × g
        T[0, j] ← LEFT
    end for

    // Fill
    for i ← 1 to m do
        for j ← 1 to n do
            diag ← D[i - 1, j - 1] + S[a[i], b[j]]
            up   ← D[i - 1, j] + g
            left ← D[i, j - 1] + g

            best ← diag
            T[i, j] ← DIAG
            if up > best then
                best ← up
                T[i, j] ← UP
            end if
            if left > best then
                best ← left
                T[i, j] ← LEFT
            end if
            D[i, j] ← best
        end for
    end for

    score ← D[m, n]
    (aligned_a, aligned_b) ← TRACEBACK(T, a, b, m, n)

    return AlignmentResult(score, aligned_a, aligned_b, T)
end function
```

## Traceback

```
function TRACEBACK(T, a, b, m, n)
    Input:  T — traceback matrix of Direction values, size (m+1) × (n+1)
            a — integer array of length m (encoded sequence A)
            b — integer array of length n (encoded sequence B)
            m — length of sequence a
            n — length of sequence b
    Output: (aligned_a, aligned_b) — pair of integer arrays with
            GAP inserted at gap positions

    aligned_a ← empty list
    aligned_b ← empty list
    i ← m
    j ← n

    while i > 0 or j > 0 do
        if i > 0 and j > 0 and T[i, j] = DIAG then
            prepend a[i] to aligned_a
            prepend b[j] to aligned_b
            i ← i - 1
            j ← j - 1
        else if i > 0 and T[i, j] = UP then
            prepend a[i] to aligned_a
            prepend GAP to aligned_b
            i ← i - 1
        else
            prepend GAP to aligned_a
            prepend b[j] to aligned_b
            j ← j - 1
        end if
    end while

    return (aligned_a, aligned_b)
end function
```

## Test Cases

### TC-01: Identical sequences

    Input:  a = [0, 1, 2], b = [0, 1, 2]
            S = identity matrix (match = 2.0, mismatch = -1.0)
            g = -2.0
    Expect: score = 6.0
            aligned_a = [0, 1, 2]
            aligned_b = [0, 1, 2]
            no gaps in either sequence

### TC-02: Completely disjoint sequences

    Input:  a = [0, 1], b = [2, 3]
            S = identity matrix (match = 2.0, mismatch = -1.0)
            g = -2.0
    Expect: score = -2.0
            aligned_a = [0, 1]
            aligned_b = [2, 3]
            all positions are mismatches, no gaps
            (mismatch cost -1.0 per position is cheaper than gap cost -2.0)

### TC-03: One empty sequence

    Input:  a = [0, 1, 2], b = []
            S = identity matrix (match = 2.0, mismatch = -1.0)
            g = -2.0
    Expect: score = -6.0
            aligned_a = [0, 1, 2]
            aligned_b = [GAP, GAP, GAP]

### TC-04: Both empty

    Input:  a = [], b = []
            S = identity matrix (match = 2.0, mismatch = -1.0)
            g = -2.0
    Expect: score = 0.0
            aligned_a = []
            aligned_b = []

### TC-05: Single substitution with flanking matches

    Input:  a = [0, 1, 2], b = [0, 3, 2]
            S = identity matrix (match = 2.0, mismatch = -1.0)
            g = -2.0
    Expect: score = 3.0
            aligned_a = [0, 1, 2]
            aligned_b = [0, 3, 2]
            positions 1 and 3 are matches (+2.0 each), position 2 is
            mismatch (-1.0); total = 2.0 + (-1.0) + 2.0 = 3.0

### TC-06: Gap in the middle

    Input:  a = [0, 1, 2], b = [0, 2]
            S = identity matrix (match = 2.0, mismatch = -1.0)
            g = -2.0
    Expect: score = 2.0
            aligned_a = [0, 1, 2]
            aligned_b = [0, GAP, 2]
            two matches (+2.0 each) and one gap (-2.0); total = 2.0

### TC-07: Gap at start (asymmetric lengths)

    Input:  a = [0], b = [1, 0]
            S = identity matrix (match = 2.0, mismatch = -1.0)
            g = -2.0
    Expect: score = 0.0
            aligned_a = [GAP, 0]
            aligned_b = [1, 0]
            one gap (-2.0) and one match (+2.0); total = 0.0

### TC-08: Dominant gap penalty forces all mismatches

    Input:  a = [0, 1], b = [1, 0]
            S = identity matrix (match = 2.0, mismatch = -1.0)
            g = -5.0
    Expect: score = -2.0
            aligned_a = [0, 1]
            aligned_b = [1, 0]
            all mismatches, no gaps (gap cost -5.0 per position far
            exceeds mismatch cost -1.0)

## Notes

1. **Teaching example only.** This formalization is a simplified linear-gap
   variant intended as a pedagogical example for the `algorithm-formalize` skill.
   Production formalizations should follow the affine gap convention (three
   coupled matrices M, X, Y with parameters `g_o` and `g_e`). A repository's own
   formalization of the full algorithm, at whatever path its manifest gives, is the
   production version.

2. **Prepend vs. append-reverse.** The traceback uses `prepend` for notational
   clarity. Implementations typically use `append` followed by `reverse` to
   avoid O(n) cost per insertion. Both produce identical output.

3. **Traceback as a separate function.** The traceback is factored out of the
   main alignment procedure per project convention. In Phase 1, this may map to
   a separate Python function or an inline block within `align()`, depending on
   complexity. The corresponding Python example inlines it for brevity.

4. **Single matrix vs. affine.** A production Needleman-Wunsch with affine gap
   penalties requires three matrices (M, X, Y) and a coupled recurrence system.
   See Gotoh (1982) for the classic affine formulation. The linear
   simplification here uses a single matrix `D` and is recoverable from the
   affine model by setting `g_o = 0`, `g_e = g`.
