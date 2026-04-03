---
name: algorithm-prototype
description: "TRIGGER: when advancing an algorithm from Phase 0 to Phase 1 via /next-phase; when FORMALIZATION.md exists and has been approved and the user asks to implement, prototype, or write the Python backend for a specific algorithm (Needleman-Wunsch, Smith-Waterman, Hirschberg, etc.). NOT for new algorithms or 'add an algorithm' requests — those go to algorithm-formalize (Phase 0)."
---

# algorithm-prototype

Guide the mechanical translation of an approved formalization into a pure Python implementation (Phase 1).

## When to trigger

When the user runs `/next-phase` for an algorithm that has a committed, approved
`FORMALIZATION.md`; when Phase 0 is complete and they ask to implement or prototype the
Python backend for a specific algorithm.

Do **not** trigger on "new algorithm" or "add an algorithm" requests — those belong to
`algorithm-formalize` (Phase 0). If the user asks to implement an algorithm but
`FORMALIZATION.md` is missing, stop and tell them to run `/new-algorithm` first.

## What to do

### 0. Verify prerequisites and read the formalization

Before writing any code:

1. Confirm `src/tokalign/algorithms/<name>/FORMALIZATION.md` exists. If it does not, stop:
   "Phase 0 is required before Phase 1. Run `/tokalign-dev:new-algorithm` to produce the
   formalization first."
2. Read `FORMALIZATION.md` in full — pseudocode, test cases (TC-XX), and notes sections.
   The implementation is a translation of this document, not an independent design.

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

#### Mechanical translation from the formalization (mandatory)

Phase 1 is a **mechanical translation** of `FORMALIZATION.md`, not a creative
reimplementation. Follow these rules strictly:

- Every function in the pseudocode becomes one Python function (same name, adapted to
  `snake_case`)
- The recurrence block maps to the inner loop body
- The traceback procedure becomes a separate Python function
- Variable names carry over from the formalization (minor Python convention adaptations
  are fine)
- The iteration order in the pseudocode is the iteration order in Python
- Any deviation from the formalization requires an explicit comment in the code explaining
  why

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
`tests/conftest.py` (see `references/test-patterns.md` for the full fixture pattern
and worked examples).

**Implement the TC-XX test case specifications from `FORMALIZATION.md` directly** —
each test case identifier and name in the formalization becomes a named test function.
The formalization is the source of truth for what inputs to use and what properties to
assert (exact values, property-based, or relational, as specified per case).

#### TC-XX to pytest translation rules

1. **Naming**: Each `TC-XX: <Descriptive Name>` becomes
   `test_tcXX_<snake_case_name>(align_fn, ...)`. Do not invent test cases beyond what
   the formalization specifies.

2. **Integer-to-string mapping**: FORMALIZATION.md specifies integer arrays (e.g.,
   `a = [4, 5, 6]`) where indices 0-3 are reserved and user symbols start at 4.
   Tests must translate these to string sequences for the `align()` API:
   - Create an `Alphabet` with enough symbols to cover the highest index used
   - Map integer index `N` to `alphabet.symbols[N - 4]`
   - Map `GAP` in expected output to `alphabet.gap_symbol`

3. **Fixture grouping**: Group test cases that share identical scoring parameters
   (match, mismatch, gap_open, gap_extend) under shared fixtures. Cases with unique
   parameters build their `Alphabet` and `ScoringMatrix` inline. Always pass
   `gap_open` and `gap_extend` explicitly — do not rely on defaults.

4. **Assertion precision**: Match the formalization's precision level for each TC:
   - **Exact**: `assert result.score == pytest.approx(X)` and
     `assert result.aligned_a == [...]`
   - **Property-based**: assert exact score, then check structural properties
     (gap count, match count, alignment length)
   - **Relational**: call `align_fn` with swapped/varied inputs and compare results

If a test scenario seems necessary but is not in the formalization, do not silently add
it. Instead: alert the user, add the test case specification to `FORMALIZATION.md`
first, then implement it in the test file.

### 5. Run tests and confirm

Run `uv run pytest tests/algorithms/test_<name>.py -v` and confirm all tests pass.

## When edge cases are discovered

If an edge case surfaces during implementation that the formalization does not cover:

1. **Amend `FORMALIZATION.md`** — add the edge case treatment to the Notes section (or
   the relevant pseudocode section and the Test Cases section)
2. **Then** implement the fix in `_python.py` and add the corresponding test

Never silently handle edge cases only in code. The formalization must remain the
authoritative specification so that Cython and GPU translators in later phases inherit
the same treatments.

## What NOT to do

- Don't creatively reinterpret the formalization — if the pseudocode says it, the Python
  says it; deviations require explicit justification in comments
- Don't add test cases beyond the formalization's TC-XX specs without first amending
  `FORMALIZATION.md`
- Don't optimize the Python implementation — clarity over speed
- Don't use numpy inside the DP computation — save that for Phase 2
- Don't skip edge-case tests "for now"
- Don't create Cython (`_cython.pyx`) or Numba (`_numba.py`) files yet

## Gotchas

- The `align()` return type must include the traceback matrix if downstream
  visualization will need it
- Scoring matrix lookups must use the `ScoringMatrix.score(i, j)` method, not raw
  dicts — this matters for mechanical Cython translation later
- Gap penalties should be parameterized as affine (gap_open + gap_extend) from the
  start — retrofitting is painful
- Reserved matrix rows/columns (indices 0–2) and the gap row/column (index 3) should
  be zeros — actual gap penalties use `gap_open`/`gap_extend`, not matrix lookups
