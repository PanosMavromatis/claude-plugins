# Parametrized testing pattern

Tests are parametrized across all available backends using `get_available_backends()`
from `tests/conftest.py`. A single test file automatically runs against Python, Cython,
and Numba backends as they become available.

## conftest.py fixture

```python
import importlib
import pytest

def get_available_backends(algorithm_name: str) -> list[tuple[str, callable]]:
    """Discover which backends are installed for a given algorithm."""
    backends = []
    mod = importlib.import_module(f"tokalign.algorithms.{algorithm_name}._python")
    backends.append(("python", mod.align))

    try:
        mod = importlib.import_module(f"tokalign.algorithms.{algorithm_name}._cython")
        backends.append(("cython", mod.align))
    except ImportError:
        pass

    try:
        mod = importlib.import_module(f"tokalign.algorithms.{algorithm_name}._numba")
        backends.append(("numba", mod.align))
    except ImportError:
        pass

    return backends
```

## Translating TC-XX specs to pytest

FORMALIZATION.md test cases use integer arrays (e.g., `a = [4, 5, 6]`) matching
the internal representation where indices 0-3 are reserved and user symbols start
at index 4. The `align()` function takes string sequences, so tests must map
integer specs back to string symbols:

- Create an `Alphabet` with enough symbols to cover the highest index used
- Integer index `4` maps to `alphabet.symbols[0]`, index `5` to `symbols[1]`, etc.
- The `GAP` sentinel in expected output maps to `alphabet.gap_symbol` (default `"."`)

For example, if the formalization says `a = [4, 5, 6]` and the alphabet has
`symbols=("A", "B", "C", ...)`, the test input is `["A", "B", "C"]`.

## Test file template

Each `TC-XX` in `FORMALIZATION.md` becomes a test function named
`test_tcXX_<snake_case_name>`. Test cases that share identical scoring parameters
can share fixtures; cases with unique parameters build their setup inline.

