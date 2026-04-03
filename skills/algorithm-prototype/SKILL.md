---
name: algorithm-prototype
description: "TRIGGER: when implementing, prototyping, or creating a new alignment algorithm in pure Python (Phase 1); algorithm names like Needleman-Wunsch, Smith-Waterman, Hirschberg"
---

# algorithm-prototype

Guide the implementation of a new alignment algorithm in pure Python (Phase 1).

## When to trigger

When the user asks to implement, prototype, or create a new alignment algorithm; when
they mention algorithm names (Needleman-Wunsch, Smith-Waterman, Hirschberg, banded
alignment, etc.); when they say "new algorithm" or "add an algorithm" in the context of
this project.

## What to do

### 1. Create the algorithm directory

Create `src/tokalign/algorithms/<name>/` with:
- `__init__.py` (empty)
- `_python.py` (the Phase 1 implementation)

### 2. Implement `_python.py`

The `align()` function **must** use this exact signature:

```python
from typing import Sequence
from ..._types import Alphabet, ScoringMatrix, AlignmentResult

def align(
    seq_a: Sequence[str],
    seq_b: Sequence[str],
    alphabet: Alphabet,
    scoring_matrix: ScoringMatrix,
    # algorithm-specific params follow (e.g., local=False for Smith-Waterman)
) -> AlignmentResult:
```

#### The encode-at-the-boundary pattern (mandatory)

The first lines of `align()` must encode sequences to integer arrays:

```python
enc_a, enc_b = alphabet.encode_pair(seq_a, seq_b)
```

The last step before returning must decode integers back to strings:

```python
aligned_a = alphabet.decode(traced_a)
aligned_b = alphabet.decode(traced_b)
return AlignmentResult(
    score=best_score,
    aligned_a=aligned_a,
    aligned_b=aligned_b,
    alphabet=alphabet,
    traceback=traceback_matrix,  # include if the algorithm produces one
)
```

**ALL computation between encode and decode must use integer arrays.** Never index
into sequences with string symbols inside the DP loop. Always use integer indices
and `scoring_matrix.score(i, j)` (the integer version, not `score_symbols()`).

#### Gap penalties

Use affine gap penalties from the start — retrofitting is painful. Access them via
`scoring_matrix.gap_open` and `scoring_matrix.gap_extend`. Linear gap penalties are
the special case where `gap_open = 0`.

#### Style

- Use only Python builtins and standard library (no numpy in Phase 1 — the point is
  clarity and correctness)
- Prioritize readability over performance
- Include type hints and a NumPy-style docstring on `align()`

### 3. Register the algorithm

Add an entry in `src/tokalign/algorithms/_registry.py` mapping the algorithm name
to its module path.

### 4. Create the test file

Create `tests/algorithms/test_<name>.py` using the parametrized backend pattern from
`tests/conftest.py` (see `references/test-patterns.md` for the full fixture pattern).

Required test cases:
- Identical sequences
- Completely different sequences
- Empty sequences (one or both)
- Single-symbol sequences
- Sequences of very different lengths
- Gaps at start, end, and middle
- Edge cases specific to the algorithm (e.g., for Smith-Waterman: optimal local
  alignment is a substring; for Hirschberg: result matches NW on small inputs)

### 5. Run tests and confirm

Run `uv run pytest tests/algorithms/test_<name>.py -v` and confirm all tests pass.

## What NOT to do

- Don't optimize the Python implementation — clarity over speed
- Don't skip edge-case tests "for now"
- Don't create Cython (`_cython.pyx`) or Numba (`_numba.py`) files yet
- Don't use numpy inside the DP computation — save that for Phase 2

## Gotchas

- The `align()` return type must include the traceback matrix if downstream
  visualization will need it
- Scoring matrix lookups must use the `ScoringMatrix.score(i, j)` method, not raw
  dicts — this matters for mechanical Cython translation later
- Gap penalties should be parameterized as affine (gap_open + gap_extend) from the
  start — retrofitting is painful
- Reserved matrix rows/columns (indices 0–2) and the gap row/column (index 3) should
  be zeros — actual gap penalties use `gap_open`/`gap_extend`, not matrix lookups
