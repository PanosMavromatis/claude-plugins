---
name: cython-translation
description: >
  TRIGGER: when the user says "cythonize", "translate to Cython", "make it fast",
  "compile", or "Phase 2" for an algorithm that has a working _python.py. Also
  trigger when the user asks to create a _cython.pyx file, mentions typed
  memoryviews, or asks about Cython performance for a tokalign algorithm.
  Do NOT trigger for GPU/Numba work (use gpu-parallelization instead).
---

# Cython Translation Skill

Guide the translation of a Phase 1 pure Python algorithm to Phase 2 Cython.

## Prerequisites — verify before writing any code

1. **`_python.py` exists** in the algorithm directory (e.g.,
   `src/tokalign/algorithms/needleman_wunsch/_python.py`). If it does not exist,
   stop and hand off to the `algorithm-prototype` skill instead, using the
   `Skill` tool with `skill: "dp-compile:algorithm-prototype"`. Do NOT use
   `Read` on the sibling `SKILL.md` — only the `Skill` tool activates the skill
   through the harness so it runs with its own references and examples.

2. **`_python.py` is not stale.** Compare modification times: if
   `FORMALIZATION.md` is newer than `_python.py`, the Python backend is stale and
   must be regenerated before Cython translation can proceed. Stop and hand off
   to the `algorithm-prototype` skill first via the `Skill` tool with
   `skill: "dp-compile:algorithm-prototype"` (not `Read`) — do not translate
   from a stale source.

3. **Check for stale artifact (regeneration case).** If `_cython.pyx` already
   exists, compare modification times: if `_python.py` is newer than
   `_cython.pyx`, the Cython backend is stale and must be regenerated. Tell the
   user: "`_python.py` has been updated since `_cython.pyx` was last generated.
   Regenerating the Cython backend." Then proceed with the translation as
   normal — read `_python.py`, rewrite `_cython.pyx` from scratch, and re-run
   all tests. Do **not** attempt to patch the existing `.pyx` — regenerate it to
   maintain the mechanical-translation guarantee.

4. **All Python tests pass.** Run:

   ```bash
   uv run pytest tests/algorithms/test_<algorithm>.py -k python
   ```

   Do not proceed if any test fails — the Cython version will inherit any bugs.

5. **Read `_python.py` in full** before writing a single line of Cython. The
   translation must be mechanical, not creative. Every line of Cython should
   trace back to a line in the Python.

6. **Read `src/tokalign/_types.py`** to understand `Alphabet`, `ScoringMatrix`,
   and `AlignmentResult` — specifically the integer index conventions and how
   `scoring_matrix._matrix` is laid out as a numpy array.

## Translation instructions

### File to create

Create `_cython.pyx` in the same algorithm directory alongside `_python.py`:

```
src/tokalign/algorithms/<algorithm>/
├── FORMALIZATION.md
├── _python.py        # already exists — read this first
└── _cython.pyx       # create this
```

### Split into wrapper + inner function

The Cython backend splits into two parts: a thin Python wrapper (handles
encode/decode) and a compiled inner function (pure integer/float computation).
The inner function must never import or touch the `Alphabet` class.

```python
# Python wrapper — stays in Python, handles encode/decode
def align(seq_a, seq_b, alphabet, scoring_matrix):
    enc_a, enc_b = alphabet.encode_pair(seq_a, seq_b)
    result = _align_impl(enc_a, enc_b, scoring_matrix._matrix,
                         scoring_matrix.gap_open, scoring_matrix.gap_extend)
    return AlignmentResult(
        score=result["score"],
        aligned_a=alphabet.decode(result["aligned_a"]),
        aligned_b=alphabet.decode(result["aligned_b"]),
        alphabet=alphabet,
    )
```

```cython
# Cython inner function — receives pre-encoded arrays, returns raw integers
cpdef dict _align_impl(int[:] seq_a, int[:] seq_b,
                       double[:, :] scores,
                       double gap_open, double gap_extend):
    ...
```

The `align()` function signature presented to the user must be **identical** to
the Python version. Tests are parametrized across backends — do not change the
interface.

### C type declarations

Declare C types for all variables used in inner loops:

```cython
cdef int m = seq_a.shape[0]
cdef int n = seq_b.shape[0]
cdef int i, j
cdef double s, best
cdef double NEG_INF = float("-inf")
```