```python
import pytest
from tokalign._types import Alphabet, ScoringMatrix
from tests.conftest import get_available_backends

ALGORITHM = "<name>"  # e.g., "needleman_wunsch"

@pytest.fixture(params=get_available_backends(ALGORITHM), ids=lambda b: b[0])
def align_fn(request):
    """Yield each available backend's align function."""
    _name, fn = request.param
    return fn


# --- Shared fixtures for test cases with common parameters ---
# Group TC cases that share the same alphabet, match, mismatch, and gap penalties.
# Cases with unique parameters should build their setup inline instead.

@pytest.fixture
def alphabet_4():
    """Alphabet with 4 user symbols (covers integer indices 4-7)."""
    return Alphabet(symbols=("A", "B", "C", "D"))

@pytest.fixture
def identity_2_m1(alphabet_4):
    """Identity matrix: match=2.0, mismatch=-1.0, g_o=-5.0, g_e=-1.0."""
    return ScoringMatrix.identity(
        alphabet_4, match=2.0, mismatch=-1.0, gap_open=-5.0, gap_extend=-1.0,
    )


# --- Exact assertion pattern (TC score and alignment are unambiguous) ---

def test_tc01_identical_sequences(align_fn, alphabet_4, identity_2_m1):
    """TC-01: Identical sequences."""
    result = align_fn(["A", "B", "C"], ["A", "B", "C"], alphabet_4, identity_2_m1)
    assert result.score == pytest.approx(6.0)
    assert result.aligned_a == ["A", "B", "C"]
    assert result.aligned_b == ["A", "B", "C"]
    # No gaps in either sequence
    assert alphabet_4.gap_symbol not in result.aligned_a
    assert alphabet_4.gap_symbol not in result.aligned_b


# --- Exact score + property assertion (alignment details are properties) ---

def test_tc02_partially_overlapping(align_fn, alphabet_4, identity_2_m1):
    """TC-02: Partially overlapping sequences."""
    # a = [4, 5, 6, 7] -> ["A", "B", "C", "D"]
    # b = [4, 5, 7, 8] -> need index 8, so use a larger alphabet
    alphabet = Alphabet(symbols=("A", "B", "C", "D", "E"))
    matrix = ScoringMatrix.identity(
        alphabet, match=2.0, mismatch=-1.0, gap_open=-5.0, gap_extend=-1.0,
    )
    result = align_fn(["A", "B", "C", "D"], ["A", "B", "D", "E"], alphabet, matrix)
    assert result.score == pytest.approx(2.0)
    assert len(result.aligned_a) == 4
    assert len(result.aligned_b) == 4
    # No gaps (mismatch cheaper than opening a gap)
    assert alphabet.gap_symbol not in result.aligned_a
    assert alphabet.gap_symbol not in result.aligned_b


# --- Gap position assertion pattern ---

def test_tc04_empty_sequence_a(align_fn, alphabet_4, identity_2_m1):
    """TC-04: Empty sequence A."""
    result = align_fn([], ["A", "B", "C"], alphabet_4, identity_2_m1)
    assert result.score == pytest.approx(-8.0)  # g_o + 3 * g_e = -5.0 + -3.0
    assert result.aligned_a == [alphabet_4.gap_symbol] * 3
    assert result.aligned_b == ["A", "B", "C"]


# --- Inline setup pattern (unique parameters per test case) ---

def test_tc09_gap_at_start(align_fn):
    """TC-09: Gap required at the start (different gap penalties)."""
    # This TC uses g_o=-3.0, g_e=-1.0 — different from the shared fixture
    alphabet = Alphabet(symbols=("A", "B", "C", "D", "E", "F"))
    matrix = ScoringMatrix.identity(
        alphabet, match=2.0, mismatch=-1.0, gap_open=-3.0, gap_extend=-1.0,
    )
    # a = [6, 4, 5] -> ["C", "A", "B"],  b = [4, 5] -> ["A", "B"]
    result = align_fn(["C", "A", "B"], ["A", "B"], alphabet, matrix)
    assert result.score == pytest.approx(0.0)
    assert result.aligned_a == ["C", "A", "B"]
    assert result.aligned_b == [alphabet.gap_symbol, "A", "B"]


# --- Relational assertion pattern (no single correct output) ---

def test_tc16_symmetry(align_fn, alphabet_4, identity_2_m1):
    """TC-16: Swapping inputs yields the same score."""
    seq_a, seq_b = ["A", "B", "C"], ["C", "B", "A"]
    result_ab = align_fn(seq_a, seq_b, alphabet_4, identity_2_m1)
    result_ba = align_fn(seq_b, seq_a, alphabet_4, identity_2_m1)
    assert result_ab.score == pytest.approx(result_ba.score)


# --- Property-based assertion pattern (multiple valid alignments) ---

def test_tc12_multiple_gaps(align_fn):
    """TC-12: Multiple gaps in the alignment."""
    alphabet = Alphabet(symbols=("A", "B", "C", "D", "E"))
    matrix = ScoringMatrix.identity(
        alphabet, match=3.0, mismatch=-1.0, gap_open=-2.0, gap_extend=-0.5,
    )
    # a = [4, 6, 5] -> ["A", "C", "B"],  b = [4, 7, 5, 8] -> ["A", "D", "B", "E"]
    result = align_fn(["A", "C", "B"], ["A", "D", "B", "E"], alphabet, matrix)
    assert result.score == pytest.approx(4.0)
    assert len(result.aligned_a) >= 4
    # At least 2 match positions
    matches = sum(
        1 for a, b in zip(result.aligned_a, result.aligned_b)
        if a == b and a != alphabet.gap_symbol
    )
    assert matches >= 2


# --- Degenerate scoring pattern (non-standard matrix) ---

def test_tc15_all_zeros_matrix(align_fn):
    """TC-15: Degenerate scoring matrix (all zeros)."""
    alphabet = Alphabet(symbols=("A", "B", "C", "D"))
    matrix = ScoringMatrix.identity(
        alphabet, match=0.0, mismatch=0.0, gap_open=-1.0, gap_extend=-0.5,
    )
    result = align_fn(["A", "B"], ["C", "D"], alphabet, matrix)
    assert result.score == pytest.approx(0.0)
    # No gaps (gaps would reduce score below 0)
    assert alphabet.gap_symbol not in result.aligned_a
    assert alphabet.gap_symbol not in result.aligned_b
```

## Key conventions

- `ids=lambda b: b[0]` makes test output show "python", "cython", "numba" labels
- Each TC-XX from `FORMALIZATION.md` maps to one `test_tcXX_<name>` function
- Fixtures are shared only when test cases have identical scoring parameters;
  cases with unique parameters use inline setup
- When adding a new backend, **no test changes are needed** — the parametrization
  picks it up automatically
- GPU-specific tests go in a separate `test_<name>_numba_specific.py` file marked
  with `@pytest.mark.gpu`
- Use `pytest.approx()` for all score comparisons (float precision)
- Match the formalization's assertion precision level:
  - **Exact**: `assert result.score == pytest.approx(6.0)` and
    `assert result.aligned_a == [...]`
  - **Property-based**: assert score, then check structural properties (gap count,
    match count, alignment length) rather than exact sequences
  - **Relational**: run `align_fn` twice with swapped/varied inputs and compare
