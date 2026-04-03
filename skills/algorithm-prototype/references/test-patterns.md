# Parametrized testing pattern

Tests are parametrized across all available backends using `get_available_backends()`
from `tests/conftest.py`. This means a single test file automatically runs against
Python, Cython, and Numba backends as they become available.

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

## Test file template

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

@pytest.fixture
def simple_alphabet():
    return Alphabet(symbols=("A", "B", "C", "D"))

@pytest.fixture
def identity_matrix(simple_alphabet):
    return ScoringMatrix.identity(simple_alphabet, match=2.0, mismatch=-1.0)

# --- Required test cases ---

def test_identical_sequences(align_fn, simple_alphabet, identity_matrix):
    seq = ["A", "B", "C"]
    result = align_fn(seq, seq, simple_alphabet, identity_matrix)
    assert result.aligned_a == result.aligned_b
    assert result.identity == 1.0

def test_completely_different(align_fn, simple_alphabet, identity_matrix):
    result = align_fn(["A", "A"], ["B", "B"], simple_alphabet, identity_matrix)
    assert result.score < 0  # all mismatches/gaps

def test_empty_sequences(align_fn, simple_alphabet, identity_matrix):
    result = align_fn([], [], simple_alphabet, identity_matrix)
    assert result.score == 0.0
    assert result.aligned_a == []
    assert result.aligned_b == []

def test_one_empty(align_fn, simple_alphabet, identity_matrix):
    result = align_fn(["A", "B"], [], simple_alphabet, identity_matrix)
    # All gaps in one sequence
    assert len(result.aligned_a) == len(result.aligned_b)

def test_single_symbol(align_fn, simple_alphabet, identity_matrix):
    result = align_fn(["A"], ["A"], simple_alphabet, identity_matrix)
    assert result.aligned_a == ["A"]
    assert result.aligned_b == ["A"]

def test_different_lengths(align_fn, simple_alphabet, identity_matrix):
    result = align_fn(["A", "B", "C", "D"], ["B", "C"], simple_alphabet, identity_matrix)
    assert len(result.aligned_a) == len(result.aligned_b)

# Add algorithm-specific edge cases below
```

## Key conventions

- `ids=lambda b: b[0]` makes test output show "python", "cython", "numba" labels
- Fixtures provide shared setup (alphabet, scoring matrix) so tests stay DRY
- When adding a new backend, **no test changes are needed** — the parametrization
  picks it up automatically
- GPU-specific tests go in a separate `test_<name>_numba_specific.py` file marked
  with `@pytest.mark.gpu`