### DP matrices as typed memoryviews

Replace Python lists with numpy arrays accessed via typed memoryviews:

```cython
import numpy as np

M_np = np.full((m + 1, n + 1), NEG_INF, dtype=np.float64)
cdef double[:, :] M = M_np
```

See `references/typed-memoryviews.md` for the full syntax reference and
`references/cython-for-dp.md` for DP-specific patterns.

### Scoring matrix lookup

The scoring matrix is the hottest path. It arrives as `double[:, :] scores`
— access it directly with integer indices:

```cython
s = scores[seq_a[i - 1], seq_b[j - 1]]
```

Never call `scoring_matrix.score()` inside the Cython inner function. The Python
wrapper already passed the raw `_matrix` array.

### GIL release

Release the GIL around the inner DP loop so the code is ready for
multi-threading in the future:

```cython
with nogil:
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            ...
```

Note: memoryview access is GIL-safe, but Python object creation is not. Move all
Python object creation (numpy allocations, list construction) outside the
`with nogil:` block.

### Disable bounds checking and wraparound

Add these decorators to the inner function to eliminate Python-level safety
checks in the hot path:

```cython
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef dict _align_impl(...):
    ...
```

Only add these after confirming the Python tests pass on the Cython build.

### Build configuration

Update `pyproject.toml` to include the new `.pyx` file in the Cython extension
list. Look for the existing `[tool.cython]` section or `setup.py` extension
declarations and add an entry following the same pattern as any existing
algorithms.

## Equivalence validation

After compilation, the translation must be verified in two ways:

### 1. Full test suite (automated)

The parametrized `conftest.py` fixture auto-discovers backends. Compiling
`_cython.pyx` makes it visible. Run:

```bash
uv run python setup.py build_ext --inplace
uv run pytest tests/algorithms/test_<algorithm>.py
```

If any test fails, fix the Cython — do not modify the tests.

### 2. Fuzzy equivalence script (critical for boundary errors)

Run the validate-equivalence script to catch off-by-one and floating-point
boundary errors that unit tests miss:

```bash
uv run python dp-compile/skills/cython-translation/scripts/validate-equivalence.py \
    --algorithm <algorithm> --n-pairs 1000
```

The script generates random sequence pairs (sampled from `alphabet.symbols`,
not random strings), runs both backends, and asserts identical scores and aligned
sequences.

## Annotation — find the slow lines

Compile with `-a` to generate annotation HTML:

```bash
uv run cython -a src/tokalign/algorithms/<algorithm>/_cython.pyx
```

Open the generated `.html` file. Yellow lines still touch the Python/C API — they
are slow. The inner DP loop must be white (pure C). If any line in the DP loop
is yellow, add missing type declarations.

## Gotchas

- **`cdef` vs `cpdef`**: `cdef` functions cannot be called from Python. Use
  `cpdef` for `_align_impl` so tests can call it directly.

- **Memoryview input type**: `int[:, :]` and `double[:, :]` require contiguous
  numpy arrays. Add the conversion at the wrapper boundary, not inside callers:

  ```python
  enc_a = np.ascontiguousarray(enc_a, dtype=np.int32)
  ```

- **GIL and Python objects**: `with nogil:` blocks cannot create Python objects
  (lists, dicts, strings). Pre-allocate all output arrays as numpy arrays before
  entering the block.

- **Integer type alignment**: `Alphabet.encode_pair()` returns numpy `int64` by
  default. The memoryview `int[:] ` expects `int32`. Cast at the boundary:

  ```python
  enc_a = enc_a.astype(np.int32)
  ```

- **Traceback matrix**: If the traceback uses an `IntEnum`, use its integer
  values (not the enum objects) in the Cython matrix. Define the direction
  constants as C integers at the top of the `.pyx` file.

- **`NEG_INF`**: `float("-inf")` works in Cython, but declare it as a `double`
  constant at module level for clarity and performance.

## Reference material

- `references/typed-memoryviews.md` — Cython typed memoryview syntax
- `references/cython-for-dp.md` — DP-specific Cython patterns
- `examples/example-cython-impl.pyx` — Annotated minimal example showing
  the wrapper + `_align_impl` pattern end-to-end
